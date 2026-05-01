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

if __name__ == '__main__':
    unittest.main()
