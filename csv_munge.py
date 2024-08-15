#!/usr/bin/python3

import sys
import os
import pathlib
import argparse
import csv
import datetime

def title_case(value: str):
	return value.title()
def date_format(fmt: str, year: int, month: int, day: int):
	return datetime.date(year=year, month=month, day=day).strftime(fmt)

def index_of_column_in_header(key_header: list, col: str):
	try:
		idx = key_header.index(col)
	except ValueError:
		return -1
	else:
		return idx

def get_from_indexes(orig_row, indexes):
	permuted_row = [ orig_row[i] for i in indexes ]
	return permuted_row

#mark -

def munge(reader: csv.reader, orig_header: list, writer: csv.writer, title_case_columns: list, date_columns: list, values_to_replace_with_empty: list):
	"Munge values in a table."
	row_count = 0

	munged_header = list(orig_header)
	values_to_replace_with_empty = set(values_to_replace_with_empty)

	date_column_indexes = []
	if date_columns:
		date_column_names = {}
		for (year_col, month_col, day_col, date_fmt, date_col) in date_columns:
			year_idx = index_of_column_in_header(orig_header, year_col)
			if year_idx < 0:
				print('No such year column:', repr(col), file=sys.stderr)
				continue
			month_idx = index_of_column_in_header(orig_header, month_col)
			if month_idx < 0:
				print('No such month column:', repr(col), file=sys.stderr)
				continue
			day_idx = index_of_column_in_header(orig_header, day_col)
			if day_idx < 0:
				print('No such day column:', repr(col), file=sys.stderr)
				continue
			# Note: day_idx is here first as a sort key, then as itself.
			date_column_indexes.append((day_idx, year_idx, month_idx, day_idx, date_fmt, None))
			date_idx = max(year_idx, month_idx, day_idx) + 1
			date_column_names[date_idx] = date_col
		date_column_indexes.sort()
		# TODO: Handle the consequences of column insertions upon date columns that follow the inserted column(s). (The next loop already handles them by using the munged header.)
		for i, v in enumerate(list(date_column_indexes)):
			day_idx, year_idx, month_idx, day_idx, date_fmt, date_idx = v
			date_idx = max(year_idx, month_idx, day_idx) + 1
			munged_header.insert(date_idx, date_column_names[date_idx])
			# Note: Sort key gets dropped from the tuple here.
			date_column_indexes[i] = (year_idx, month_idx, day_idx, date_fmt, date_idx)

	title_case_column_indexes = []
	if title_case_columns:
		for col in title_case_columns:
			try:
					title_case_column_indexes.append(index_of_column_in_header(munged_header, col))
			except ValueError:
				print('No such column:', repr(col), file=sys.stderr)

	try:
		writer.writerow(munged_header)

		for orig_row in reader:
			munged_row = list(orig_row)
			for i, value in enumerate(orig_row):
				if value in values_to_replace_with_empty:
					munged_row[i] = ''

			for (year_idx, month_idx, day_idx, date_fmt, date_idx) in date_column_indexes:
				try:
					year = int(orig_row[year_idx])
					month = int(orig_row[month_idx])
					day = int(orig_row[day_idx])
				except ValueError:
					munged_row.insert(date_idx, '')
				else:
					try:
						date = datetime.date(year, month, day)
					except ValueError:
						print('Bogus date: %r-%r-%r' % (year, month, day), file=sys.stderr)
						munged_row.insert(date_idx, '')
					else:
						munged_row.insert(date_idx, date.strftime(date_fmt))

			for col_idx in title_case_column_indexes:
				orig_value = orig_row[col_idx]
				munged_value = title_case(orig_value)
				munged_row[col_idx] = munged_value

			writer.writerow(munged_row)
			row_count += 1
	except BrokenPipeError:
		# We're probably being piped into head or something. This is not a problem.
		pass

	return row_count

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--title-case', dest='title_case_columns', metavar='COLUMN', action='append', help="Name of a column whose values should be converted to Title Case. Can be used multiple times.")
	parser.add_argument('--format-date', dest='date_columns', nargs=5, metavar=( 'YEAR_COLUMN', 'MONTH_COLUMN', 'DAY_COLUMN', 'DATE_FORMAT', 'DATE_COLUMN_NAME' ), action='append', help="Names of three existing columns, a date format, and the name for a new column to insert after the three others. For example, --format-date Year Month Day '%%Y-%%m-%%d' ISO8601Date. Can be used multiple times.")
	parser.add_argument('--suppress', dest='values_to_replace_with_empty', action='append', metavar='SENTINEL', help="Replace all values equal to a SENTINEL with empty values. Can be used multiple times.")
	parser.add_argument('input_path', nargs='?', default=None, type=pathlib.Path, help="Path to a files containing CSV data to process.")
	opts = parser.parse_args()

	path = opts.input_path if opts.input_path else '-'
	writer = csv.writer(sys.stdout)

	with open(opts.input_path, 'r')  if opts.input_path else sys.stdin as f:
		reader = csv.reader(f)
		key_header = next(reader)
		row_count = munge(reader, key_header, writer, opts.title_case_columns, opts.date_columns, opts.values_to_replace_with_empty)
		print('{}\t{:n}'.format(path, row_count), file=sys.stderr)

if __name__ == "__main__":
	main()
