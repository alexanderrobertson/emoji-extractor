import re
import pickle
import pkg_resources
from collections import Counter
from collections.abc import Iterable

data_path = pkg_resources.resource_filename('emoji_extractor', 'data/')

regex_file = 'big_regex.pkl'
emoji_file = 'possible_emoji.pkl'
tme_regex_file = 'tme_regex.pkl'



class Extractor:
    """
    Extract emoji from strings.
    Return a count of the emoji found.
    """
    def __init__(self, regex=data_path+regex_file, emoji=data_path+emoji_file, tme=data_path+tme_regex_file):
        with open(regex, 'rb') as f:
            self.big_regex = pickle.load(f)

        with open(emoji, 'rb') as f:
            self.possible_emoji = pickle.load(f)

        with open(tme, 'rb') as f:
            self.tme = pickle.load(f)

        self.tones_re = re.compile(r'[🏻🏼🏽🏾🏿]', re.UNICODE)

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

    def count_tme(self, string, check_first=True):
        if check_first:
            if self.detect_emoji(string):
                return Counter(self.tme.findall(string))
            else:
                return Counter()
        else:
            return Counter(self.tme.findall(string))

    def count_tones(self, string, check_first=True):
        if check_first:
            if self.detect_emoji(string):
                return Counter(self.tones_re.findall(string))
            else:
                return Counter()

    def count_all_tones(self, iterable, check_first=True):
        running_total = Counter()

        if type(iterable) == str:
            raise TypeError("This method is not for single strings. Use count_emoji() instead")

        try:
            for string in iterable:
                running_total.update(self.count_tones(string, check_first=check_first))

            return running_total
        except:
            raise TypeError('This method requires an iterable of strings.')            

    def count_all_emoji(self, iterable, check_first=True):
        running_total = Counter()

        if type(iterable) == str:
            raise TypeError("This method is not for single strings. Use count_emoji() instead")

        try:
            for string in iterable:
                running_total.update(self.count_emoji(string, check_first=check_first))

            return running_total
        except:
            raise TypeError('This method requires an iterable of strings.')

    def count_all_tme(self, iterable, check_first=True):
        running_total = Counter()

        if type(iterable) == str:
            raise TypeError("This method is not for single strings. Use count_tme() instead")

        try:
            for string in iterable:
                running_total.update(self.count_tme(string, check_first=check_first))

            return running_total
        except:
            raise TypeError('This method requires an iterable of strings.')