#!/usr/bin/python3

import os
import sys
import pathlib
import argparse
import csv

def find_common(needle_path: pathlib.Path, needle_column: str, haystack_path: pathlib.Path, haystack_column: str):
	needles = set()

	with open(needle_path, 'r') as f:
		reader = csv.reader(f)
		header = next(reader)
		try:
			column_idx = header.index(needle_column)
		except ValueError:
			print('Needle column {} not found in needle file header {}'.format(needle_column, header), file=sys.stderr)
			raise

		for row in reader:
			needles.add(row[column_idx])

	with open(haystack_path, 'r') as f_in:
		reader = csv.reader(f_in)
		header = next(reader)
		column_idx = header.index(haystack_column)

		writer = csv.writer(sys.stdout)
		writer.writerow(header)

		for row in reader:
			haystack_value = row[column_idx]
			if haystack_value in needles:
				writer.writerow(row)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Prints rows from one CSV file if a particular column matches values from a column of another CSV file.')
	parser.add_argument('needle_path', type=pathlib.Path, help='Path to a CSV file to load needle values from.')
	parser.add_argument('needle_column', type=str, help='Column in the needles file that contains needle values.')
	parser.add_argument('haystack_path', type=pathlib.Path, help='Path to a CSV file whose haystack column is the haystack.')
	parser.add_argument('haystack_column', type=str, help='Column in the haystack file to search for needle values. Any row that has a needle value in this column is considered a match.')
	opts = parser.parse_args()
	sys.exit(find_common(opts.needle_path, opts.needle_column, opts.haystack_path, opts.haystack_column))
