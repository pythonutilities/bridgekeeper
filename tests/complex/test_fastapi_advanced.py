import pytest
from fastapi import FastAPI, APIRouter
from functools import partial
import os

from bridgekeeper.checker import check_models, _get_relative_path
from bridgekeeper.mocking import mock_modules
import inspect

def test_included_router_prefix():
    """
    Tests that bridgekeeper correctly extracts the prefix from an
    _IncludedRouter (or any included router with a prefix in FastAPI).
    """
    app = FastAPI()
    sub_router = APIRouter()
    
    # Missing response annotation on purpose
    @sub_router.get("/my-endpoint")
    def my_nested_endpoint(request_data: str):
        return {"data": request_data}
        
    # Include the router with a prefix
    app.include_router(sub_router, prefix="/api/v1")
    
    results = check_models(app, allow_any=False, check_only="response")
    
    # We should have exactly 1 result, and its api path should have the prefix
    assert len(results) == 1
    assert results[0]["api"] == "/api/v1/my-endpoint"
    assert "response" in results[0]["missing"]


def test_partial_function_file_path():
    """
    Tests that bridgekeeper correctly determines the source file path
    even when the endpoint is wrapped in functools.partial.
    """
    app = FastAPI()
    
    def my_base_endpoint(instance, data: dict):
        return {"status": "ok"}
        
    class FakeInstance:
        pass
        
    instance = FakeInstance()
    # Bind the function via partial
    bound_method = partial(my_base_endpoint, instance)
    
    app.add_api_route("/partial-test", bound_method, methods=["POST"])
    
    results = check_models(app, allow_any=False, check_only="response")
    
    assert len(results) == 1
    assert results[0]["api"] == "/partial-test"
    # It should correctly identify the file, not 'unknown'
    assert "test_fastapi_advanced.py" in results[0]["file"]
    assert results[0]["file"] != "unknown"


def test_auto_mock_integration():
    """
    Tests that auto_mock_missing can be safely used to bypass
    missing heavy dependencies while still letting standard routing logic execute.
    """
    mock_modules(auto_mock_missing=True)
    
    # This should dynamically mock 'non_existent_heavy_library'
    import non_existent_heavy_library  # type: ignore
    
    app = FastAPI()
    
    # We avoid returning non_existent_heavy_library.SomeClass because FastAPI
    # validates return types and rejects MagicMock.
    @app.get("/mock-test")
    def mock_endpoint(req: str) -> str:
        # We can freely use the missing heavy library inside the code!
        client = non_existent_heavy_library.Client()
        return client.do_something(req)
        
    results = check_models(app, allow_any=False, check_only="response")
    
    # Since we provided a valid string return annotation, it shouldn't be flagged
    assert len(results) == 0

