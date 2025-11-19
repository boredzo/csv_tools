#!/usr/bin/python3

import sys
import os
import pathlib
import argparse
import csv
import zipfile
import xml.etree.ElementTree as ET
import xml.parsers.expat as expat
import locale

locale.setlocale(locale.LC_ALL, '')

class XSLXSheet:
	def __init__(self, sheet_number: int, name: str):
		self.sheet_number = sheet_number
		self.name = name

	@classmethod
	def iter_from_xslx(self, xslx: zipfile.ZipFile):
		with xslx.open('xl/workbook.xml', 'r') as wbf:
			tree = ET.parse(wbf)
			root = tree.getroot()
			for element in root.iter():
				# Strip off namespace cruft
				chunks = element.tag.rsplit('}', 1)
				name = chunks[-1]
				if name == 'sheet':
					yield self(int(element.attrib['sheetId']), element.attrib['name'])

	def extract_to_csv(self, xslx: zipfile.ZipFile, path: pathlib.Path, subtract_one_for_header=True):
		with open(path, 'w') as csvf:
			csvw = csv.writer(csvf)
			sheet_filename = 'xl/worksheets/sheet{}.xml'.format(self.sheet_number)
			with xslx.open(sheet_filename, 'r') as shf:
				parser = expat.ParserCreate(namespace_separator=' ')
				class ParserState:
					pass
				state = ParserState()
				state.rows = []
				state.row_count = 0
				state.current_row = None
				state.current_element_stack = []
				state.current_element_contents = None
				def StartElementHandler(name: str, attributes: dict):
					name = name.rsplit(' ', 1)[-1]
					if name == 'row':
						state.current_row = []
					elif name == 'c':
						pass
					elif name == 'is':
						pass
					elif name == 't':
						state.current_element_contents = []
					state.current_element_stack.append(name)
				def CharacterDataHandler(value: str):
					if state.current_element_contents is not None:
						state.current_element_contents.append(value)
				def EndElementHandler(name: str):
					name = name.rsplit(' ', 1)[-1]
					if name == 't' and state.current_element_contents is not None:
						state.current_row.append(''.join(state.current_element_contents))
						state.current_element_contents = None
					elif name == 'row':
#						state.rows.append(state.current_row)
						csvw.writerow(state.current_row)
						state.row_count += 1
					state.current_element_stack.pop()
				parser.StartElementHandler = StartElementHandler
				parser.CharacterDataHandler = CharacterDataHandler
				parser.EndElementHandler = EndElementHandler
				parser.buffer_text = True

				parser.ParseFile(shf)
				print('Got {:n} rows'.format(state.row_count - subtract_one_for_header))

def make_path_safe(filename: str):
	return filename.replace('/', '_')

if __name__ == "__main__":
	parser = argparse.ArgumentParser(desc="Convert an Excel .xlsx file to a CSV.")
	parser.add_argument('input_paths', type=pathlib.Path, nargs='*', help="Path to one or more files containing CSV data to count rows of. If omitted, read from stdin.")
	opts = parser.parse_args()

	for xslx_path in opts.input_paths:
		with zipfile.ZipFile(xslx_path) as xslx:
			sheets = list(XSLXSheet.iter_from_xslx(xslx))
			if len(sheets) == 1:
				output_path = xslx_path.stem + '.csv'
				for sheet in sheets:
					sheet.extract_to_csv(xslx, output_path)
			else:
				for sheet in sheets:
					output_path = xslx_path.stem + '-{}-{}.csv'.format(sheet.sheet_number, make_path_safe(sheet.name))
					sheet.extract_to_csv(xslx, output_path)
