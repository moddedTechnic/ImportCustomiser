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

from functools import partial
from types import ModuleType
from xml.etree.ElementTree import Element, parse, fromstring

from .descriptor import Descriptor
from .import_utils import ImportBase


def _get_types(root):
	for node in root:
		if node.tag == 'type':
			yield node
		elif node.tag == 'group':
			yield from _get_types(node)


def _dedent(txt):
	txt = '\n'.join(line for line in txt.split('\n') if line.strip())
	try:
		start_pos = next(i for i, j in enumerate(txt) if j.strip())
	except StopIteration:
		start_pos = len(txt) - 1
	return '\n'.join(line[start_pos:] for line in txt.split('\n'))


def _indent(txt, n=1):
	return '\t' * n + txt.replace('\n', '\n' + '\t' * n)


def _escaped(txt: str):
	swaps = {
		'\\': '\\\\',
		'\'': '\\\'',
		'\t': '\\t',
	}
	for old, new in swaps.items():
		txt = txt.replace(old, new)
	return txt


def _get_type(elem: Element):
	elem_type = elem.get('type')
	return '' if elem_type else (': ' + elem_type)


class _Field:
	def __init__(self, field: Element) -> None:
		self.name = field.get('name')
		self.type = _get_type(field)
		self.value = field.text

	def __repr__(self) -> str:
		return f'{self.name}{self.type} = {self.value}'


class _NoDefaultParameter:
	def __bool__(self): return False


NoDefaultParameter = _NoDefaultParameter()


class _Param:
	def __init__(self, param: Element) -> None:
		self.name = param.get('name')
		self.type = _get_type(param)
		self.default = param.get('default', NoDefaultParameter)
		self.default = '' if self.default is NoDefaultParameter else (
			' = ' + self.default)

		self.initialiser = None
		if param.text:
			self.initialiser = _dedent(param.text)

	def __repr__(self) -> str:
		return self.initialiser if self.initialiser else f'self.{self.parameter} = {self.name}'

	def __str__(self) -> str:
		return self.name + self.type + self.default


class _Import:
	def __init__(self, import_: Element) -> None:
		''' New import code from struct_importer.py (factor out?)
		'''
		self.src = import_.get('src')

		self.aliases = []
		for alias in import_.findall('alias'):
			name = alias.get('name')
			as_name = alias.get('as')

			if as_name:
				self.aliases.append(f'{name} as {as_name}')
			else:
				self.aliases.append(name)

	def __repr__(self) -> str:
		if len(self.aliases):
			import_stmt = f'from {self.src} import ' + ', '.join(self.aliases)
		else:
			import_stmt = 'import ' + self.src
		return import_stmt
		

_repr = partial(map, repr)


class _Type:
	def __init__(self, elem: Element) -> None:
		self.name = elem.get('name')
		self.base = elem.get('base', 'Descriptor')

		self.fields = (_Field(field) for field in elem.findall('field'))
		self.params = (_Param(param) for param in elem.findall('param'))
		self.imports = (_Import(imp) for imp in elem.findall('import'))

		self.set_code = elem.find('set')
		if self.set_code:
			self.set_code = _dedent(self.set_code.text)

	def __str__(self) -> str:
		return self.name + '(' + self.base + ')'

	def __repr__(self) -> str:
		code = ''
		code = '\n'.join(map(repr, self.imports))
		code += '\n'
		code += 'class ' + str(self)

		body = ''

		if self.fields:
			body += '\n'.join(_repr(self.fields))
			body += '\n\n'

		if self.params:
			body += ', '.join(x for x in ('def __init__(self, *args',
										  ', '.join(map(str, self.params)), '**kwargs):\n') if x)
			body += _indent('\n'.join(_repr(self.params)))
			body += '\n'
			body += _indent('super().__init__(*args, **kwargs)')
			body += '\n\n'

		if self.set_code:
			body += '@staticmethod\n'
			body += 'def set_code():\n'
			body += _indent('return [')
			body += '\n'
			body += _indent(',\n'.join(
				f'\'{_escaped(line)}\'' for line in self.set_code.split('\n')), 2)
			body += '\n'
			body += _indent(']')
			body += '\n\n'

		code += _indent('\n' + body) if body else ' pass\n\n'
		code += '\n'
		return code


def _import(data: str):
	root = fromstring(data)

	if root.tag == 'types':
		types = (_Type(elem) for elem in _get_types(root))
	elif root.tag == 'type':
		types = (_Type(root),)
	else:
		types = ()

	types = _repr(types)
	code = '\n'.join(types).split('\n')
	code = map(lambda x: x.rstrip('\t'), code)
	code = '\n'.join(line for line in code if line.strip())

	return code


class TypeImporter(ImportBase):
	extension = 'type'

	@staticmethod
	def populate_module(module: ModuleType, filename: str) -> ModuleType:
		with open(filename, 'r') as f:
			data = f.read()
		code = _import(data)
		module.__dict__['Descriptor'] = Descriptor
		exec(code, module.__dict__, module.__dict__)
		return module


TypeImporter.install()
