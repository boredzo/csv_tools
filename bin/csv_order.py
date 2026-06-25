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

class ReversedComparable:
	def __init__(self, obj):
		self.obj = obj
	def __lt__(self, other):
		return self.obj >= other.obj
	def __le__(self, other):
		return self.obj > other.obj
	def __gt__(self, other):
		return self.obj <= other.obj
	def __ge__(self, other):
		return self.obj < other.obj
	def __cmp__(self, other):
		return -cmp(self.obj, other.obj)

class SortColumn:
	def __init__(self, name, reverse=False, value_type=str):
		self.name = name
		self.reverse = reverse
		self.value_type = value_type
		assert callable(self.value_type)
	def parse_value(self, value_str):
		value = self.value_type(value_str)
		if self.reverse:
			value = ReversedComparable(value)
		return value

def validate_schema(input_path: pathlib.Path, sort_columns: list):
	"Returns (valid, missing_columns) where valid is True if none of the indicated columns are missing from the file's header, or False if one or more columns are missing. In the latter case, missing_columns is a list of those columns."
	with open(input_path, 'r') as input_file:
		reader = csv.reader(input_file)
		header = next(reader)
		missing_columns = [ col for col in sort_columns if col.name not in header ]
		return (not missing_columns), missing_columns
	
def order_rows(input_path: pathlib.Path, sort_columns: list, writer: csv.writer, opts: argparse.Namespace):
	all_row_count = 0
	included_row_count = 0 # all_row_count minus dropped rows.

	with open(input_path, 'r') as input_file:
		reader = csv.reader(input_file)
		header = next(reader)

		indexes_to_consider = [ header.index(col.name) for col in sort_columns ]
		sortable_rows = []

		for orig_row in reader:
			all_row_count += 1
			sort_item_strs = get_from_indexes(orig_row, indexes_to_consider)
			if opts.only_nonempty:
				drop_this_row = False
				for value in sort_item_strs:
					if not value:
						drop_this_row = True
						break
				if drop_this_row:
					continue
			included_row_count += 1

			sort_items = [ col.parse_value(value_str) for col, value_str in zip(sort_columns, sort_item_strs) ]
			sortable_rows.append((sort_items, orig_row))

	sortable_rows.sort()
	writer.writerow(header)
	for sort_items, orig_row in sortable_rows:
		writer.writerow(orig_row)

	return included_row_count, all_row_count

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--column', action='append', dest='sort_columns', help="Order by this column. Can be used multiple times to order by multiple columns.")
	parser.add_argument('--only-nonempty', '--only-non-empty', action='store_true', default=False, help="Omit rows for which the order column is empty.")
	parser.add_argument('input_paths', type=pathlib.Path, nargs='+', help="Path to one or more files containing CSV data to concatenate into one large file. The first file's header determines the schema of all others; any files with a different header will be skipped.")
	opts = parser.parse_args()

	sort_columns = [ SortColumn(name) for name in opts.sort_columns ]

	all_valid = True
	missing_columns_by_path = {}
	for path in opts.input_paths:
		valid, missing_columns = validate_schema(path, sort_columns)
		if not valid:
			all_valid = False
			missing_columns_by_path[path] = missing_columns
	if not all_valid:
		print('{}\t{}'.format('source', 'missing_columns'))
		for path in opts.input_paths:
			missing_columns = missing_columns_by_path[path]
			if missing_columns:
				#TODO: Use proper CSV representation (csv.writer) here
				print('{}\t{}'.format(str(path), ','.join(col.name for col in missing_columns)), file=sys.stderr)

		sys.exit(1)

	# OK, all the input files have all the requested ordering columns. Proceed.
	writer = csv.writer(sys.stdout)

	print('{}\t{}\t{}\t{}'.format('path', 'included', 'dropped', 'all'), file=sys.stderr)

	total_included_row_count = 0
	total_all_row_count = 0
	for path in opts.input_paths:
		included_row_count, all_row_count = order_rows(path, sort_columns, writer, opts)

		print('{}\t{:n}\t{:n}\t{:n}'.format(str(path), included_row_count, all_row_count - included_row_count, all_row_count), file=sys.stderr)
		total_included_row_count += included_row_count
		total_all_row_count += all_row_count

	print('{}\t{:n}\t{:n}\t{:n}'.format('total', total_included_row_count, total_all_row_count - total_included_row_count, total_all_row_count), file=sys.stderr)
