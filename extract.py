import re
import pickle
from collections import Counter

regex_file = 'big_regex.pkl'
emoji_file = 'possible_emoji.pkl'

class Extractor:
    """
    Extract emoji from strings.
    Return a count of the emoji found.
    """
    def __init__(self, regex=regex_file, emoji=emoji_file):
        with open(regex, 'rb') as f:
            self.big_regex = pickle.load(f)

        with open(emoji, 'rb') as f:
            self.possible_emoji = pickle.load(f)

    def detect_emoji(self, string):
        return set(string).intersection(self.possible_emoji) != set()

    def count_emoji(self, string, check_first=True):
        if check_first:
            if self.detect_emoji(string):
                return Counter(self.big_regex.findall(string))
            else:
                return Counter()
        else:
            return Counter(self.big_regex.findall(string))

    def count_all_emoji(self, iterable, check_first=True):
        running_total = Counter()

        for string in iterable:
            running_total.update(self.count_emoji(string, check_first=check_first))

        return running_total