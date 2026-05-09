import unittest
import json
import os
from unittest.mock import patch

from collections import Counter
from emoji_extractor import Extractor, detect_emoji, count_emoji

class TestExtractor(unittest.TestCase):

    def test_extractor_init_default(self):
        extractor = Extractor()
        self.assertEqual(extractor.version, '17.0')

    def test_extractor_invalid_version(self):
        with self.assertRaises(ValueError) as context:
            Extractor(version='99.9')
        self.assertIn("Emoji data for version '99.9' not found", str(context.exception))

    def test_lazy_loading(self):
        extractor = Extractor()
        # At this point, no files should have been read.
        self.assertIsNone(extractor._emoji_trie)
        self.assertIsNone(extractor._possible_emoji)
        self.assertIsNone(extractor._tme_trie)
        
        # Trigger lazy load
        trie = extractor.emoji_trie
        self.assertIsNotNone(trie)
        self.assertIsInstance(trie, dict)
        self.assertIsNotNone(extractor._emoji_trie)

    def test_detect_emoji_instance(self):
        extractor = Extractor()
        self.assertTrue(extractor.detect_emoji("Hello 👋"))
        self.assertFalse(extractor.detect_emoji("Hello"))

    def test_count_emoji_instance(self):
        extractor = Extractor()
        counts = extractor.count_emoji("Apple 🍎 and Banana 🍌🍌")
        self.assertEqual(counts['🍎'], 1)
        self.assertEqual(counts['🍌'], 2)

    def test_convenience_functions(self):
        self.assertTrue(detect_emoji("Hello 👋"))
        self.assertFalse(detect_emoji("Hello"))
        counts = count_emoji("Apple 🍎 and Banana 🍌🍌")
        self.assertEqual(counts['🍎'], 1)
        self.assertEqual(counts['🍌'], 2)

    def test_count_tme_no_empty_string(self):
        extractor = Extractor()
        counts = extractor.count_tme("Siga todos que derem fav nesse tweet 💁🏻")
        self.assertEqual(counts['💁🏻'], 1)
        self.assertNotIn('', counts)

    @patch('emoji_extractor.extract.importlib.resources.files')
    def test_version_isolation(self, mock_files):
        import tempfile
        import pathlib
        with tempfile.TemporaryDirectory() as tmp_path:
            version_dir = os.path.join(tmp_path, "data", "1.0")
            os.makedirs(version_dir)
            
            with open(os.path.join(version_dir, "possible_emoji.json"), "w", encoding="utf-8") as f:
                json.dump(["🍎"], f, ensure_ascii=False)
            with open(os.path.join(version_dir, "emoji_sequences.json"), "w", encoding="utf-8") as f:
                json.dump(["🍎"], f, ensure_ascii=False)
            with open(os.path.join(version_dir, "tme_sequences.json"), "w", encoding="utf-8") as f:
                json.dump(["🍎"], f, ensure_ascii=False)
                
            mock_files.return_value = pathlib.Path(tmp_path)
            
            extractor = Extractor(version='1.0')
            self.assertEqual(extractor.version, '1.0')
            self.assertTrue(extractor.detect_emoji("Testing 🍎"))
            self.assertFalse(extractor.detect_emoji("Testing 1️⃣"))

    def test_all_downloaded_versions(self):
        # We ensure that every version we've downloaded can be instantiated
        # and has a non-empty trie and possible_emoji set.
        for version in ['4.0', '5.0', '11.0', '12.0', '12.1', '13.0', '14.0', '15.0', '15.1', '16.0', '17.0']:
            extractor = Extractor(version=version)
            self.assertEqual(extractor.version, version)
            self.assertIsInstance(extractor.emoji_trie, dict)
            self.assertTrue(len(extractor.emoji_trie) > 0)
            self.assertTrue(len(extractor.possible_emoji) > 0)

    def test_version_boundaries(self):
        # Check that emojis are only found in versions where they exist
        # 12.0: 🥱 Yawning face
        # 13.0: 🥲 Smiling face with tear
        # 14.0: 🫠 Melting face
        # 15.0: 🩷 Pink heart
        # 15.1: 🍋‍🟩 Lime (sequence)
        
        ext_11 = Extractor('11.0')
        ext_12 = Extractor('12.0')
        ext_13 = Extractor('13.0')
        ext_14 = Extractor('14.0')
        ext_15 = Extractor('15.0')
        ext_15_1 = Extractor('15.1')

        # 🥱 Yawning face (12.0)
        self.assertFalse(ext_11.detect_emoji("🥱"))
        self.assertTrue(ext_12.detect_emoji("🥱"))

        # 🥲 Smiling face with tear (13.0)
        self.assertFalse(ext_12.detect_emoji("🥲"))
        self.assertTrue(ext_13.detect_emoji("🥲"))

        # 🫠 Melting face (14.0)
        self.assertFalse(ext_13.detect_emoji("🫠"))
        self.assertTrue(ext_14.detect_emoji("🫠"))

        # 🩷 Pink heart (15.0)
        self.assertFalse(ext_14.detect_emoji("🩷"))
        self.assertTrue(ext_15.detect_emoji("🩷"))

        # 🍋‍🟩 Lime (15.1)
        # Note: Lime is a sequence of Lemon + ZWJ + Green Square
        # In 15.0, it will be counted as two separate emojis (Lemon, Green Square).
        # In 15.1, it will be counted as one single emoji (Lime).
        self.assertNotIn("🍋‍🟩", ext_15.count_emoji("🍋‍🟩"))
        self.assertIn("🍋‍🟩", ext_15_1.count_emoji("🍋‍🟩"))


