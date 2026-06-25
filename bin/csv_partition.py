#!/usr/bin/python3

import sys
import os
import pathlib
import argparse
import fileinput
import csv
import string
import itertools
import math
import locale
locale.setlocale(locale.LC_ALL, '')

def factors(n):
	max_factor = int(math.sqrt(n))
	factors = set()
	for divisor in range(2, max_factor + 1):
		if n % divisor == 0:
			factors.add(divisor)
			factors.add(n // divisor)
	return factors

def avg(nums):
	if not nums:
		return 0
	return sum(nums) / len(nums)

def avg_factor(n):
	divs = factors(n)
	mean = int(avg(divs))
	offset = 0
	while mean + offset in divs and mean - offset in divs and mean - offset > 0:
		offset += 1
	if mean + offset not in divs:
		return mean + offset
	if mean - offset not in divs:
		return mean - offset
	return None

def find_stride_length(n):
	return (avg_factor(n) or int(math.sqrt(n))) + int(math.sqrt(n))

def test_factors():
	print(factors(24))

def test_avg_factors():
	print(avg_factor(24))

class RandomRange:
	"A sequence of integers that behaves like a range, but generates numbers in a pseudorandom order rather than linear order."
	def __init__(self, start=0, stop=None, step=1):
		self._pool = list(range(start, stop, step))
		self._num_yielded = 0
		self._num_available = len(self._pool)
		self._stride_length = find_stride_length(self._num_available)
		self._cur_idx = int(math.sqrt(self._num_available))
	def __len__(self):
		return self._num_available
	def __iter__(self):
		return self
	def __next__(self):
		if (self._num_yielded >= self._num_available):
			raise StopIteration
		next_item = self._pool[self._cur_idx]
		self._cur_idx = (self._cur_idx + self._stride_length) % self._num_available
		self._num_yielded += 1
		return next_item

def test_randomrange():
	rr = RandomRange(1, 25+1)
	idxs = list(rr)
	print(len(rr), len(idxs))
	print(idxs, file=sys.stderr)

def column_segment_identifier(column_segment_number: int):
	"Return strings like A, B, C, … Z, AA, AB, AC…."
	hundreds = column_segment_number // (26 * 26) % 26
	tens = column_segment_number // 26 % 26
	units = column_segment_number % 26
	diagnostic_mode = False
	if diagnostic_mode:
		print(hundreds, tens, units)
		alphabet_h = [ '' ] + [ chr(x) for x in range(0x1d586, 0x1d5a0) ]
		alphabet_t = [ '' ] + [ chr(x) for x in range(0x1d5a0, 0x1d5ba) ]
		alphabet_u = string.ascii_uppercase
		alphabet_h = alphabet_t = [ '' ] + list(string.ascii_uppercase)
		alphabet_u = string.ascii_uppercase
	else:
		alphabet_h = alphabet_t = [ '' ] + list(string.ascii_uppercase)
		alphabet_u = string.ascii_uppercase
	return (''
		+ (alphabet_h[hundreds] if hundreds else '')
		+ (alphabet_t[tens] if tens or hundreds else '')
		+ alphabet_u[units]
	)
	
def test_column_segment_identifier(die_on_failure=True):
	def test_one(column_segment_number: int, expected: str):
		sys.stdout.write('{}\te {}\t'.format(column_segment_number, expected))
		sys.stdout.flush()

		try:
			result = column_segment_identifier(column_segment_number)
		except BaseException as e:
			if die_on_failure:
				raise
			else:
				print('{}: {}'.format(type(e).__name__, e), file=sys.stderr)
			result = None

		print('r', result)
		sys.stdout.flush()
		if die_on_failure:
			assert result == expected
		else:
			print('FAIL!' if result != expected else 'PASS')
	test_one(0, 'A')
	test_one(25, 'Z')
	test_one(26, 'AA')
	test_one(26 + 25, 'AZ')
	test_one(26 + 26, 'BA')

def output_path_for_input_path(input_path: pathlib.Path, column_segment_number: int, row_segment_number: int, opts: argparse.Namespace):
	column_segment_letter = column_segment_identifier(column_segment_number)
	filename_values = {
		'basename': input_path.stem,
		'row_segment': row_segment_number,
		'column_segment': column_segment_letter,
	}
	filename = opts.output_filename_format.format(**filename_values)
	# Note: with_suffix breaks when filename has a period in it; pathlib thinks the part after the period is a suffix and replaces it.
	output_path = pathlib.Path(filename + input_path.suffix)

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
	leading_columns = opts.common_columns or []
	all_indexes = make_permutation(orig_header, leading_columns)
	if opts.columns_per_file == 0:
		# We're not segmenting, so return the all permutation.
		yield all_indexes
	else:
		num_leading_columns = len(leading_columns) if leading_columns else 0
		if opts.columns_per_file == len(leading_columns):
			yield all_indexes[:num_leading_columns]
		else:
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
	rows_so_far_this_segment = 0

	if opts.perturb_output_count and rows_per_file > 100:
		perturbations = itertools.cycle(RandomRange(1, 100))
	else:
		perturbations = itertools.repeat(0)

	reader = csv.reader(open(input_path, 'r', encoding=opts.input_encoding))
	orig_header = next(reader)
	permutations = list(column_segment_permutations(orig_header, opts))
	if not permutations:
		sys.exit('No columns to include in output (original column set: {!r})'.format(orig_header))

	def open_files(row_segment_number, rows_this_segment):
		out_files = []
		writers = []

		for column_segment_number, indexes in enumerate(permutations):
			output_path = output_path_for_input_path(input_path, column_segment_number, row_segment_number, opts)
			print('Writing up to {:n} rows to {}'.format(rows_this_segment, output_path))
			output_file = open(output_path, 'w')
			writer = csv.writer(output_file)

			out_files.append(output_file)
			writers.append(writer)

			subh = get_from_indexes(orig_header, indexes)
			subh = apply_renames(subh, opts.column_renames)
			writer.writerow(subh)

		return out_files, writers

	row_segment_number = 1
	max_rows_this_segment = rows_per_file - next(perturbations)
	out_files, writers = open_files(row_segment_number, max_rows_this_segment)

	try:
		for row in reader:
			if max_rows_this_segment != 0 and rows_so_far_this_segment > 0 and rows_so_far_this_segment % max_rows_this_segment == 0:
				print('Wrote {:n} rows'.format(rows_so_far_this_segment))
				for f in out_files: f.close()

				row_segment_number += 1
				rows_so_far_this_segment = 0
				perturb = next(perturbations)
				max_rows_this_segment = rows_per_file - perturb
				out_files, writers = open_files(row_segment_number, max_rows_this_segment)

			for column_segment_number, indexes in enumerate(permutations):
				w = writers[column_segment_number]
				segment = get_from_indexes(row, indexes)
				w.writerow(segment)

			rows_so_far_this_segment += 1
			rows_so_far += 1
	except UnicodeDecodeError:
		print('Encountered a decoding error after {:n} rows'.format(rows_so_far), file=sys.stderr)
		raise
	finally:
		print('Wrote a total of {:n} rows'.format(rows_so_far))

def parse_pair(pair_str):
	# TODO: Use csv.reader here
	old_name, new_name = pair_str.split(',')
	return (old_name, new_name)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--input-encoding', action='store', default='utf-8', help='Encoding to use for decoding the input file.')
	parser.add_argument('--no-header', action='store_false', dest='include_header', default=True, help="Input files do not have header rows, so neither will output files. Default is to assume input files have header rows and reproduce each input file's header row to all segments of it.")
	parser.add_argument('-k', '--common-columns', action='append', help='Columns to keep in every file. These columns will be moved to the start of the output.')
	parser.add_argument('-l', '--rename-column', '--label-column', type=parse_pair, action='append', dest='column_name_pairs', help='Value is a comma-separated pair of column names. Each former name of a column from the input is changed to the latter in the output.')
	parser.add_argument('-m', '--columns-per-file', '--max-columns', type=int, default=0, help='Split the input into segments of this many columns each. This number includes any --common-columns. Can be combined with --rows-per-file.')
	parser.add_argument('-n', '--rows-per-file', type=int, default=0, help='Split the input into segments of this many rows each.')
	parser.add_argument('-o', '--output-directory', default=None, type=pathlib.Path, help='Directory in which output files are created. Defaults to the same directory as each input file.')
	parser.add_argument('--output-filename-format', default='{basename}-pt{row_segment:04}-{column_segment}', help='Format for the names under which output segment files will be created. Row segments are numbers starting from 1. Column segments are letters starting from A.')
	parser.add_argument('--perturb-output-count', default=False, action='store_true', help='If true, remove a small random number of rows from each vertical segment. (The number of rows will remain constant across horizontal segments.) This can be used to distinguish segments after transformations, uploads, etc.')
	parser.add_argument('input_paths', type=pathlib.Path, nargs='+', help='CSV files to read. Each file gets split separately; all segments of one input file can be re-joined to reproduce that file.')
	opts = parser.parse_args()

	if opts.output_directory:
		opts.output_directory.mkdir(exist_ok=True, mode=0o0755)

	column_renames = {}
	if opts.column_name_pairs:
		for old_name, new_name in opts.column_name_pairs:
			column_renames[old_name] = new_name
	opts.column_renames = column_renames

	for input_path in opts.input_paths:
		segment(input_path, opts)

if __name__ == "__main__":
	main()
