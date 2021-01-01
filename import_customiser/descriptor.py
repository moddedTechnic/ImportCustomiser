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

from typing import Any
from . import export


def _make_setter(cls: type):
    code = 'def __set_(self, instance, value):\n'
    for c in cls.__mro__:
        if 'set_code' in c.__dict__:
            for line in c.set_code():
                code += '\t' + line + '\n'
    return code


class DescriptorMeta(type):
    def __init__(self, clsname: str, bases: tuple[type, ...], clsdict: dict[str, Any]):
        super().__init__(clsname, bases, clsdict)

        if '__set__'  in clsdict:
            raise TypeError('Define the @staticmethod set_code(), not __set__()')

        code = _make_setter(self)
        exec(code, globals(), clsdict)
        setattr(self, '__set__', clsdict['__set__'])


@export
class Descriptor(metaclass=DescriptorMeta):
    def __init__(self, name=None):
        self.name = name

    @staticmethod
    def set_code():
        return [
            'instance.__dict__[self.name] = value'
        ]

    def __delete__(self, instance):
        raise AttributeError('Can\'t delete attributes')
