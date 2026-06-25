#!/usr/bin/env python3

import pathlib
import csv
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

	def test_multipleMatches(self):
		csv_histo = subprocess.Popen([ 'bin/csv_histo.py', '--only-columns=first,last', 'test_data/csv_histo_test.csv' ], stdout=subprocess.PIPE, stderr=open('/dev/null', 'w'), text=True)
		expected = {
			('John', 'Egbert'): 1,
			('Rose', 'Lalonde'): 1,
			('Dave', 'Strider'): 3,
			('Jade', 'Harley'): 2,
		}
		reader = csv.reader(csv_histo.stdout)
		next(reader)
		for row in reader:
			key = tuple(row[1:])
			expected_count = expected[key]
			actual_count = int(row[0])
			self.assertEqual(expected_count, actual_count, 'incorrect count for {!r}'.format(key))

		self.assertEqual(csv_histo.wait(), 0)

if __name__ == "__main__":
	unittest.main()
