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

from typing import Iterable, Type

from . import NoDuplicateOrderedDict, export
from .descriptor import Descriptor


def _get_fields(fields: Iterable[str], self: bool = False, cls: bool = False):
    if self:
        yield 'self'
    if cls:
        yield 'cls'

    yield from fields


def _make_init(fields: Iterable[str]):
    code = f'def __init__(' + \
        ', '.join(_get_fields(fields, self=True)) + '):\n'
    for name in fields:
        code += f'\tself.{name} = {name}\n'
    return code


class _StructMeta(type):
    @classmethod
    def __prepare__(*_) -> NoDuplicateOrderedDict:
        return NoDuplicateOrderedDict()

    def __new__(cls: Type[type], clsname: str, bases: tuple[type, ...], clsdict: NoDuplicateOrderedDict) -> type:
        fields = (key for key, val in clsdict.items()
                  if isinstance(val, Descriptor))
        for name in fields:
            clsdict[name].name = name

        if fields:
            init_code = _make_init(fields)
            exec(init_code, globals(), clsdict)

        clsobj = super().__new__(cls, clsname, bases, dict(clsdict))
        setattr(clsobj, '_fields', fields)
        return clsobj


@export
class Struct(metaclass=_StructMeta):
    _fields = []

    def __repr__(self) -> str:
        args = ', '.join(repr(getattr(self, name)) for name in self._fields)
        return self.__class__.__name__ + '(' + args + ')'
