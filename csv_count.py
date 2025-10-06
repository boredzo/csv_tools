#!/usr/bin/python3

import sys
import os
import pathlib
import argparse
import csv
import locale

locale.setlocale(locale.LC_ALL, '')

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

	if len(opts.input_paths) > 1:
		print('count\tfile')

	if opts.input_paths:
		total_row_count = 0
		for input_path in opts.input_paths:
			with open(input_path, 'r') as input_file:
				row_count = count_records(input_file)
				if len(opts.input_paths) > 1:
					print('{:n}\t{}'.format(row_count, input_path))
				else:
					print('{:n}'.format(row_count))
				total_row_count += row_count
		print('{:n}\t{}'.format(total_row_count, 'total'))
	else:
		path = '-'
		input_file = sys.stdin

		row_count = count_records(input_file)
		if len(opts.input_paths) > 1:
			print('{:n}\t{}'.format(row_count, path))
		else:
			print('{:n}'.format(row_count))
