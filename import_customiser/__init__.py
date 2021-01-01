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

from collections import OrderedDict
from typing import Callable, Union

__all__ = []


def export(item: Union[type, Callable]) -> Union[type, Callable]:
    '''Export the decorated item
    Adds it to __all__ and globals

    Usage:
    @export
    def foo():
            pass
    '''

    globals()[item.__name__] = item
    __all__.append(item.__name__)
    return item


@export
class NoDuplicateOrderedDict(OrderedDict):
    '''An `OrderedDict` which doesn't allow duplicate keys
    '''

    def __setitem__(self, k, v) -> None:
        if k in self:
            raise NameError(f'{k} is already defined')
        return super().__setitem__(k, v)

from . import lazy_import
from . import descriptor
from . import struct
from . import import_utils
from . import type_importer
from . import struct_importer
