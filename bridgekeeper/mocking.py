import os
import sys
from typing import Dict, List, Union, Any
from unittest.mock import MagicMock

def mock_modules(modules: Union[List[str], Dict[str, Any]]) -> None:
    """
    Mock heavy modules (like databases, redis, etc.) before importing the app.
    
    :param modules: A list of module strings to mock automatically with MagicMock, 
                    or a dictionary mapping module strings to custom mock objects. 
                    If a dictionary value is None, MagicMock is auto-applied.
    """
    if isinstance(modules, list):
        for mod in modules:
            sys.modules[mod] = MagicMock()
    elif isinstance(modules, dict):
        for mod, mock_obj in modules.items():
            if mock_obj is None:
                sys.modules[mod] = MagicMock()
            else:
                sys.modules[mod] = mock_obj

def mock_env(env_vars: Dict[str, str]) -> None:
    """
    Mock environment variables before importing the app.
    
    :param env_vars: A dictionary of environment variable keys and values.
    """
    for key, value in env_vars.items():
        os.environ[key] = value
