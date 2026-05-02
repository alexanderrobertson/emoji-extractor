# Emoji Extractor

Extract and count emoji from text efficiently and accurately. Fully supports multi-part emoji (skin tones, zero-width joiners, flags).

## Installation

```bash
pip install emoji_extractor
```

Usage examples: [see this Jupyter notebook](https://github.com/alexanderrobertson/emoji-extractor/blob/master/notebooks/examples.ipynb)

## Quick Start

You can use the top-level convenience functions to extract emoji using the default (latest) Unicode version:

```python
from emoji_extractor import count_emoji, detect_emoji

# Returns a Counter object of emojis and their counts
counts = count_emoji("I love apples 🍎 and bananas 🍌🍌")
print(counts)
# Counter({'🍌': 2, '🍎': 1})

# Check if a string has emoji
has_emoji = detect_emoji("No emoji here") # False
```

## Advanced Usage (Version Selection)

By default, the package uses the latest available Unicode Emoji data. 
If you need to extract emoji precisely as they were defined in a specific historical Unicode version, instantiate the `Extractor` class:

```python
from emoji_extractor import Extractor

# Initialise an extractor for a specific version
ext_14 = Extractor(version='14.0')
ext_15 = Extractor(version='15.0')

# 🩷 Pink heart was introduced in 15.0
print(ext_14.detect_emoji("🩷")) # False
print(ext_15.detect_emoji("🩷")) # True
```

Available versions: `4.0`, `5.0`, `11.0`, `12.0`, `12.1`, `13.0`, `13.1`, `14.0`, `15.0`, `15.1`, `16.0`.

## Details & Features
- **Accurate Counting**: Uses dynamically generated regular expressions to properly capture multi-codepoint sequences, including ZWJ sequences like '💁🏽‍♂️' and flags.
- **Historical Accuracy**: Supports strict adherence to older Unicode specifications, avoiding false positives on newer emoji.
- **Always Up to Date**: Automatically checks for new Unicode releases via GitHub Actions and updates itself.

### How it works under the hood
The package relies on official Unicode data parsed from `emoji-test.txt`. Inside the `data/` folder for each version, it generates:
* `possible_emoji.json`: A set of all characters that could possibly be part of an emoji (used as a fast initial filter before checking the regex).
* `big_regex.txt`: A massive list of exact matching strings piped together in order of decreasing length. This guarantees multi-part emojis are matched before their individual components.
* `tme_regex.txt`: Regex definitions for Tone-Modifiable Emoji.

*(Note: Prior versions of this package used `.pkl` files, but we have migrated to standard formats like JSON/TXT for better security and cross-platform compatibility).*

Some emoji have a variation selector `0xFE0F`, but some platforms strip these and still render the emoji form. However, the regex used here will capture both (e.g. `0xFE0F` after each emoji codepoint vs no `0xFE0F`). See Unicode's Full Emoji List and search for '0xFE0F' to see which emoji this potentially affects.

## Other work

If you want to do stuff more complicated than simply detecting, extracting and counting emoji then you might find [this Python package useful](https://github.com/carpedm20/emoji/).

## Anything else

Feel free to email me about any of this stuff.
