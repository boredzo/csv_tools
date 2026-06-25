#!/usr/bin/python3

import sys
import os
import pathlib
import argparse
import csv
import subprocess
import locale

locale.setlocale(locale.LC_ALL, '')

class TallyCounter:
	"An object that wraps an iterable and counts items yielded by it. Retrieve the count as self.count."
	def __init__(self, iterable):
		self.iterable = iter(iterable)
		self.reset()

	def reset(self):
		self._count = 0
	@property
	def count(self):
		return self._count

	def __iter__(self):
		return self
	def __next__(self):
		# Note: Need to do this first in case it raises StopIteration. If that happens, we shouldn't increment the count.
		item = next(self.iterable)
		self._count += 1
		return item
	def __len__(self):
		return len(self.iterable)
	def __getitem__(self, idx):
		return self.iterable[idx]

class CSVSource:
	def __init__(self, flob, name: str):
		self.name = name
		self.flob = flob
		self.reader = csv.reader(flob)
	def __iter__(self):
		return iter(self.reader)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(help='Use the stream editor sed(1) to process every value in any, some, or every column(s).\nWARNING: Output may be incorrect when multi-line values are involved. Be sure to check the output!')
	parser.add_argument('-n', '--no-automatic-print', dest='automatic_print', action='store_false', default=True, help="Only print row when explicitly ordered to by the sed program. Does not apply to the header row, which is always printed.")
	parser.add_argument('-e', '--execute', action='append', dest='sed_commands', help='One line of sed program to execute. Can contain multiple commands separated with ;, be used multiple times, or both.')
	parser.add_argument('-c', '--column', action='append', dest='columns_to_filter', help='One column to apply sed commands to. By default, filter all columns.')
	parser.add_argument('-C', '--exclude-column', action='append', dest='columns_to_not_filter', help='One column to pass through unmodified instead of filtering. Redundant if -c is also used. Naming a column with both options is an error.')
	# TODO: Add options for dealing with multi-line values.
	# One possibility is an option to promise that the transformation won't change the number of lines; if given, the tool should count the lines in the input value and read that many lines for the output value.
	# Another is an option to run sed once per value, rather than once per column. (This will run sed a great many times.)
	# Another is to write a sentinel value between values. When -n is used, if the sentinel(s) are constant, a hidden '/^(sentinel0|sentinel1|sentinel2…)-([0-9]+)$/p' could be added to the commands list to ensure sentinels continue to be passed through. (The number would be the hash of each input value, to further help prevent collisions between real values and sentinels.)
	parser.add_argument('input_path', type=pathlib.Path, nargs='?', default='-', help="Path to a file containing CSV data to process. If omitted, read from stdin.")
	opts = parser.parse_args()

	if opts.input_path == pathlib.Path('-'):
		source = CSVSource(sys.stdin, '-')
	else:
		source = CSVSource(open(opts.input_path, 'r'), str(opts.input_path))

	counted_source = TallyCounter(source)
	header = next(counted_source)
	counted_source.reset()

	destination = csv.writer(sys.stdout)
	destination.writerow(header)

	if opts.columns_to_not_filter:
		if opts.columns_to_filter:
			ctnf = set(opts.columns_to_not_filter)
			ctf = set(opts.columns_to_filter)
			columns_to_both_filter_and_not_filter = ctnf & ctf
			if columns_to_both_filter_and_not_filter:
				sys.exit('Cannot both filter and not filter these columns: {:r}'.format(list(columns_to_both_filter_and_not_filter)))
		columns_to_filter = [ col for col in header if col not in opts.columns_to_not_filter ]
	else:
		columns_to_filter = opts.columns_to_filter or []

	unknown_columns = [ col for col in columns_to_filter if col not in header ]
	if unknown_columns:
		sys.exit('Unknown columns: {:r}')

	if not columns_to_filter:
		columns_to_filter = header
		column_indexes = list(range(len(columns_to_filter)))
	else:
		column_indexes = []
		for idx, col in enumerate(header):
			if col in columns_to_filter:
				column_indexes.append(idx)

	sed_arguments_0 = [
		'sed',
		'-E', #extended regular expressions
		'-u', #unbuffered I/O
	]
	sed_arguments_1 = [] if opts.automatic_print else [ '-n' ]
	sed_arguments_2 = []
	for cmd in opts.sed_commands:
		sed_arguments_2.append('-e')
		sed_arguments_2.append(cmd)
	sed_arguments = sed_arguments_0 + sed_arguments_1 + sed_arguments_2

	seds = [ subprocess.Popen(sed_arguments, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE) for col in columns_to_filter ]

	for orig_row in counted_source:
		transformed_row = list(orig_row)

		for sed, col, column_idx in zip(seds, columns_to_filter, column_indexes):
			orig_value = orig_row[column_idx]
			if '\n' in orig_value:
				print('WARNING: Multi-line value detected in column {} of row {:n}; output may be corrupt from this point on'.format(col, counted_source.count()), file=sys.stderr)
			sed.stdin.write(orig_value.encode('utf-8') + b'\n')
			sed.stdin.flush()

		for sed, col, column_idx in zip(seds, columns_to_filter, column_indexes):
			new_value = sed.stdout.readline().decode('utf-8')
			new_value = new_value.rstrip('\n')
			transformed_row[column_idx] = new_value

		destination.writerow(transformed_row)

	sys.stdout.flush()
	print('{}\t{:n}'.format(source.name, counted_source.count), file=sys.stderr)
