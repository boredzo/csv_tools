#!/usr/bin/python3

import sys
import os
import pathlib
import argparse
import csv

def count_records(input_file):
	row_count = 0

	reader = csv.reader(input_file)
	header = next(reader)

	for row in reader:
		row_count += 1

	return row_count

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('input_paths', type=pathlib.Path, nargs='*', help="Path to one or more files containing CSV data to count rows of. If omitted, read from stdin.")
	opts = parser.parse_args()

	if opts.input_paths:
		total_row_count = 0
		for path in opts.input_paths:
			with open(input_path, 'r') as input_file:
				row_count = count_records(input_file)
				if len(opts.input_paths) > 1:
					print('{}\t{:n}'.format(path, row_count))
				else:
					print('{:n}'.format(row_count))
				total_row_count += row_count
		print('{}\t{:n}'.format('total', total_row_count))
	else:
		path = '-'
		input_file = sys.stdin

		row_count = count_records(input_file)
		if len(opts.input_paths) > 1:
			print('{}\t{:n}'.format(path, row_count))
		else:
			print('{:n}'.format(row_count))
