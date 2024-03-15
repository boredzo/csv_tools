#!/usr/bin/python3

import sys
import os
import pathlib
import argparse
import fileinput
import csv

def output_path_for_input_path(input_path: pathlib.Path, segment_number: int, opts: argparse.Namespace):
	output_path = (pathlib.Path(str(input_path.with_suffix('')) + '-pt{:04}'.format(segment_number))).with_suffix(input_path.suffix)

	output_dir = opts.output_directory
	if output_dir is not None:
		output_path = output_dir / output_path.name

	return output_path

def segment(input_path: pathlib.Path, opts: argparse.Namespace):
	rows_per_file = opts.rows_per_file
	rows_so_far = 0

	segment_number = 1
	output_path = output_path_for_input_path(input_path, segment_number, opts)
	if rows_so_far == 0:
		print('Writing rows to {}'.format(output_path))
	else:
		print('Writing up to {:n} rows to {}'.format(rows_per_file, output_path))
	output_file = open(output_path, 'w')
	writer = csv.writer(output_file)

	reader = csv.reader(open(input_path, 'r'))
	header = next(reader)
	writer.writerow(header)
	for row in reader:
		if rows_per_file != 0 and rows_so_far == rows_per_file:
			print('Wrote {:n} rows to {}'.format(rows_so_far, output_path))
			output_file.close()

			segment_number += 1
			rows_so_far = 0
			output_path = output_path_for_input_path(input_path, segment_number, opts)
			print('Writing up to {:n} rows to {}'.format(rows_per_file, output_path))
			output_file = open(output_path, 'w')
			writer = csv.writer(output_file)
			writer.writerow(header)

		writer.writerow(row)
		rows_so_far += 1
	else:
		print('Wrote {:n} rows to {}'.format(rows_so_far, output_path))

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--no-header', action='store_false', dest='include_header', default=True, help="Input files do not have header rows, so neither will output files. Default is to assume input files have header rows and reproduce each input file's header row to all segments of it.")
	parser.add_argument('-n', '--rows-per-file', type=int, default=0, help='Split the input into segments of this many rows each.')
	parser.add_argument('-o', '--output-directory', default=None, type=pathlib.Path, help='Directory in which output files are created. Defaults to the same directory as each input file.')
	parser.add_argument('input_paths', type=pathlib.Path, nargs='+', help='CSV files to read. Each file gets split separately; all segments of one input file can be re-joined to reproduce that file.')
	opts = parser.parse_args()
	for input_path in opts.input_paths:
		segment(input_path, opts)
