import os
import sys
from unittest.mock import MagicMock
from bridgekeeper.mocking import mock_modules, mock_env

def test_mock_modules_list() -> None:
    # Ensure module isn't loaded
    if "dummy_module_1" in sys.modules:
        del sys.modules["dummy_module_1"]
        
    mock_modules(["dummy_module_1"])
    
    assert "dummy_module_1" in sys.modules
    assert isinstance(sys.modules["dummy_module_1"], MagicMock)

def test_mock_modules_dict() -> None:
    if "dummy_module_2" in sys.modules:
        del sys.modules["dummy_module_2"]
    if "dummy_module_3" in sys.modules:
        del sys.modules["dummy_module_3"]
        
    custom_mock = object()
    
    mock_modules({
        "dummy_module_2": None,          # Should be MagicMock
        "dummy_module_3": custom_mock    # Should be custom_mock
    })
    
    assert "dummy_module_2" in sys.modules
    assert isinstance(sys.modules["dummy_module_2"], MagicMock)
    
    assert "dummy_module_3" in sys.modules
    assert sys.modules["dummy_module_3"] is custom_mock

def test_mock_env() -> None:
    if "DUMMY_ENV_VAR" in os.environ:
        del os.environ["DUMMY_ENV_VAR"]
        
    mock_env({"DUMMY_ENV_VAR": "secret_value"})
    
    assert os.environ.get("DUMMY_ENV_VAR") == "secret_value"
    
    # Cleanup
    del os.environ["DUMMY_ENV_VAR"]
