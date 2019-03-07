import importlib
import importlib.util as importutil
import logging
import gc
from pathlib import Path
from typing import Optional, Sequence
from .module import Module


log = logging.getLogger(__name__)


class InvalidModuleException(Exception):
    def __init__(self, name: str, reason: str = None) -> None:
        self.name = name
        message = "could not load module " + name
        if reason is not None:
            message += ": " + reason
        super().__init__(message)


class ModuleLoader:
    def __init__(self, search_paths: Sequence[Path]) -> None:
        self._search_paths = list(map(Path, search_paths))
        self._loaded_modules = dict()

    @property
    def search_paths(self) -> Sequence[Path]:
        return self._search_paths

    def find_module(self, name: str) -> Optional[Path]:
        init = Path(name) / '__init__.py'
        name = name + '.py'
        for path_dir in self.search_paths:
            path = path_dir / name
            initpath = path_dir / init
            if path.exists():
                return path
            elif initpath.exists():
                return initpath
        return None

    def load_module(self, name: str) -> Optional[Module]:
        """
        Searches for a module with the given name, and attempts to load it.

        If the module is already loaded then it is returned.
        """
        importlib.invalidate_caches()
        if name in self._loaded_modules:
            return self._loaded_modules[name]

        path = self.find_module(name)
        if path is None:
            raise InvalidModuleException(name, "module not found")
        if str(path).endswith('.py'):
            module_name = str(path)[:-3].replace('/', '.')
        log.debug("Loading module %s from path %s", name, path)
        spec = importutil.spec_from_file_location(module_name, path)
        module = importutil.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as ex:
            log.exception("Could not execute module")
            raise InvalidModuleException(name, str(ex))
        if not hasattr(module, 'ModuleClass'):
            raise InvalidModuleException(name, 'ModuleClass type must be defined by this module')
        elif not issubclass(module.ModuleClass, Module):
            raise InvalidModuleException(name, 'ModuleClass type must be an instance of ' \
                                               'omnibot.module.Module')
        self._loaded_modules[name] = module.ModuleClass
        log.info("Loaded module %s", name)
        return self._loaded_modules[name]

    def unload_module(self, name: str):
        """
        Unloads a module with the given name, if it has been added by this loader.
        """
        self._loaded_modules.pop(name, None)
        log.debug("Running garbage collector")
        # collect generation 0 objects, including the module
        gc.collect(0)

