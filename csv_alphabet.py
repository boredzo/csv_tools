#!/usr/bin/python3

import sys
import os
import pathlib
import argparse
import csv
import locale

locale.setlocale(locale.LC_ALL, '')

def get_from_indexes(orig_row, indexes):
	permuted_row = [ orig_row[i] for i in indexes ]
	return permuted_row

def select_distinct(input_path: pathlib.Path, columns_of_interest: list):
	found_values = set()

	with open(input_path, 'r') as input_file:
		reader = csv.reader(input_file)
		header = next(reader)

		indexes = [ header.index(col) for col in columns_of_interest ]
		
		for orig_row in reader:
			permuted_row = get_from_indexes(orig_row, indexes)
			found_values.add(tuple(permuted_row))

	return found_values

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--column', action='append', dest='column_names', help="Column to collect distinct values from.")
	parser.add_argument('input_paths', type=pathlib.Path, nargs='+', help="Paths to files containing CSV data to inventory.")
	opts = parser.parse_args()

	all_combos = set()
	num_combos = 0
	for input_path in opts.input_paths:
		these_combos = select_distinct(input_path, opts.column_names)
		all_combos |= these_combos

	writer = csv.writer(sys.stdout)
	for combination in sorted(all_combos):
		writer.writerow(combination)
		num_combos += 1
	print('{}\t{:n}'.format('total', num_combos), file=sys.stderr)
