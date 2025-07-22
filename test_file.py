import unittest
from file import extract_first_line, split_multiple_types, has_invalid_type

class TestExtractFirstLine(unittest.TestCase):
    def test_albatross(self):
        self.assertEqual(extract_first_line('Albatross'), 'Albatross')

    def test_alpaca_with_reference(self):
        self.assertEqual(extract_first_line('Alpaca\n[14]'), 'Alpaca')

    def test_boar_multiline(self):
        self.assertEqual(extract_first_line('Boar\n/wild pig\nAlso see\nPig'), 'Boar')

class TestSplitMultipleTypes(unittest.TestCase):
    def test_multiple_types(self):
        self.assertEqual(split_multiple_types('diomedeid\ndiomedeine'), ['diomedeid', 'diomedeine'])

    def test_single_type(self):
        self.assertEqual(split_multiple_types('camelid'), ['camelid'])

class TestHasInvalidType(unittest.TestCase):
    def test_dash(self):
        self.assertTrue(has_invalid_type(['—']))

    def test_empty(self):
        self.assertTrue(has_invalid_type([]))

    def test_valid_single(self):
        self.assertFalse(has_invalid_type(['potosine']))

    def test_valid_multiple(self):
        self.assertFalse(has_invalid_type(['phascolarctid', 'phascolarctine']))

if __name__ == "__main__":
    unittest.main() 