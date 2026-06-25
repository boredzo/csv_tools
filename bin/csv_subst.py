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

# Copied from csv_order
class SortColumn:
	def __init__(self, name, column_idx, reverse=False, value_type=str):
		self.name = name
		self.column_index = column_idx # New since csv_order
		self.reverse = reverse
		self.value_type = value_type
		assert callable(self.value_type)
	def parse_value(self, value_str):
		value = self.value_type(value_str)
		if self.reverse:
			value = ReversedComparable(value)
		return value

types_by_name = {
	'str': str,
	'int': int,
	'float': float,
}
class Evaluator:
	def __init__(self, comparand):
		self.comparand = comparand

	def __call__(self, value):
		raise ValueError("{} not implemented".format(self.operator))

class EvaluatorEQ(Evaluator):
	def __call__(self, value):
		return self.comparand == value
class EvaluatorNE(Evaluator):
	def __call__(self, value):
		return self.comparand != value
# The negative of an operator is equivalent to NOT (A op B). So, for example, NOT (A = B) is (A ≠ B).
EvaluatorEQ.negative = EvaluatorNE
EvaluatorNE.negative = EvaluatorEQ
# The inverse of an operator is the equivalent to exchanging the operands. For example, INV (A = B) is (B = A).
# Equality is its own inverse, as is inequality. Where inversion becomes important is in the relational operators below.
EvaluatorEQ.inverse = EvaluatorEQ
EvaluatorNE.inverse = EvaluatorNE

class EvaluatorLT(Evaluator):
	def __call__(self, value):
		return self.comparand < value
class EvaluatorGT(Evaluator):
	def __call__(self, value):
		return self.comparand > value
class EvaluatorLE(Evaluator):
	def __call__(self, value):
		return self.comparand <= value
class EvaluatorGE(Evaluator):
	def __call__(self, value):
		return self.comparand >= value
EvaluatorLT.negative = EvaluatorGE
EvaluatorGT.negative = EvaluatorLE
EvaluatorLE.negative = EvaluatorGT
EvaluatorGE.negative = EvaluatorLT
EvaluatorLT.inverse = EvaluatorGT
EvaluatorGT.inverse = EvaluatorLT
EvaluatorLE.inverse = EvaluatorGE
EvaluatorGE.inverse = EvaluatorLE

operator_classes = {
	'=': EvaluatorEQ,
	'≠': EvaluatorNE,
	'<': EvaluatorLT,
	'>': EvaluatorGT,
	'≤': EvaluatorLE,
	'≥': EvaluatorGE,
}
for k, v in operator_classes.items():
	v.operator = k
operator_classes['=='] = operator_classes['=']
operator_classes['!='] = operator_classes['≠']
operator_classes['<>'] = operator_classes['≠']
operator_classes['<='] = operator_classes['≤']
operator_classes['>='] = operator_classes['≥']

# Shell-friendly synonyms.
operator_classes['EQ'] = operator_classes['=']
operator_classes['NE'] = operator_classes['≠']
operator_classes['LT'] = operator_classes['<']
operator_classes['GT'] = operator_classes['>']
operator_classes['LE'] = operator_classes['≤']
operator_classes['GE'] = operator_classes['≥']

class Criterion:
	def __init__(self, column: SortColumn, evaluator: Evaluator):
		self.column = column
		self.evaluator = evaluator
	def evaluate(self, row):
		value = row[self.column.column_index]
#		print('C{}\tO{}\tV{}\tR{}'.format(self.evaluator.comparand, self.evaluator.operator, value, 'TRUE' if self.evaluator(value) else 'FALSE'))
		return self.evaluator(value)

class AlwaysTrue(Criterion):
	def __init__(self):
		pass
	def evaluate(self, row):
		return True

class Substitution:
	def __init__(self, criterion, subst_value):
		self.criterion = criterion
		self.subst_value = subst_value
	def filter_row(self, orig_row):
		if self.criterion.evaluate(orig_row):
			altered_row = list(orig_row)
			altered_row[self.criterion.column.column_index] = self.subst_value
#			print('Criterion passed, so changing column {:n} to {!r}'.format(self.criterion.column.column_index, self.subst_value))
			return altered_row
		return orig_row

