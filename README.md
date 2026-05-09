# Emoji Extractor

Extract, detect, and count emoji from text — fast and accurate. Fully supports multi-codepoint sequences (skin tones, ZWJ sequences, flags).

Uses a **trie-based greedy longest-match engine** (pure Python, zero dependencies) that is **27× faster** than regex for single strings and **115× faster** when processing large datasets with automatic multiprocessing.

## Installation

```bash
pip install emoji_extractor
```

## Quick Start

Use the top-level convenience functions for simple tasks:

```python
from emoji_extractor import count_emoji, detect_emoji

# Check if a string contains emoji
detect_emoji("Hello 👋")   # True
detect_emoji("No emoji")   # False

# Count emoji in a single string — returns a Counter
counts = count_emoji("I love 🍎 and 🍌🍌")
print(counts)
# Counter({'🍌': 2, '🍎': 1})
```

## Single Strings vs Bulk Processing

The package provides two tiers of counting methods:

### `count_emoji(string)` — Single string

Scans one string and returns a `Counter`. Fast enough for real-time use (~9µs per line).

```python
from emoji_extractor import Extractor

ext = Extractor()
ext.count_emoji("Great job 🎉🎉🎉")
# Counter({'🎉': 3})
```

### `count_all_emoji(iterable)` — Bulk processing

Processes a list (or any iterable) of strings. For inputs with **1,000+ lines**, work is automatically distributed across multiple CPU cores for significantly faster throughput.

```python
tweets = ["Love this 🍎", "So funny 😂😂", "Hello world", ...]

# Automatically parallelised for large inputs
totals = ext.count_all_emoji(tweets)
print(totals.most_common(5))
# [('😂', 2813), ('❤', 1150), ('😍', 974), ...]
```

| Method | Input | Parallelised? |
|---|---|---|
| `count_emoji(string)` | Single string | No (already ~9µs) |
| `count_all_emoji(iterable)` | List of strings | Yes, for ≥1000 lines |
| `count_tme(string)` | Single string | No |
| `count_all_tme(iterable)` | List of strings | Yes, for ≥1000 lines |
| `count_tones(string)` | Single string | No |
| `count_all_tones(iterable)` | List of strings | Yes, for ≥1000 lines |

## Advanced Usage

### Version Selection

By default, the package uses the latest Unicode Emoji data (currently 17.0).
To extract emoji as defined in a specific historical version:

```python
from emoji_extractor import Extractor

ext_14 = Extractor(version='14.0')
ext_15 = Extractor(version='15.0')

# 🩷 Pink heart was introduced in 15.0
ext_14.detect_emoji("🩷")  # False
ext_15.detect_emoji("🩷")  # True
```

Available versions: `4.0`, `5.0`, `11.0`, `12.0`, `12.1`, `13.0`, `14.0`, `15.0`, `15.1`, `16.0`, `17.0`.

### Tone-Modifiable Emoji

Count emoji that support skin tone modifiers, plus their unmodified base forms:

```python
ext = Extractor()
ext.count_tme("High five ✋🏽")
# Counter({'✋🏽': 1})

ext.count_tones("Waves 👋🏻👋🏿")
# Counter({'🏻': 1, '🏿': 1})
```

### Controlling Parallelism

```python
# Use fewer workers (default: min(cpu_count, 8))
ext = Extractor(n_workers=4)

# Disable multiprocessing entirely
ext = Extractor(n_workers=1)

# Clean up worker processes when done
ext.close()
```

## Details & Features

- **Accurate Counting**: Uses a greedy longest-match trie to correctly handle multi-codepoint emoji, including ZWJ sequences like `👩‍🦰` and flag sequences like `🇬🇧`.
- **Fast**: 27× faster than regex for single strings. 115× faster with parallelism for bulk data.
- **Zero Dependencies**: Pure Python — no external packages required.
- **Historical Accuracy**: Supports strict adherence to older Unicode specifications, avoiding false positives on newer emoji.
- **Always Up to Date**: Automatically checks for new Unicode releases via GitHub Actions and updates itself.

### How It Works Under the Hood

The package relies on official Unicode data parsed from `emoji-test.txt`. For each supported version, the `data/` folder contains:

* **`emoji_sequences.json`**: All emoji strings, sorted longest-first. Used to build a nested-dict trie for greedy matching.
* **`tme_sequences.json`**: Tone-modifiable emoji sequences.
* **`possible_emoji.json`**: A set of all characters that could be part of an emoji (used by `detect_emoji()` for fast presence checking).

The trie scanner walks through text character by character, always matching the longest possible emoji sequence at each position. This naturally handles cases where a shorter emoji is a prefix of a longer one (e.g., `👩` vs `👩‍🦰`).

> **Note**: Some emoji include a variation selector (U+FE0F), but some platforms strip it while still rendering the emoji. The trie captures both forms.

## Changelog

### 17.0.2
- **Engine**: Regex replaced with pure-Python trie (27× faster single, 115× bulk with multiprocessing)
- **Data**: `big_regex.txt` / `tme_regex.txt` → `emoji_sequences.json` / `tme_sequences.json`
- `check_first` parameter is now a no-op (accepted for compatibility)
- `count_all_*` methods auto-parallelise for large inputs
- Added `n_workers` parameter and `close()` method to `Extractor`
- Removed `Extractor.big_regex` and `Extractor.tme` (raise helpful error if accessed)

## Other Work

If you want to do more than detecting, extracting, and counting emoji, [this Python package](https://github.com/carpedm20/emoji/) may be useful.

## Contact

Feel free to email me about any of this stuff.
