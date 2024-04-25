#!/usr/bin/python3

import os
import sys
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

def prefix_row(orig_row: list, prefix: str):
	if not orig_row: return orig_row
	return [ prefix + str(orig_row[0]) ] + orig_row[1:]

def compare_tables_sorted(left_path: pathlib.Path, right_path: pathlib.Path, writer: csv.writer, match_keys: list, check_equal_keys: list, max_differences=None):
	"Print every row for which all of the values for match keys are equal and the values for check_equal_keys are not equal. This implementation assumes both tables are already sorted by all of the match_keys. Returns a tuple of Booleans indicating whether the left table was missing entries found in the right, the right table was missing entries from the left, and any matched rows were found to be unequal in the checked columns. The return values may not be comprehensive if max_differences (if not None, an integer limiting the number of differences before returning failure) is reached."

	left_missing_entries = False
	right_missing_entries = False
	matched_rows_unequal = False
	num_differences = 0

	with open(left_path, 'r') as f_left:
		with open(right_path, 'r') as f_right:
			left_reader = csv.reader(f_left)
			right_reader = csv.reader(f_right)
			left_header = next(left_reader)
			right_header = next(right_reader)

			left_match_indexes = []
			right_match_indexes = []
			for k in match_keys:
				left_match_indexes.append(left_header.index(k))
				right_match_indexes.append(right_header.index(k))

			left_check_equal_indexes = []
			right_check_equal_indexes = []
			for k in check_equal_keys:
				left_check_equal_indexes.append(left_header.index(k))
				right_check_equal_indexes.append(right_header.index(k))

			left_row = next(left_reader)
			right_row = next(right_reader)
			while left_row and right_row:
				left_match_values = get_from_indexes(left_row, left_match_indexes)
				right_match_values = get_from_indexes(right_row, right_match_indexes)
				if left_match_values < right_match_values:
					# The right table has skipped an entry.
					writer.writerow(prefix_row(left_row, '-'))
					right_missing_entries = True
					num_differences += 1
					left_row = next(left_reader)
				elif left_match_values > right_match_values:
					# The left table has skipped an entry.
					writer.writerow(prefix_row(right_row, '+'))
					left_missing_entries = True
					num_differences += 1
					right_row = next(right_reader)
				else:
					# We've matched two rows together. Compare the values that are expected to also be equal.
					left_check_equal_values = get_from_indexes(left_row, left_check_equal_indexes)
					right_check_equal_values = get_from_indexes(right_row, right_check_equal_indexes)
					if left_check_equal_values != right_check_equal_values:
						matched_rows_unequal = True
						num_differences += 1
						if writer is not None:
							writer.writerow(prefix_row(left_row, '-'))
							writer.writerow(prefix_row(right_row, '+'))

					left_row = next(left_reader)
					right_row = next(right_reader)

				if max_differences and num_differences >= max_differences:
					break

	return left_missing_entries, right_missing_entries, matched_rows_unequal

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Prints rows from one CSV file matched to rows another CSV file on the basis of some columns if those rows are not equal in other columns.')
	parser.add_argument('--match-column', action='append', dest='match_keys', help='A column to match rows upon. Rows are matched if all of their values for all match columns are equal. This flag can be used multiple times to match on multiple columns.')
	parser.add_argument('--check-column', action='append', dest='check_equal_keys', help="A column to check for equality between matched rows. A check fails if the two matched rows' values for a checked column are not equal. This flag can be used multiple times to check multiple columns.")
	parser.add_argument('--assume-sorted', action='store_true', default=False, help='Assume that both tables are sorted by all of the match columns in order. [NOTE: Currently required. Use sort(1) and possibly csv_permute to put both tables into sorted order.]')
	parser.add_argument('--max-differences', type=int, default=10, help='Bail out if more than this many differences are detected. Defaults to 10. Set to 0 for unlimited differences.')
	parser.add_argument('left_path', type=pathlib.Path, help='Path to a CSV file containing the table that will be considered to be on the left.')
	parser.add_argument('right_path', type=pathlib.Path, help='Path to a CSV file containing the table that will be considered to be on the right.')
	opts = parser.parse_args()
	if not opts.assume_sorted:
		sys.exit("Comparing unsorted tables is not yet implemented. Sort both tables, then use --assume-sorted.")

	left_missing_entries, right_missing_entries, matched_rows_unequal = compare_tables_sorted(opts.left_path, opts.right_path, csv.writer(sys.stdout), opts.match_keys, opts.check_equal_keys, max_differences=opts.max_differences or None)

	exit_status = (
		0
		| left_missing_entries << 2
		| right_missing_entries << 1
		| matched_rows_unequal << 0
	)
	sys.exit(exit_status)
