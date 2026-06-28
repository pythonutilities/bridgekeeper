import os
import sys
from typing import Dict, List, Union, Any, Optional
from unittest.mock import MagicMock
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec

class _MockLoader(Loader):
    def __init__(self, mock_obj=None):
        self.mock_obj = mock_obj

    def create_module(self, spec):
        if self.mock_obj is not None:
            return self.mock_obj
        m = MagicMock()
        m.__path__ = []
        m.__spec__ = None
        m.__version__ = "1.0.0"
        return m
        
    def exec_module(self, module):
        pass

class _MockFinder(MetaPathFinder):
    def __init__(self, prefixes: List[str], custom_mocks: Dict[str, Any]):
        self.prefixes = prefixes
        self.custom_mocks = custom_mocks
        
    def find_spec(self, fullname, path, target=None):
        if fullname in self.custom_mocks:
            return ModuleSpec(fullname, _MockLoader(self.custom_mocks[fullname]))
            
        for prefix in self.prefixes:
            if fullname == prefix or fullname.startswith(prefix + "."):
                return ModuleSpec(fullname, _MockLoader())
                
        return None

class _FallbackMockFinder(MetaPathFinder):
    """
    A fallback finder that returns a mock for any missing module.
    Because it's appended to the end of sys.meta_path, it only catches
    modules that genuinely failed to load via standard finders.
    """
    def find_spec(self, fullname, path, target=None):
        return ModuleSpec(fullname, _MockLoader())

def mock_modules(modules: Optional[Union[List[str], Dict[str, Any]]] = None, auto_mock_missing: bool = False) -> None:
    """
    Mock heavy modules (like databases, redis, etc.) before importing the app.
    Automatically intercepts submodules (e.g. mocking 'boto3' also mocks 'boto3.client').
    
    :param modules: A list of module strings to mock automatically with MagicMock, 
                    or a dictionary mapping module strings to custom mock objects.
    :param auto_mock_missing: If True, appends a fallback finder that automatically
                              mocks ANY missing module.
    """
    prefixes = []
    custom_mocks = {}
    
    if modules:
        if isinstance(modules, list):
            prefixes = modules
        elif isinstance(modules, dict):
            for k, v in modules.items():
                if v is None:
                    prefixes.append(k)
                else:
                    custom_mocks[k] = v
                    
        sys.meta_path.insert(0, _MockFinder(prefixes, custom_mocks))
        
    if auto_mock_missing:
        sys.meta_path.append(_FallbackMockFinder())

def mock_env(env_vars: Dict[str, str]) -> None:
    """
    Mock environment variables before importing the app.
    
    :param env_vars: A dictionary of environment variable keys and values.
    """
    for key, value in env_vars.items():
        os.environ[key] = value
