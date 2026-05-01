import unittest
import os
from unittest.mock import patch

from emoji_extractor import Extractor, detect_emoji, count_emoji

class TestExtractor(unittest.TestCase):

    def test_extractor_init_latest(self):
        extractor = Extractor()
        self.assertEqual(extractor.version, 'latest')

    def test_extractor_invalid_version(self):
        with self.assertRaises(ValueError) as context:
            Extractor(version='99.9')
        self.assertIn("Emoji data for version '99.9' not found", str(context.exception))

    def test_lazy_loading(self):
        extractor = Extractor()
        # At this point, no files should have been read.
        self.assertIsNone(extractor._big_regex)
        self.assertIsNone(extractor._possible_emoji)
        self.assertIsNone(extractor._tme)
        
        # Trigger lazy load
        pattern = extractor.big_regex
        self.assertIsNotNone(pattern)
        self.assertIsNotNone(extractor._big_regex)

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

    @patch('pkg_resources.resource_filename')
    def test_version_isolation(self, mock_resource_filename):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_path:
            version_dir = os.path.join(tmp_path, "1.0")
            os.mkdir(version_dir)
            
            with open(os.path.join(version_dir, "possible_emoji.json"), "w", encoding="utf-8") as f:
                f.write('["🍎"]')
            with open(os.path.join(version_dir, "big_regex.txt"), "w", encoding="utf-8") as f:
                f.write('🍎')
            with open(os.path.join(version_dir, "tme_regex.txt"), "w", encoding="utf-8") as f:
                f.write('🍎')
                
            mock_resource_filename.return_value = version_dir
            
            extractor = Extractor(version='1.0')
            self.assertEqual(extractor.version, '1.0')
            self.assertTrue(extractor.detect_emoji("Testing 🍎"))
            self.assertFalse(extractor.detect_emoji("Testing 1️⃣"))

    def test_all_downloaded_versions(self):
        # We ensure that every version we've downloaded can be instantiated
        # and has a non-empty regex pattern.
        for version in ['4.0', '5.0', '11.0', '12.0', '12.1', '13.0', '14.0', '15.0', '15.1', '16.0', 'latest']:
            extractor = Extractor(version=version)
            self.assertEqual(extractor.version, version)
            self.assertIsNotNone(extractor.big_regex)
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

if __name__ == '__main__':
    unittest.main()
