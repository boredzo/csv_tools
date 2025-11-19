#!/usr/bin/python3

import sys
import os
import pathlib
import argparse
import csv
import io
import locale

locale.setlocale(locale.LC_ALL, '')

def lint(input_file, input_file_isoLatin1, verbose, quote_character):
	try:
		row_count = 0

		reader = csv.reader(input_file, quotechar=quote_character)
		header = next(reader)

		expected_column_count = len(header)

		for row in reader:
			row_count += 1
			# NOTE: The row numbers here are intentionally not put through {:n} so they can be passed to various “go to line” commands in text editors and spreadsheets.
			this_column_count = len(row)
			if this_column_count < expected_column_count:
				print('{}: Column underflow: Expected {:n} columns, got {:n}'.format(row_count, expected_column_count, this_column_count), file=sys.stderr)
				if verbose:
					for row_idx, column, value in zip(range(len(row)), header, row):
						print('{}\t{}\t{}'.format(row_idx, column, value or '(empty)'))
			elif this_column_count > expected_column_count:
				print('{}: Column overflow: Expected {:n} columns, got {:n}'.format(row_count, expected_column_count, this_column_count), file=sys.stderr)
				if verbose:
					extension = [ '???' ] * (len(row) - len(header))
					for row_idx, column, value in zip(range(len(row)), header + extension, row):
						print('{}\t{}\t{}'.format(row_idx, column, value or '(empty)'))
	except UnicodeDecodeError:
		row_count += 1
		print('{}: Failed to decode UTF-8. Failing over to ISO-8859-1.'.format(row_count), file=sys.stderr)
		last_row_count = row_count
		row_count = 0

		reader = csv.reader(input_file_isoLatin1, quotechar=quote_character)
		header = next(reader)

		expected_column_count = len(header)

		for row in reader:
			row_count += 1
			if row_count < last_row_count:
				continue

			# NOTE: The row numbers here are intentionally not put through {:n} so they can be passed to various “go to line” commands in text editors and spreadsheets.
			this_column_count = len(row)
			if this_column_count < expected_column_count:
				print('{}: Column underflow: Expected {:n} columns, got {:n}'.format(row_count, expected_column_count, this_column_count), file=sys.stderr)
				if verbose:
					for row_idx, column, value in zip(range(len(row)), header, row):
						print('{}\t{}\t{}'.format(row_idx, column, value or '(empty)'))
			elif this_column_count > expected_column_count:
				print('{}: Column overflow: Expected {:n} columns, got {:n}'.format(row_count, expected_column_count, this_column_count), file=sys.stderr)
				if verbose:
					extension = [ '???' ] * (len(row) - len(header))
					for row_idx, column, value in zip(range(len(row)), header + extension, row):
						print('{}\t{}\t{}'.format(row_idx, column, value or '(empty)'))

	return row_count

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-v', '--verbose', default=False, action='store_true')
	parser.add_argument('--quote-character', '--quote-char', '--quotechar', default='"', help='Set the quote character used for parsing quoted values. Defaults to ".')
	parser.add_argument('input_paths', type=pathlib.Path, nargs='*', help="Path to one or more files containing CSV data to count rows of. If omitted, read from stdin.")
	opts = parser.parse_args()

	if opts.input_paths:
		total_row_count = 0
		for input_path in opts.input_paths:
			with open(input_path, 'r') as input_file:
				with open(input_path, 'r', encoding='iso-8859-1') as input_file_isoLatin1:
					row_count = lint(input_file, input_file_isoLatin1, opts.verbose, opts.quote_character)
					if len(opts.input_paths) > 1:
						print('{}\t{:n}'.format(input_path, row_count))
					else:
						print('{:n}'.format(row_count))
					total_row_count += row_count
		print('{}\t{:n}'.format('total', total_row_count))
	else:
		path = '-'
		input_file = sys.stdin
		with io.TextIOWrapper(sys.stdin.buffer, encoding='iso-8859-1') as input_file_isoLatin1:
			row_count = lint(input_file, input_file_isoLatin1, opts.verbose)
			if len(opts.input_paths) > 1:
				print('{}\t{:n}'.format(path, row_count))
			else:
				print('{:n}'.format(row_count))