class TestTrieEngine(unittest.TestCase):
    """Tests specific to the trie-based engine internals and new behaviour."""

    def setUp(self):
        self.ext = Extractor()

    def test_trie_greedy_longest_match(self):
        # 👩‍🦰 (woman with red hair) should be matched as one emoji,
        # not as 👩 + ZWJ + 🦰 separately.
        counts = self.ext.count_emoji("👩\u200d🦰")
        self.assertEqual(len(counts), 1, "ZWJ sequence should match as single emoji")

    def test_trie_overlapping_sequences(self):
        # Flag sequences: 🇬🇧 is G + B regional indicators.
        # Should be one match, not two separate regional indicator symbols.
        counts = self.ext.count_emoji("🇬🇧")
        self.assertEqual(sum(counts.values()), 1)

    def test_check_first_is_noop(self):
        text = "Hello 🍎 world 🍌🍌"
        result_true = self.ext.count_emoji(text, check_first=True)
        result_false = self.ext.count_emoji(text, check_first=False)
        self.assertEqual(result_true, result_false)

    def test_empty_string(self):
        self.assertEqual(self.ext.count_emoji(""), Counter())
        self.assertEqual(self.ext.count_tme(""), Counter())
        self.assertEqual(self.ext.count_tones(""), Counter())

    def test_no_emoji_text(self):
        self.assertEqual(self.ext.count_emoji("Hello world, no emoji here!"), Counter())

    def test_consecutive_emoji(self):
        counts = self.ext.count_emoji("🍎🍌🍎")
        self.assertEqual(counts['🍎'], 2)
        self.assertEqual(counts['🍌'], 1)

    def test_skin_tone_matching(self):
        # 👋🏽 should be matched as a single toned emoji, not 👋 + tone
        counts = self.ext.count_emoji("👋🏽")
        self.assertEqual(sum(counts.values()), 1)
        # The key should be the full toned sequence
        self.assertIn("👋🏽", counts)

    def test_deprecation_shim_big_regex(self):
        with self.assertRaises(RuntimeError) as ctx:
            _ = self.ext.big_regex
        self.assertIn("removed", str(ctx.exception).lower())
        self.assertIn("count_emoji", str(ctx.exception))

    def test_deprecation_shim_tme(self):
        with self.assertRaises(RuntimeError) as ctx:
            _ = self.ext.tme
        self.assertIn("removed", str(ctx.exception).lower())
        self.assertIn("count_tme", str(ctx.exception))

    def test_bulk_matches_serial(self):
        lines = ["Hello 🍎", "World 🍌🍌", "No emoji here", "🎉🎉🎉"]
        bulk = self.ext.count_all_emoji(lines)
        # Manually aggregate serial results
        serial = Counter()
        for line in lines:
            serial.update(self.ext.count_emoji(line))
        self.assertEqual(bulk, serial)

    def test_bulk_string_raises(self):
        with self.assertRaises(TypeError):
            self.ext.count_all_emoji("not an iterable of strings")
        with self.assertRaises(TypeError):
            self.ext.count_all_tme("not an iterable of strings")
        with self.assertRaises(TypeError):
            self.ext.count_all_tones("not an iterable of strings")

    def test_n_workers_parameter(self):
        ext = Extractor(n_workers=2)
        self.assertEqual(ext.n_workers, 2)
        ext.close()

    def test_close_pool(self):
        ext = Extractor()
        ext.close()  # Should not raise even with no pool
        ext.close()  # Should be safe to call twice


if __name__ == '__main__':
    unittest.main()
