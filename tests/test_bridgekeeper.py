import pytest
import typing
from typing import Any, List, Dict
from bridgekeeper import check_models
from bridgekeeper.checker import MissingResult

# Mock FastAPI to avoid hard dependency in tests if missing
class MockAPIRoute:
    def __init__(self, path: str, endpoint: typing.Callable[..., Any], response_model: typing.Optional[str] = None):
        self.path = path
        self.endpoint = endpoint
        self.response_model = response_model

class MockFastAPI:
    def __init__(self, routes: List[MockAPIRoute]):
        self.routes = routes

# Mock Flask
class MockRule:
    def __init__(self, rule: str, endpoint: str):
        self.rule = rule
        self.endpoint = endpoint

class MockUrlMap:
    def __init__(self, rules: List[MockRule]):
        self.rules = rules
    def iter_rules(self) -> List[MockRule]:
        return self.rules

class MockFlask:
    def __init__(self, rules: List[MockRule], view_functions: Dict[str, typing.Callable[..., Any]]):
        self.url_map = MockUrlMap(rules)
        self.view_functions = view_functions

# Test functions
def perfect_func(item: str) -> str:
    return item

def missing_return(item: str) -> Any:
    return item

def missing_input(item: Any) -> str:
    return str(item)

def missing_both(item: Any) -> Any:
    return item

# We need to remove the return annotations for missing tests to trigger the logic.
# Python signatures are dynamic, let's redefine without hints.
def missing_return_real(item: str):
    return item

def missing_input_real(item) -> str:
    return item

def missing_both_real(item):
    return item

def test_fastapi_checker() -> None:
    routes = [
        MockAPIRoute("/perfect", perfect_func),
        MockAPIRoute("/missing_return", missing_return_real),
        MockAPIRoute("/missing_input", missing_input_real),
        MockAPIRoute("/missing_both", missing_both_real),
        MockAPIRoute("/with_response_model", missing_return_real, response_model="SomeModel"),
    ]
    app = MockFastAPI(routes)
    
    results = check_models(app)
    
    assert len(results) == 3
    
    assert results[0]['api'] == "/missing_return"
    assert results[0]['missing'] == ["response"]
    
    assert results[1]['api'] == "/missing_input"
    assert results[1]['missing'] == ["request"]
    
    assert results[2]['api'] == "/missing_both"
    assert set(results[2]['missing']) == {"request", "response"}

def test_fastapi_allow_list() -> None:
    routes = [
        MockAPIRoute("/missing_both", missing_both_real),
        MockAPIRoute("/ignored", missing_both_real),
    ]
    app = MockFastAPI(routes)
    
    results = check_models(app, allow_list=["/ignored"])
    assert len(results) == 1
    assert results[0]['api'] == "/missing_both"

def test_fastapi_check_only_request() -> None:
    routes = [
        MockAPIRoute("/perfect", perfect_func),
        MockAPIRoute("/missing_return", missing_return_real),
        MockAPIRoute("/missing_input", missing_input_real),
        MockAPIRoute("/missing_both", missing_both_real),
    ]
    app = MockFastAPI(routes)
    
    results = check_models(app, check_only="request")
    
    # Missing return should be ignored now
    assert len(results) == 2
    
    assert results[0]['api'] == "/missing_input"
    assert results[0]['missing'] == ["request"]
    
    assert results[1]['api'] == "/missing_both"
    assert results[1]['missing'] == ["request"]

def test_fastapi_check_only_response() -> None:
    routes = [
        MockAPIRoute("/perfect", perfect_func),
        MockAPIRoute("/missing_return", missing_return_real),
        MockAPIRoute("/missing_input", missing_input_real),
        MockAPIRoute("/missing_both", missing_both_real),
    ]
    app = MockFastAPI(routes)
    
    results = check_models(app, check_only="response")
    
    # Missing input should be ignored now
    assert len(results) == 2
    
    assert results[0]['api'] == "/missing_return"
    assert results[0]['missing'] == ["response"]
    
    assert results[1]['api'] == "/missing_both"
    assert results[1]['missing'] == ["response"]

def test_flask_checker() -> None:
    rules = [
        MockRule("/perfect", "perfect_func"),
        MockRule("/missing_return", "missing_return_real"),
        MockRule("/static", "static"),
    ]
    view_functions: Dict[str, typing.Callable[..., Any]] = {
        "perfect_func": perfect_func,
        "missing_return_real": missing_return_real,
        "static": lambda: "static"
    }
    app = MockFlask(rules, view_functions)
    
    results = check_models(app)
    
    assert len(results) == 1
    assert results[0]['api'] == "/missing_return"
    assert results[0]['missing'] == ["response"]

def test_allow_any_false_by_default() -> None:
    routes = [
        MockAPIRoute("/missing_any_return", missing_return),
        MockAPIRoute("/missing_any_input", missing_input),
        MockAPIRoute("/missing_any_both", missing_both),
    ]
    app = MockFastAPI(routes)
    
    # allow_any defaults to False, so typing.Any should be flagged as missing
    results = check_models(app)
    
    assert len(results) == 3
    assert results[0]['missing'] == ["response"]
    assert results[1]['missing'] == ["request"]
    assert set(results[2]['missing']) == {"request", "response"}

def test_allow_any_true() -> None:
    routes = [
        MockAPIRoute("/missing_any_return", missing_return),
        MockAPIRoute("/missing_any_input", missing_input),
        MockAPIRoute("/missing_any_both", missing_both),
    ]
    app = MockFastAPI(routes)
    
    # allow_any=True means typing.Any is accepted as a valid model
    results = check_models(app, allow_any=True)
    
    assert len(results) == 0
