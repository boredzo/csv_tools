#!/usr/bin/python3

import sys
import os
import pathlib
import argparse
import csv

def count_records(input_path):
	row_count = 0

	with open(input_path, 'r') as input_file:
		reader = csv.reader(input_file)
		header = next(reader)

		for row in reader:
			row_count += 1

	return row_count

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('input_paths', type=pathlib.Path, nargs='+', help="Path to one or more files containing CSV data to concatenate into one large file. The first file's header determines the schema of all others; any files with a different header will be skipped.")
	opts = parser.parse_args()

	total_row_count = 0
	for path in opts.input_paths:
		row_count = count_records(path)
		if len(opts.input_paths) > 1:
			print('{}\t{:n}'.format(path, row_count))
		else:
			print('{:n}'.format(row_count))
		total_row_count += row_count
	if len(opts.input_paths) > 1:
		print('{}\t{:n}'.format('total', total_row_count))
