#!/usr/bin/python3

import sys
import os
import pathlib
import argparse
import csv
import collections
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

def histogram(reader: csv.reader, orig_header: list, writer: csv.writer, opts: argparse.Namespace):
	num_all = 0

	columns_of_interest = opts.only_columns
	if columns_of_interest:
		# TODO: Use csv.reader to parse this
		columns_of_interest = columns_of_interest.split(',')
		indexes = []
		for col in columns_of_interest:
			try:
				idx = orig_header.index(col)
			except ValueError:
				pass
			else:
				indexes.append(idx)
	else:
		indexes = None

	counter = collections.Counter()

	for orig_row in reader:
		selected_values = tuple(orig_row if not indexes else get_from_indexes(orig_row, indexes))
		counter[selected_values] += 1
		num_all += 1

	pairs = [
		(count, selected_values)
		for (selected_values, count)
		in counter.items()
		if (opts.min_count <= count and (opts.max_count is None or count <= opts.max_count))
	]
	pairs.sort()

	num_matched = 0
	writer.writerow(orig_header if not columns_of_interest else get_from_indexes(orig_header, indexes))
	for count, selected_values in reversed(pairs):
		writer.writerow([ count ] + list(selected_values))
		num_matched += count

	num_combos = len(pairs)
	num_rows = len(counter)
	return num_combos, num_matched, num_all

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--input-encoding', action='store', default='utf-8', help='Encoding to use for decoding the input file.')
	parser.add_argument('--only-columns', default=None, help="Comma-separated list of columns to examine. Defaults to all columns. Counts are of unique groups of values from these columns only.")
	parser.add_argument('--min-count', default=0, type=int, help="Only report combinations that appear at least this many times.")
	parser.add_argument('--max-count', default=None, type=int, help="Only report combinations that appear no more than this many times.")
	parser.add_argument('input_path', nargs='?', default=None, type=pathlib.Path, help="Path to a file containing CSV data to count value groups from.")
	opts = parser.parse_args()

	writer = csv.writer(sys.stdout)

	path = opts.input_path
	if path:
		with open(path, 'r', encoding=opts.input_encoding) as f:
			reader = csv.reader(f)
			header = next(reader)

			row_count = histogram(reader, header, writer, opts)
			print('{}\t{:n}'.format(path, row_count), file=sys.stderr)
	else:
		reader = csv.reader(sys.stdin)
		header = next(reader)

		num_combos, num_matched, num_all = histogram(reader, header, writer, opts)
		print('{}\t{:n}'.format('unique combinations', num_combos), file=sys.stderr)
		print('{}\t{:n}'.format('rows counted', num_matched), file=sys.stderr)
		print('{}\t{:n}'.format('all rows', num_all), file=sys.stderr)

if __name__ == "__main__":
	main()
