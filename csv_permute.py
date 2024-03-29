#!/usr/bin/python3

import os
import sys
import argparse
import csv

def get_from_indexes(orig_row, indexes):
	permuted_row = [ orig_row[i] for i in indexes ]
	return permuted_row

def csv_permute(reader, writer, leading_columns):
	header = next(reader)
	indexes = []
	try:
		for col in leading_columns:
			indexes.append(header.index(col))
	except ValueError:
		print('Header row:', header, file=sys.stderr)
		raise
	for i, col in enumerate(header):
		if col in leading_columns:
			pass
		else:
			indexes.append(i)

	permuted_header = get_from_indexes(header, indexes)
	writer.writerow(permuted_header)

	for orig_row in reader:
		permuted_row = get_from_indexes(orig_row, indexes)
		writer.writerow(permuted_row)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('leading_columns', nargs='+', default=[], help='Columns to move to the start of a row, in order.')
	opts = parser.parse_args()

	leading_columns = opts.leading_columns

	reader = csv.reader(sys.stdin)
	writer = csv.writer(sys.stdout)
	csv_permute(reader, writer, leading_columns)
