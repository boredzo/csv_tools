#!/usr/bin/env python3

import pathlib
import subprocess
import unittest

class TestHistogram(unittest.TestCase):
	def test_count(self):
		csv_histo = subprocess.Popen([ 'bin/csv_histo.py', '--only-report', 'test_data/csv_histo_test.csv' ], stderr=subprocess.PIPE)
		gotUniques = False
		gotRowsCounted = False
		gotAllRows = False
		for line in csv_histo.stderr:
			line = line.strip().decode('utf-8')
			category, num_rows = line.split('\t', 1)
			num_rows = int(num_rows)
			if category == 'unique combinations':
				self.assertEqual(num_rows, 7)
				gotUniques = True
			elif category == 'rows counted':
				self.assertEqual(num_rows, 7)
				gotRowsCounted = True
			elif category == 'all rows':
				self.assertEqual(num_rows, 7)
				gotAllRows = True
			else:
				self.fail('unknown category {!r}'.format(category))
		self.assertTrue(gotUniques)
		self.assertTrue(gotRowsCounted)
		self.assertTrue(gotAllRows)
		self.assertEqual(csv_histo.wait(), 0)

if __name__ == "__main__":
	unittest.main()
