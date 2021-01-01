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

from os.path import exists, join
from sys import meta_path, modules
from sys import path as sys_path
from types import ModuleType

from . import export


class ImportLoader:
    def __init__(self, filename: str, populate_module: function[[ModuleType, str], ModuleType]) -> None:
        self._filename = filename
        self.populate_module = populate_module

    def load_module(self, fullname: str):
        if fullname in modules:
            return modules[fullname]

        mod = modules.setdefault(fullname, ModuleType(fullname))
        mod.__file__ = self._filename
        mod.__loader__ = self
        mod = self.populate_module(mod, self._filename)
        return mod


@export
class ImportBase:
    '''Base class for customising imports

    Usage:
    class Foo(ImportBase):
            extension = 'foo'

            @staticmethod
            def populate_module(module: ModuleType, filename: str) -> ModuleType:
                    # Do something to populate the module
                    return module
    '''

    extension: str = ''

    @classmethod
    def find_module(cls, fullname, path=None):
        for dirname in sys_path:
            filename = join(dirname, fullname + '.' + cls.extension)
            if exists(filename):
                return ImportLoader(filename, cls.populate_module)
        return None

    @classmethod
    def install(cls):
        meta_path.append(cls)

    @staticmethod
    def populate_module(module: ModuleType, filename: str) -> ModuleType:
        return module
