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

from importlib.util import spec_from_loader
from sys import path_hooks
from types import ModuleType
from urllib.request import urlopen
from xml.etree.ElementTree import fromstring

from . import export


_allowed_protocols = 'http:', 'https:'

def _url_hook(name: str):
    if not name.startswith(_allowed_protocols):
        raise ImportError('Invalid network protocol')
    data: str = urlopen(name).read().decode('utf-8')
    filenames = set(data.split('\n'))
    return _UrlFinder(name, filenames)

loaders = {}
@export
def register_loader(extension: str):
    def wrapper(cls):
        loaders[extension] = cls
        return cls
    return wrapper


class _UrlFinder:
    def __init__(self, baseuri, filenames) -> None:
        self.baseuri = baseuri
        self.filenames = filenames

    def find_spec(self, modname, target=None):
        for extension, loader in loaders.items():
            if f'{modname}.{extension}' in self.filenames:
                origin = self.baseuri = '/' + modname + '.' + extension
                return spec_from_loader(modname, loader(), origin=origin)


@export
class Loader:
    def create_module(self, target):
        return None

    def get_module_contents(self, module: ModuleType):
        return urlopen(module.__spec__.origin).read()


@register_loader('py')
class PyLoader(Loader):
    def exec_module(self, module: ModuleType):
        code = super().get_module_contents(module)
        compile(code, module.__spec__.origin, 'exec')
        exec(code, module.__dict__)


path_hooks.append(_url_hook)
