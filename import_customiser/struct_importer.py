'''
Copyright 2020 Jonathan Leeming

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

	http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

from types import ModuleType
from xml.etree.ElementTree import Element, parse

from .import_utils import ImportBase

from .struct import Struct


def _xml_to_code(filename):
	doc = parse(filename)

	code += 'import type_importer\n'

	imports = doc.findall('import')
	for import_ in imports:
		src = import_.get('src')

		aliases = []
		for alias in import_.findall('alias'):
			name = alias.get('name')
			as_name = alias.get('as')

			if as_name:
				aliases.append(f'{name} as {as_name}')
			else:
				aliases.append(name)

		if len(aliases):
			import_stmt = f'from {src} import ' + ', '.join(aliases)
		else:
			import_stmt = 'import ' + src
		code += import_stmt + '\n'

	structures = doc.findall('structure')
	if structures:
		for st in structures:
			code += _xml_struct_code(st)
		return code

	fields = doc.findall('field')
	if fields:
		code += _xml_struct_code
		return code

	return None


def _xml_struct_code(st: Element):
	stname = st.get('name')
	code = f'class {stname}(Struct):\n'

	for field in st.findall('field'):
		name = field.get('name')
		dtype = field.get('type')
		kwargs = ', '.join(
			f'{k}={v}' for k, v in field.items() if k not in ('type', 'name'))
		code += f'\t{name} = {dtype}({kwargs})\n'

	str_format = st.find('str')
	if str_format:
		use_class = eval(str_format.get('class', 'False'))

		format_ = str_format.text
		format_ = format_.replace('{', '{{').replace('}', '}}')
		format_ = format_.replace('{' * 4, '{').replace('}' * 4, '}')
		body = f'f\'{format_}\''

		_repr_ = ''
		_repr_ += '\tdef __repr__(self):\n'
		_repr_ += '\t\treturn '

		if use_class:
			_repr_ += f'type(self).__name__ + \'(\' + '
		_repr_ += body
		if use_class:
			_repr_ += ' + \')\'\n'

		code += _repr_

	return code


class StructImporter(ImportBase):
	extension = 'struct'

	@staticmethod
	def populate_module(module: ModuleType, filename: str) -> ModuleType:
		code = _xml_to_code(filename)
		module.__dict__['Struct'] = Struct
		exec(code, module.__dict__, module.__dict__)
		return module


StructImporter.install()
