
import builtins
from functools import partial
from importlib.machinery import ModuleSpec
from importlib.util import find_spec
from sys import modules
from types import ModuleType
from typing import Any, Mapping, Sequence, Union

original_import = __import__


class _Module(ModuleType):
    pass


class _LazyModule(_Module):
    def __init__(self, spec: ModuleSpec) -> None:
        super().__init__(spec.name)
        self.__file__ = spec.origin
        self.__package__ = spec.parent
        self.__loader__ = spec.loader
        self.__path__ = spec.submodule_search_locations
        self.__spec__ = spec

    def __getattr__(self, name: str) -> Any:
        self.__class__ = _Module
        mod = self.__spec__.loader.load_module(self.__name__)
        self = modules[self.__name__] = mod
        return getattr(self, name)


def imp(
    name:     str,
    globals:  Union[Mapping[str, Any], None] = None,
    locals:   Union[Mapping[str, Any], None] = None,
    fromlist: Sequence[str] = (),
    level:    int = 0,
    *,
    non_lazy: bool = False
) -> _Module:
    base_import = partial(original_import, name, globals,
                          locals, fromlist, level)
    if non_lazy:
        return base_import()

    if level != 0 or fromlist:
        return base_import()

    if name in modules:
        return modules[name]

    spec = find_spec(name)
    if not spec or spec.origin == 'built-in':
        return base_import()

    if not hasattr(spec.loader, 'load_module'):
        return base_import()

    module = modules[name] = _LazyModule(spec)
    return module


builtins.__import__ = imp
