# Emoji extractor/counter

# Installation

```pip install emoji_extractor```

Usage examples: [see this Jupyter notebook](https://github.com/alexanderrobertson/emoji-extractor/blob/master/notebooks/examples.ipynb)

# Info

It counts the emoji in a string, returning the emoji and their counts. That's it! It should properly detect and count all current multi-part emoji.

# Details

* Uses [v14.0 of the current Full Emoji List](https://unicode.org/emoji/charts-14.0/full-emoji-list.html).

* `possible_emoji.pkl` is a pickled set of possible emoji, used to check for their presence in a string with a few additional characters like the exciting [VARIATION-SELECTOR-16](https://emojipedia.org/variation-selector-16/) and the individual characters which make up flag sequences.

* `big_regex.pkl` is a pickled compiled regular expression. It's just 3628 regular expressions piped together in order of decreasing length. This is important to make sure that you can count multi-codepoint sequences like '💁🏽\u200d♂️' and so on.

# Other work

If you want to do stuff more complicated than simply detecting, extracting and counting emoji then you might find [this Python package useful](https://github.com/carpedm20/emoji/).

# To do

It may be possible to speed up the extraction/counting process by limited the regular expression used to only those which are possible, given the unique detected characters. I guess it would depend on how quickly the new smaller regex can be compiled. Storing them might be possible but the combinations are likely to be prohibitive.

# Anything else.

Feel free to email me about any of this stuff.
