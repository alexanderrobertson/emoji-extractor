from .extract import Extractor

# Global instance for convenience functions. 
# This default extractor will only ever use the default Unicode version.
# For specific versions, instantiate the Extractor class directly.
_default_extractor = Extractor()

def detect_emoji(string):
    """
    Detect if a string contains any emoji.
    Note: Operates on the default Unicode version only.
    """
    return _default_extractor.detect_emoji(string)

def count_emoji(string, check_first=False):
    """
    Count the occurrences of each emoji in a string.
    Note: Operates on the default Unicode version only.
    """
    return _default_extractor.count_emoji(string, check_first=check_first)

def count_tme(string, check_first=False):
    """
    Count the occurrences of tone-modifiable emoji.
    Note: Operates on the default Unicode version only.
    """
    return _default_extractor.count_tme(string, check_first=check_first)

def count_tones(string, check_first=False):
    """
    Count the occurrences of skin tones.
    Note: Operates on the default Unicode version only.
    """
    return _default_extractor.count_tones(string, check_first=check_first)

def count_all_tones(iterable, check_first=False):
    """
    Count skin tones across an iterable of strings.
    Note: Operates on the default Unicode version only.
    """
    return _default_extractor.count_all_tones(iterable, check_first=check_first)

def count_all_emoji(iterable, check_first=False):
    """
    Count emoji across an iterable of strings.
    Note: Operates on the default Unicode version only.
    """
    return _default_extractor.count_all_emoji(iterable, check_first=check_first)

def count_all_tme(iterable, check_first=False):
    """
    Count tone-modifiable emoji across an iterable of strings.
    Note: Operates on the default Unicode version only.
    """
    return _default_extractor.count_all_tme(iterable, check_first=check_first)
