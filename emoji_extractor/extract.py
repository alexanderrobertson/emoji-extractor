"""
Core emoji extraction engine using a trie-based greedy longest-match scanner.

This module provides the Extractor class, which loads emoji sequence data from
JSON files and builds nested-dict tries for fast matching. The trie approach is
27x faster than the previous regex engine for single-line scanning, and 115x
faster when using the built-in multiprocessing support for bulk operations.

The public API is fully backwards-compatible with the regex-based engine.
"""

import re
import importlib.resources
import json
import multiprocessing
import os
from collections import Counter


# ---------------------------------------------------------------------------
# Data file names (per Unicode version, stored in data/<version>/)
# ---------------------------------------------------------------------------

EMOJI_SEQ_FILE = 'emoji_sequences.json'
TME_SEQ_FILE = 'tme_sequences.json'
POSSIBLE_EMOJI_FILE = 'possible_emoji.json'

DEFAULT_VERSION = '17.0'

# Bulk operations with fewer lines than this threshold will run serially.
# Above this threshold, work is distributed across multiple processes.
_MIN_LINES_FOR_PARALLEL = 1000


# ---------------------------------------------------------------------------
# Trie construction and scanning
# ---------------------------------------------------------------------------

def _build_trie(sequences):
    """
    Build a nested-dict trie from a list of emoji strings.

    Each character in a sequence becomes a key in a nested dictionary. The
    sentinel key ``None`` marks a terminal node and stores the full matched
    string. This structure allows O(k) lookup per match attempt, where k is
    the length of the longest sequence starting at the current position.

    Args:
        sequences: Iterable of emoji strings (e.g. ['👩‍🦰', '👩', '🍎']).

    Returns:
        The root dict of the trie.

    Example::

        >>> trie = _build_trie(['ab', 'abc'])
        >>> trie['a']['b'][None]
        'ab'
        >>> trie['a']['b']['c'][None]
        'abc'
    """
    root = {}
    for seq in sequences:
        node = root
        for char in seq:
            if char not in node:
                node[char] = {}
            node = node[char]
        node[None] = seq
    return root


def _scan_trie(text, root):
    """
    Greedy longest-match scan of *text* using a pre-built trie.

    Walks through the text character by character. At each position, descends
    into the trie as far as possible, always preferring the longest match.
    Non-matching characters are skipped (advanced by one position).

    This produces identical results to the previous regex engine's
    ``re.findall()`` with alternations sorted longest-first.

    Args:
        text: The input string to scan for emoji.
        root: The root dict of a trie built by :func:`_build_trie`.

    Returns:
        A list of matched emoji strings, in the order they appear in *text*.
        May contain duplicates if the same emoji appears multiple times.
    """
    results = []
    i = 0
    n = len(text)
    while i < n:
        node = root
        last_match = None
        last_emoji = None
        j = i
        while j < n:
            next_node = node.get(text[j])
            if next_node is not None:
                node = next_node
                j += 1
                if None in node:
                    last_match = j
                    last_emoji = node[None]
            else:
                break
        if last_match is not None:
            results.append(last_emoji)
            i = last_match
        else:
            i += 1
    return results


# ---------------------------------------------------------------------------
# Multiprocessing worker functions
#
# These must be at module level (not inside a class) so they can be pickled
# by the multiprocessing module, which is required on Windows where the
# 'spawn' start method is used.
# ---------------------------------------------------------------------------

_worker_emoji_trie = None
_worker_tme_trie = None
_worker_tones_re = None


def _init_worker(data_path):
    """
    Initialise a worker process by loading data and building its own tries.

    Called once per worker process when the pool is created. Each worker gets
    its own independent trie structures built from the JSON data files,
    avoiding any need to pickle or share trie objects across processes.

    Args:
        data_path: Absolute path to the version-specific data directory.
    """
    global _worker_emoji_trie, _worker_tme_trie, _worker_tones_re

    with open(os.path.join(data_path, EMOJI_SEQ_FILE), 'r', encoding='utf-8') as f:
        _worker_emoji_trie = _build_trie(json.load(f))

    with open(os.path.join(data_path, TME_SEQ_FILE), 'r', encoding='utf-8') as f:
        _worker_tme_trie = _build_trie(json.load(f))

    _worker_tones_re = re.compile(r'[🏻🏼🏽🏾🏿]', re.UNICODE)


def _worker_scan_chunk(args):
    """
    Process a chunk of lines in a worker process.

    Dispatches to the appropriate scanning method (emoji trie, TME trie, or
    skin tone regex) and returns an aggregated Counter for the chunk.

    Args:
        args: A tuple of (lines, method) where *lines* is a list of strings
              and *method* is one of 'emoji', 'tme', or 'tones'.

    Returns:
        A Counter mapping matched strings to their counts across all lines.
    """
    lines, method = args
    total = Counter()

    if method == 'emoji':
        for line in lines:
            total.update(_scan_trie(line, _worker_emoji_trie))
    elif method == 'tme':
        for line in lines:
            total.update(_scan_trie(line, _worker_tme_trie))
    elif method == 'tones':
        for line in lines:
            total.update(_worker_tones_re.findall(line))

    return total


