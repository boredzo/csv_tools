#!/usr/bin/python3

import sys
import os
import pathlib
import argparse
import csv
import locale

locale.setlocale(locale.LC_ALL, '')

def cat(input_path, key_header, writer):
	row_count = 0

	with open(input_path, 'r') as input_file:
		reader = csv.reader(input_file)
		header = next(reader)
		if key_header is None:
			key_header = header
			writer.writerow(key_header)
		elif key_header != header:
			#Non-matching schema. Skip.
			return header, None

		for row in reader:
			writer.writerow(row)
			row_count += 1

	return key_header, row_count

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('input_paths', type=pathlib.Path, nargs='+', help="Path to one or more files containing CSV data to concatenate into one large file. The first file's header determines the schema of all others; any files with a different header will be skipped.")
	opts = parser.parse_args()

	writer = csv.writer(sys.stdout)

	total_row_count = 0
	key_header = None
	for path in opts.input_paths:
		header, row_count = cat(path, key_header, writer)
		if key_header is None:
			key_header = header
		if row_count is None:
			print('Skipped due to non-matching schema:', path, file=sys.stderr)
		else:
			print('{}\t{:n}'.format(path, row_count), file=sys.stderr)
			total_row_count += row_count
	print('{}\t{:n}'.format('total', total_row_count), file=sys.stderr)
