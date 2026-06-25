#!/usr/bin/python3

import sys
import os
import pathlib
import argparse
import csv
import io
import locale

locale.setlocale(locale.LC_ALL, '')

class Diagnostic:
	def __init__(self, first_row_number: int, message: str):
		self.message = message
		self.range = range(first_row_number, first_row_number+1)
		self.specimens = {}

	def does_row_extend_range(self, row_number: int):
		return row_number == self.range.stop
	def record_as_found_on_row(self, row_number: int, row: list):
		self.range = range(self.range.start, row_number + 1)
		self.specimens[row_number] = row
	def last_row(self):
		row_idx = self.range.stop - 1
		return row_idx, self.specimens[row_idx]

	def __len__(self):
		return len(self.range)

	def __str__(self):
		# NOTE: The row numbers here are intentionally not put through {:n} so they can be passed to various “go to line” commands in text editors and spreadsheets.
		if len(self) > 1:
			range_str = '{}..{}'.format(self.range.start, self.range.stop - 1)
		else:
			range_str = '{}'.format(self.range.start)
		return '{}: {}'.format(range_str, self.message)

	def flush(self, verbose=bool):
		if self.message is None: return
		print(str(self), file=sys.stderr)
		if verbose:
#			self.print_specimens()
			self.flush_verbose()
	def flush_verbose(self):
		pass

	def print_specimens(self, max_specimens=3):
		for i, row_idx in enumerate(self.range):
			if i >= max_specimens: break
			row = self.specimens[row_idx]

class DiagnosticColumnUnderflow(Diagnostic):
	def __init__(self, first_row_number: int, message: str, header: list):
		super().__init__(first_row_number, message)
		self.header = header

	def flush_verbose(self):
		row_idx, row = self.last_row()
		print('Example for row #{}:'.format(row_idx))
		for col_idx, column, value in zip(range(len(row)), self.header, row):
			print('{}\t{}\t{}'.format(col_idx, column, value or '(empty)'))

class DiagnosticColumnOverflow(Diagnostic):
	def __init__(self, first_row_number: int, message: str, header: list):
		super().__init__(first_row_number, message)
		self.header = header

	def flush_verbose(self):
		row_idx, row = self.last_row()
		print('Example for row #{}:'.format(row_idx))
		extension = [ '???' ] * (len(row) - len(self.header))
		for col_idx, column, value in zip(range(len(row)), self.header + extension, row):
			print('{}\t{}\t{}'.format(col_idx, column, value or '(empty)'))

def lint_reader(reader: csv.reader, header: list, verbose: bool):
	global g_row_count

	expected_column_count = len(header)
	if verbose:
		print('Expecting {:n} columns per row'.format(expected_column_count))
	last_diagnostic = None

	for row in reader:
		g_row_count += 1
		this_column_count = len(row)

		if verbose and g_row_count == 1:
			print('First row has {:n} columns'.format(this_column_count))

		if this_column_count < expected_column_count:
			message = 'Column underflow: Expected {:n} columns, got {:n}'.format(expected_column_count, this_column_count)

			if last_diagnostic is None:
				last_diagnostic = DiagnosticColumnUnderflow(g_row_count, message, header)
			elif last_diagnostic.message != message:
				last_diagnostic.flush(verbose=verbose)
				last_diagnostic = Diagnostic(g_row_count, message)

			last_diagnostic.record_as_found_on_row(g_row_count, row)

		elif this_column_count > expected_column_count:
			message = 'Column overflow: Expected {:n} columns, got {:n}'.format(expected_column_count, this_column_count)

			if last_diagnostic is None:
				last_diagnostic = DiagnosticColumnOverflow(g_row_count, message, header)
			elif last_diagnostic.message != message:
				last_diagnostic.flush(verbose=verbose)
				last_diagnostic = Diagnostic(g_row_count, message)

			last_diagnostic.record_as_found_on_row(g_row_count, row)

	if last_diagnostic is not None:
		last_diagnostic.flush()

	return g_row_count

def lint(input_file, input_file_isoLatin1, verbose, quote_character):
	global g_row_count
	try:
		g_row_count = 0

		reader = csv.reader(input_file, quotechar=quote_character)
		header = next(reader)
		row_count = lint_reader(reader, header, verbose)
	except UnicodeDecodeError:
		g_row_count += 1
		print('{}: Failed to decode UTF-8. Failing over to ISO-8859-1.'.format(g_row_count), file=sys.stderr)
		g_row_count = 0

		reader = csv.reader(input_file_isoLatin1, quotechar=quote_character)
		header = next(reader)

		row_count = lint_reader(reader, header, verbose)

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