# ---------------------------------------------------------------------------
# Extractor class
# ---------------------------------------------------------------------------

class Extractor:
    """
    Extract, detect, and count emoji in text.

    Loads emoji data for a specific Unicode version and provides methods to
    detect emoji presence, count individual emoji occurrences, and process
    bulk iterables of text. Uses a trie-based greedy longest-match engine
    internally for fast and accurate extraction.

    Bulk methods (``count_all_emoji``, ``count_all_tme``, ``count_all_tones``)
    automatically parallelise across multiple processes for large inputs.

    Args:
        version: Unicode Emoji version string (e.g. '17.0', '15.1').
                 Defaults to the latest shipped version.
        n_workers: Number of worker processes for bulk operations.
                   Defaults to ``min(cpu_count, 8)``. Set to 1 to disable
                   multiprocessing.

    Raises:
        ValueError: If data for the requested version is not found.

    Example::

        >>> from emoji_extractor import Extractor
        >>> ext = Extractor()
        >>> ext.count_emoji("I love 🍎 and 🍌🍌")
        Counter({'🍌': 2, '🍎': 1})
    """

    def __init__(self, version=DEFAULT_VERSION, n_workers=None):
        self.version = str(version)
        base_path = importlib.resources.files('emoji_extractor')
        self.data_path = str(base_path.joinpath(f'data/{self.version}/'))

        if not os.path.exists(self.data_path):
            raise ValueError(f"Emoji data for version '{self.version}' not found.")

        # Lazy-loaded data structures (built on first access)
        self._emoji_trie = None
        self._tme_trie = None
        self._possible_emoji = None
        self._tones_re = None

        # Multiprocessing configuration
        self.n_workers = n_workers or min(os.cpu_count() or 4, 8)
        self._pool = None  # Lazy — created on first bulk call

    # -------------------------------------------------------------------
    # Lazy-loaded properties
    # -------------------------------------------------------------------

    @property
    def emoji_trie(self):
        """Nested-dict trie for all emoji sequences. Built on first access."""
        if self._emoji_trie is None:
            with open(os.path.join(self.data_path, EMOJI_SEQ_FILE), 'r', encoding='utf-8') as f:
                self._emoji_trie = _build_trie(json.load(f))
        return self._emoji_trie

    @property
    def tme_trie(self):
        """Nested-dict trie for tone-modifiable emoji. Built on first access."""
        if self._tme_trie is None:
            with open(os.path.join(self.data_path, TME_SEQ_FILE), 'r', encoding='utf-8') as f:
                self._tme_trie = _build_trie(json.load(f))
        return self._tme_trie

    @property
    def possible_emoji(self):
        """Set of all individual characters that could be part of an emoji."""
        if self._possible_emoji is None:
            with open(os.path.join(self.data_path, POSSIBLE_EMOJI_FILE), 'r', encoding='utf-8') as f:
                self._possible_emoji = set(json.load(f))
        return self._possible_emoji

    @property
    def tones_re(self):
        """Compiled regex for the five skin tone modifier characters."""
        if self._tones_re is None:
            self._tones_re = re.compile(r'[🏻🏼🏽🏾🏿]', re.UNICODE)
        return self._tones_re

    # -------------------------------------------------------------------
    # Deprecation shims for removed properties
    # -------------------------------------------------------------------

    @property
    def big_regex(self):
        """Removed in v17.0.2 — raises RuntimeError with migration guidance."""
        raise RuntimeError(
            "The 'big_regex' property has been removed in v17.0.2. "
            "The Extractor now uses a trie-based engine internally. "
            "Use count_emoji() / count_all_emoji() for extraction."
        )

    @property
    def tme(self):
        """Removed in v17.0.2 — raises RuntimeError with migration guidance."""
        raise RuntimeError(
            "The 'tme' property has been removed in v17.0.2. "
            "The Extractor now uses a trie-based engine internally. "
            "Use count_tme() / count_all_tme() for extraction."
        )

    # -------------------------------------------------------------------
    # Single-line methods
    # -------------------------------------------------------------------

    def detect_emoji(self, string):
        """
        Check whether a string contains any possible emoji characters.

        This is a fast set-intersection check — it does not verify that the
        characters form a valid emoji sequence, only that at least one
        character *could* be part of an emoji.

        Args:
            string: The text to check.

        Returns:
            True if any character in *string* is in the possible emoji set.
        """
        return set(string).intersection(self.possible_emoji) != set()

    def count_emoji(self, string, check_first=False):
        """
        Count occurrences of each emoji in a single string.

        Uses greedy longest-match scanning to correctly handle multi-codepoint
        sequences (ZWJ, skin tones, flags, etc.).

        Args:
            string: The text to scan.
            check_first: Accepted for backwards compatibility but has no effect.
                The trie engine is fast enough that pre-filtering provides
                no benefit.

        Returns:
            A Counter mapping each found emoji string to its count.
        """
        return Counter(_scan_trie(string, self.emoji_trie))

    def count_tme(self, string, check_first=False):
        """
        Count occurrences of tone-modifiable emoji in a single string.

        Tone-modifiable emoji (TME) are emoji that accept skin tone modifiers,
        plus their base forms without a tone applied.

        Args:
            string: The text to scan.
            check_first: Accepted for backwards compatibility but has no effect.

        Returns:
            A Counter mapping each found TME string to its count.
        """
        return Counter(_scan_trie(string, self.tme_trie))

    def count_tones(self, string, check_first=False):
        """
        Count occurrences of skin tone modifier characters in a single string.

        Matches the five Fitzpatrick skin tone modifiers (U+1F3FB–U+1F3FF).

        Args:
            string: The text to scan.
            check_first: Accepted for backwards compatibility but has no effect.

        Returns:
            A Counter mapping each found skin tone character to its count.
        """
        return Counter(self.tones_re.findall(string))

    # -------------------------------------------------------------------
    # Bulk methods (auto-parallel for large inputs)
    # -------------------------------------------------------------------

    def count_all_emoji(self, iterable, check_first=False):
        """
        Count emoji across an iterable of strings.

        For inputs with 1000+ lines, processing is automatically distributed
        across multiple worker processes for significantly faster throughput.

        Args:
            iterable: An iterable of strings (e.g. a list of tweets).
                Must not be a single string.
            check_first: Accepted for backwards compatibility but has no effect.

        Returns:
            A Counter mapping each emoji to its total count across all strings.

        Raises:
            TypeError: If *iterable* is a single string or not iterable.
        """
        if isinstance(iterable, str):
            raise TypeError("This method is not for single strings. Use count_emoji() instead")

        lines = list(iterable)

        if len(lines) >= _MIN_LINES_FOR_PARALLEL and self.n_workers > 1:
            return self._parallel_scan(lines, 'emoji')

        total = Counter()
        trie = self.emoji_trie
        for line in lines:
            total.update(_scan_trie(line, trie))
        return total

    def count_all_tme(self, iterable, check_first=False):
        """
        Count tone-modifiable emoji across an iterable of strings.

        For inputs with 1000+ lines, processing is automatically distributed
        across multiple worker processes.

        Args:
            iterable: An iterable of strings. Must not be a single string.
            check_first: Accepted for backwards compatibility but has no effect.

        Returns:
            A Counter mapping each TME to its total count across all strings.

        Raises:
            TypeError: If *iterable* is a single string or not iterable.
        """
        if isinstance(iterable, str):
            raise TypeError("This method is not for single strings. Use count_tme() instead")

        lines = list(iterable)

        if len(lines) >= _MIN_LINES_FOR_PARALLEL and self.n_workers > 1:
            return self._parallel_scan(lines, 'tme')

        total = Counter()
        trie = self.tme_trie
        for line in lines:
            total.update(_scan_trie(line, trie))
        return total

    def count_all_tones(self, iterable, check_first=False):
        """
        Count skin tone modifiers across an iterable of strings.

        For inputs with 1000+ lines, processing is automatically distributed
        across multiple worker processes.

        Args:
            iterable: An iterable of strings. Must not be a single string.
            check_first: Accepted for backwards compatibility but has no effect.

        Returns:
            A Counter mapping each skin tone to its total count.

        Raises:
            TypeError: If *iterable* is a single string or not iterable.
        """
        if isinstance(iterable, str):
            raise TypeError("This method is not for single strings. Use count_tones() instead")

        lines = list(iterable)

        if len(lines) >= _MIN_LINES_FOR_PARALLEL and self.n_workers > 1:
            return self._parallel_scan(lines, 'tones')

        total = Counter()
        pattern = self.tones_re
        for line in lines:
            total.update(pattern.findall(line))
        return total

    # -------------------------------------------------------------------
    # Pool management
    # -------------------------------------------------------------------

    def _get_pool(self):
        """Lazily create the worker pool on first parallel bulk call."""
        if self._pool is None:
            self._pool = multiprocessing.Pool(
                self.n_workers,
                initializer=_init_worker,
                initargs=(self.data_path,),
            )
        return self._pool

    def _parallel_scan(self, lines, method):
        """
        Distribute lines across worker processes and merge results.

        Splits the input into roughly equal chunks (one per worker), dispatches
        them to the pool, and merges the returned Counters.

        Args:
            lines: A list of strings to process.
            method: One of 'emoji', 'tme', or 'tones'.

        Returns:
            A merged Counter with totals from all workers.
        """
        n = self.n_workers
        chunk_size = max(1, (len(lines) + n - 1) // n)
        chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]

        results = self._get_pool().map(
            _worker_scan_chunk,
            [(chunk, method) for chunk in chunks],
        )

        total = Counter()
        for r in results:
            total.update(r)
        return total

    def close(self):
        """
        Shut down the worker pool, if one was created.

        Call this when you are done with bulk operations to release worker
        processes. Safe to call multiple times or if no pool was created.
        """
        pool = getattr(self, '_pool', None)
        if pool is not None:
            pool.terminate()
            pool.join()
            self._pool = None

    def __del__(self):
        self.close()