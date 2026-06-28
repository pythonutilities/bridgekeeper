import os
import sys
from unittest.mock import MagicMock
from bridgekeeper.mocking import mock_modules, mock_env

def test_mock_modules_list() -> None:
    # Ensure module isn't loaded
    if "dummy_module_1" in sys.modules:
        del sys.modules["dummy_module_1"]
        
    mock_modules(["dummy_module_1"])
    
    import dummy_module_1  # type: ignore
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
    
    import dummy_module_2  # type: ignore
    import dummy_module_3  # type: ignore
    assert "dummy_module_2" in sys.modules
    assert isinstance(sys.modules["dummy_module_2"], MagicMock)
    
    assert "dummy_module_3" in sys.modules
    assert sys.modules["dummy_module_3"] is custom_mock

def test_mock_env() -> None:
    if "DUMMY_ENV_VAR" in os.environ:
        del os.environ["DUMMY_ENV_VAR"]
        
    mock_env({"DUMMY_ENV_VAR": "secret_value"})
    
    assert os.environ.get("DUMMY_ENV_VAR") == "secret_value"
    
def test_auto_mock_missing() -> None:
    # Ensure a truly non-existent module is not there
    non_existent = "some_crazy_non_existent_module_name"
    if non_existent in sys.modules:
        del sys.modules[non_existent]
        
    # Standard import should fail
    try:
        import some_crazy_non_existent_module_name  # type: ignore
        assert False, "Should have raised ImportError"
    except ImportError:
        pass
        
    # Now enable auto_mock_missing
    mock_modules(auto_mock_missing=True)
    
    # Standard import should now succeed and return a MagicMock!
    import some_crazy_non_existent_module_name  # type: ignore
    assert "some_crazy_non_existent_module_name" in sys.modules
    assert isinstance(sys.modules["some_crazy_non_existent_module_name"], MagicMock)
