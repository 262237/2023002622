import tempfile
import unittest
from pathlib import Path
from PIL import Image
import numpy as np
from plant_data import make_split, image_array

class DataTests(unittest.TestCase):
    def test_deterministic_disjoint_split_and_duplicate_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for c in range(2):
                (root / str(c)).mkdir()
                for i in range(20):
                    Image.new('RGB', (10, 10), (c * 100, i * 10, 30)).save(root / str(c) / f'{i}.png')
            Image.open(root / '0/0.png').save(root / '0/copy.png')
            split = make_split(root)
            self.assertEqual(split, make_split(root))
            self.assertEqual(split['counts'], {'test': 4, 'validation': 4, 'train': 32})
            self.assertEqual(len(split['duplicates_removed']), 1)
            hashes = [r['sha256_pixels'] for r in split['records']]
            self.assertEqual(len(hashes), len(set(hashes)))
            for name in ('train', 'validation', 'test'):
                self.assertEqual({r['class'] for r in split['records'] if r['split'] == name}, {'0', '1'})

    def test_preprocessing_rgb_shape_and_range(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'gray.png'
            Image.new('L', (10, 20), 128).save(path)
            pixels = image_array(path, 160)
            self.assertEqual(pixels.shape, (160, 160, 3))
            self.assertEqual(pixels.dtype, np.float32)
            self.assertTrue(np.all(pixels == 128))

    def test_conflicting_duplicate_labels_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for label in ['healthy', 'diseased']:
                (root / label).mkdir()
                Image.new('RGB', (8, 8), (20, 40, 60)).save(root / label / 'same.png')
            with self.assertRaisesRegex(ValueError, 'conflicting labels'):
                make_split(root)

if __name__ == '__main__':
    unittest.main()
