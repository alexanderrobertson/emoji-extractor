import re
import pkg_resources
import json
import os
from collections import Counter
from collections.abc import Iterable

regex_file = 'big_regex.txt'
emoji_file = 'possible_emoji.json'
tme_regex_file = 'tme_regex.txt'


class Extractor:
    """
    Extract emoji from strings.
    Return a count of the emoji found.
    """
    def __init__(self, version='latest'):
        self.version = str(version)
        self.data_path = pkg_resources.resource_filename('emoji_extractor', f'data/{self.version}/')
        
        if not os.path.exists(self.data_path):
            raise ValueError(f"Emoji data for version '{self.version}' not found.")
        
        self._big_regex = None
        self._possible_emoji = None
        self._tme = None
        self._tones_re = None

    @property
    def big_regex(self):
        if self._big_regex is None:
            with open(os.path.join(self.data_path, regex_file), 'r', encoding='utf-8') as f:
                self._big_regex = re.compile(f.read(), re.UNICODE)
        return self._big_regex

    @property
    def possible_emoji(self):
        if self._possible_emoji is None:
            with open(os.path.join(self.data_path, emoji_file), 'r', encoding='utf-8') as f:
                self._possible_emoji = set(json.load(f))
        return self._possible_emoji

    @property
    def tme(self):
        if self._tme is None:
            with open(os.path.join(self.data_path, tme_regex_file), 'r', encoding='utf-8') as f:
                self._tme = re.compile(f.read(), re.UNICODE)
        return self._tme

    @property
    def tones_re(self):
        if self._tones_re is None:
            self._tones_re = re.compile(r'[🏻🏼🏽🏾🏿]', re.UNICODE)
        return self._tones_re

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