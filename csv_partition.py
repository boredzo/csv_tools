#!/usr/bin/python3

import sys
import os
import pathlib
import argparse
import fileinput
import csv
import string
import locale
locale.setlocale(locale.LC_ALL, '')

def output_path_for_input_path(input_path: pathlib.Path, column_segment_number: int, row_segment_number: int, opts: argparse.Namespace):
	column_segment_letter = string.ascii_uppercase[column_segment_number]
	filename_values = {
		'basename': input_path.stem,
		'row_segment': row_segment_number,
		'column_segment': column_segment_letter,
	}
	filename = opts.output_filename_format.format(**filename_values)
	output_path = (pathlib.Path(filename)).with_suffix(input_path.suffix)

	output_dir = opts.output_directory
	if output_dir is not None:
		output_path = output_dir / output_path.name

	return output_path

def make_permutation(header: list, leading_columns: list):
	"Return a list of indexes in which the indexes of each name from leading_columns in header are at the start of the list, followed by the list of the indexes of items in header that were not in leading_columns."

	indexes = []
	try:
		for col in leading_columns:
			indexes.append(header.index(col))
	except ValueError:
		print('Header row:', header, file=sys.stderr)
		raise
	except TypeError:
		# None is not iterable. No leading columns were specified.
		return list(range(len(header)))
	for i, col in enumerate(header):
		if col in leading_columns:
			pass
		else:
			indexes.append(i)
	return indexes

def get_from_indexes(orig_row, indexes):
	permuted_row = [ orig_row[i] for i in indexes ]
	return permuted_row

def column_segment_permutations(orig_header: list, opts: argparse.Namespace):
	leading_columns = opts.common_columns
	all_indexes = make_permutation(orig_header, leading_columns)
	if opts.columns_per_file == 0:
		# We're not segmenting, so return the all permutation.
		yield all_indexes
	else:
		num_leading_columns = len(leading_columns) if leading_columns else 0
		num_trailing_columns = opts.columns_per_file - num_leading_columns
		leading_indexes = all_indexes[:num_leading_columns]
		trailing_offset = num_leading_columns
		trailing_indexes = all_indexes[trailing_offset:trailing_offset + num_trailing_columns]
		while trailing_indexes:
			yield leading_indexes + trailing_indexes
			trailing_offset += num_trailing_columns
			trailing_indexes = all_indexes[trailing_offset:trailing_offset + num_trailing_columns]

def apply_renames(orig_header: list, renames: dict):
	revised_header = list(orig_header)
	for old_name, new_name in renames.items():
		try:
			idx = orig_header.index(old_name)
		except ValueError:
			pass
		else:
			revised_header[idx] = new_name
	return revised_header

def segment(input_path: pathlib.Path, opts: argparse.Namespace):
	rows_per_file = opts.rows_per_file
	rows_so_far = 0

	reader = csv.reader(open(input_path, 'r'))
	orig_header = next(reader)
	permutations = list(column_segment_permutations(orig_header, opts))

	def open_files(row_segment_number):
		out_files = []
		writers = []

		for column_segment_number, indexes in enumerate(permutations):
			output_path = output_path_for_input_path(input_path, column_segment_number, row_segment_number, opts)
			print('Writing up to {:n} rows to {}'.format(rows_per_file, output_path))
			output_file = open(output_path, 'w')
			writer = csv.writer(output_file)

			out_files.append(output_file)
			writers.append(writer)

			subh = get_from_indexes(orig_header, indexes)
			subh = apply_renames(subh, opts.column_renames)
			writer.writerow(subh)

		return out_files, writers

	row_segment_number = 1
	out_files, writers = open_files(row_segment_number)

	for row in reader:
		if rows_per_file != 0 and rows_so_far > 0 and rows_so_far % rows_per_file == 0:
			print('Wrote {:n} rows'.format(rows_so_far))
			for f in out_files: f.close()

			row_segment_number += 1
			out_files, writers = open_files(row_segment_number)

		for column_segment_number, indexes in enumerate(permutations):
			w = writers[column_segment_number]
			segment = get_from_indexes(row, indexes)
			w.writerow(segment)

		rows_so_far += 1
	else:
		print('Wrote a total of {:n} rows'.format(rows_so_far))

def parse_pair(pair_str):
	# TODO: Use csv.reader here
	old_name, new_name = pair_str.split(',')
	return (old_name, new_name)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--no-header', action='store_false', dest='include_header', default=True, help="Input files do not have header rows, so neither will output files. Default is to assume input files have header rows and reproduce each input file's header row to all segments of it.")
	parser.add_argument('-k', '--common-columns', action='append', help='Columns to keep in every file. These columns will be moved to the start of the output.')
	parser.add_argument('--rename-column', type=parse_pair, action='append', dest='column_name_pairs', help='Value is a comma-separated pair of column names. Each former name of a column from the input is changed to the latter in the output.')
	parser.add_argument('-m', '--columns-per-file', '--max-columns', type=int, default=0, help='Split the input into segments of this many columns each. This number includes any --common-columns. Can be combined with --rows-per-file.')
	parser.add_argument('-n', '--rows-per-file', type=int, default=0, help='Split the input into segments of this many rows each.')
	parser.add_argument('-o', '--output-directory', default=None, type=pathlib.Path, help='Directory in which output files are created. Defaults to the same directory as each input file.')
	parser.add_argument('--output-filename-format', default='{basename}-pt{row_segment:04}-{column_segment}', help='Format for the names under which output segment files will be created. Row segments are numbers starting from 1. Column segments are letters starting from A.')
	parser.add_argument('input_paths', type=pathlib.Path, nargs='+', help='CSV files to read. Each file gets split separately; all segments of one input file can be re-joined to reproduce that file.')
	opts = parser.parse_args()

	column_renames = {}
	for old_name, new_name in opts.column_name_pairs:
		column_renames[old_name] = new_name
	opts.column_renames = column_renames

	for input_path in opts.input_paths:
		segment(input_path, opts)

if __name__ == "__main__":
	main()
