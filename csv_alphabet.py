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

def select_distinct(input_path: pathlib.Path, column_of_interest: str):
	found_values = set()

	with open(input_path, 'r') as input_file:
		reader = csv.reader(input_file)
		header = next(reader)
		idx = header.index(column_of_interest)
		
		for orig_row in reader:
			found_values.add(orig_row[idx])

	return found_values

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('column_name', help="Column to collect distinct values from.")
	parser.add_argument('input_paths', type=pathlib.Path, nargs='+', help="Paths to files containing CSV data to inventory.")
	opts = parser.parse_args()

	all_values = set()
	for input_path in opts.input_paths:
		num_values = 0
		these_values = select_distinct(input_path, opts.column_name)
		all_values |= these_values
	for value in all_values:
		print(value)
		num_values += 1
	print('{}\t{:n}'.format('total', num_values), file=sys.stderr)
