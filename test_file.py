import unittest
from file import extract_first_line, split_multiple_types

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

if __name__ == "__main__":
    unittest.main() 