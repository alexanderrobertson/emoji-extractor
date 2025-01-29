# Emoji extractor/counter

# Installation

```pip install emoji_extractor```
```conda install emoji-extractor -c conda-forge```

Usage examples: [see this Jupyter notebook](https://github.com/alexanderrobertson/emoji-extractor/blob/master/notebooks/examples.ipynb)

# Info

It counts the emoji in a string, returning the emoji and their counts. That's it! It should properly detect and count all current multi-part emoji.

There is an update script in `update_regex` which can be used to update to the latest Unicode version, or if you want to detect only emoji for a specific Unicode version.

# Details

* Uses [v16.0 of the current Full Emoji List](https://unicode.org/emoji/charts-16.0/full-emoji-list.html).

* `possible_emoji.pkl` is a pickled set of possible emoji, used to check for their presence in a string with a few additional characters like the exciting [VARIATION-SELECTOR-16](https://emojipedia.org/variation-selector-16/) and the individual characters which make up flag sequences.

* `big_regex.pkl` is a pickled compiled regular expression. It's just lots of regular expressions piped together in order of decreasing length. This is important to make sure that you can count multi-codepoint sequences like '💁🏽\u200d♂️' and so on.

* Some emoji have a variation selector 0xFE0F, but some platforms strip these and still render the emoji form. However, the regex used here will capture both '👁️\u200d🗨️' (0xFE0F after each emoji codepoint) and '👁\u200d🗨' (no 0xFE0F) and even situations where some component codepoints can and do have variant selectors but others can but don't. See Unicode's Full Emoji List and search for '0xFE0F' to see which emoji this potentially affects.

# Other work

If you want to do stuff more complicated than simply detecting, extracting and counting emoji then you might find [this Python package useful](https://github.com/carpedm20/emoji/).

# To do

It may be possible to speed up the extraction/counting process by limited the regular expression used to only those which are possible, given the unique detected characters. I guess it would depend on how quickly the new smaller regex can be compiled. Storing them might be possible but the combinations are likely to be prohibitive.

I probably need to update this package to automatically check Unicode's public emoji files for updates so that I don't need to do it manually every time...

# Anything else

Feel free to email me about any of this stuff.
