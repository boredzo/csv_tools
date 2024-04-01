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

def has_nonempty_values(seq):
	"Iterate through the iterable seq and return True if any non-empty (truthy) value is encountered. Return False if not."
	for x in seq:
		if x:
			return True
	else:
		return False

def filter_rows(input_path: pathlib.Path, key_header: list, writer: csv.writer, opts: argparse.Namespace):
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

		indexes_to_consider = [ i for i, col in enumerate(header) if col not in opts.exclude_columns ]

		for orig_row in reader:
			matched_criteria = 0
			all_criteria = 0
			subrow = get_from_indexes(orig_row, indexes_to_consider)

			if opts.only_nonempty:
				all_criteria += 1
				matched_criteria += has_nonempty_values(filter(None, subrow))

			if matched_criteria == all_criteria:
				writer.writerow(orig_row)
				row_count += 1

	return key_header, row_count

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-x', '--except-column', action='append', dest='exclude_columns', help="Don't apply filtering criteria to this column. Can be used multiple times to exclude multiple columns.")
	parser.add_argument('--only-nonempty', '--only-non-empty', action='store_true', default=False, help="Select only rows for which any non-excluded column contains data.")
	parser.add_argument('input_paths', type=pathlib.Path, nargs='+', help="Path to one or more files containing CSV data to concatenate into one large file. The first file's header determines the schema of all others; any files with a different header will be skipped.")
	opts = parser.parse_args()

	writer = csv.writer(sys.stdout)

	total_row_count = 0
	key_header = None
	for path in opts.input_paths:
		header, row_count = filter_rows(path, key_header, writer, opts)
		if key_header is None:
			key_header = header
		if row_count is None:
			print('Skipped due to non-matching schema:', path, file=sys.stderr)
		else:
			print('{}\t{:n}'.format(path, row_count), file=sys.stderr)
			total_row_count += row_count
	print('{}\t{:n}'.format('total', total_row_count), file=sys.stderr)