def substitute_values_in_rows(reader: csv.reader, orig_header: list, substitutions: list, writer: csv.writer, opts: argparse.Namespace):
	row_count = 0

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

#	print('Applying {:n} substitutions', len(substitutions))
	writer.writerow(orig_header if not columns_of_interest else get_from_indexes(orig_header, indexes))
	for orig_row in reader:
		altered_row = orig_row
		for this_subst in substitutions:
			altered_row = this_subst.filter_row(altered_row)
		else:
			writer.writerow(altered_row if not columns_of_interest else get_from_indexes(altered_row, indexes))
			row_count += 1

	return row_count

def parsePathOrStdio(path_str: str):
	if path_str == '-':
		return None
	else:
		return pathlib.Path(path_str)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--input-encoding', action='store', default='utf-8', help='Encoding to use for decoding the input file.')
	parser.add_argument('--only-nonempty', '--only-non-empty', action='store_true', default=False, help="Select only rows for which any non-excluded column contains data.")
	parser.add_argument('--only-columns', default=None, help="Comma-separated list of columns to include in the output. Defaults to all columns.")
	parser.add_argument('input_path', type=parsePathOrStdio, help="Path to a file containing CSV data to select from.")
	parser.add_argument('terms', nargs='*', help="Algebraic expressions defining the substitutions. A single expression consists of COLUMN OPERATOR COMPARAND SUBSTITUTION. COLUMN must be the name of one of the columns in the file; OPERATOR must be =, ≠, <, >, ≤, or ≥; COMPARAND is a single fixed value to compare to. An additional word in parentheses between the OPERATOR and COMPARAND indicates the type to interpret all values for that column (including the comparand) as; for example, “total_sold ≤ (int) 4000”. Supported types include str (default), int, and float. For any row where the expression is true, that column is changed to the SUBSTITUTION.")
	opts = parser.parse_args()

	writer = csv.writer(sys.stdout)

	def process(path, flob):
		reader = csv.reader(flob)
		header = next(reader)

		substitutions = []
		terms = opts.terms
		if terms:
			terms_iter = iter(terms)
			while True:
				try:
					column_name = next(terms_iter)
				except StopIteration:
					break
				try:
					column_idx = header.index(column_name)
				except ValueError:
					sys.exit('{}\tColumn {!r} not found among columns: {!r}'.format(path, column_name, header))

				try:
					operator = next(terms_iter)
				except StopIteration:
					sys.exit('Expected operator after column {!r}'.format(column_name))
				try:
					evaluator_class = operator_classes[operator]
				except KeyError:
					sys.exit('Operator {} not recognized'.format(repr(operator)))
				else:
					# The input syntax is (value_column operator comparand), but the criteria are evaluated as (comparand !operator value), so we need to invert the operator.
					evaluator_class = evaluator_class.inverse

				try:
					type_or_comparand = next(terms_iter)
				except StopIteration:
					sys.exit('Expected type annotation or comparand for column {!r}'.format(column_name))
				if type_or_comparand.startswith('(') and type_or_comparand.endswith(')'):
					type_name = type_or_comparand[1:-1]
					try:
						comparand = next(terms_iter)
					except StopIteration:
						sys.exit('Expected comparand for column {!r}'.format(column_name))
				else:
					type_name = 'str'
					comparand = type_or_comparand

				try:
					value_type = types_by_name[type_name]
				except KeyError:
					sys.exit('Type {} not recognized'.format(type_name))

				column = SortColumn(column_name, column_idx, value_type=value_type)
				criterion = Criterion(column, evaluator_class(comparand))

				try:
					subst_value = next(terms_iter)
				except StopIteration:
					sys.exit('Expected substitution value column {!r}'.format(column_name))
				this_subst = Substitution(criterion, subst_value)
				substitutions.append(this_subst)

		row_count = substitute_values_in_rows(reader, header, substitutions, writer, opts)
		print('{}\t{:n}'.format(path or '-', row_count), file=sys.stderr)

	path = opts.input_path
	if path:
		with open(path, 'r', encoding=opts.input_encoding) as f:
			process(path, f)
	else:
		process('-', sys.stdin)

if __name__ == "__main__":
	main()
