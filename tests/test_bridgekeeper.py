import pytest
from bridgekeeper import check_models
import typing

# Mock FastAPI to avoid hard dependency in tests if missing
class MockAPIRoute:
    def __init__(self, path, endpoint, response_model=None):
        self.path = path
        self.endpoint = endpoint
        self.response_model = response_model

class MockFastAPI:
    def __init__(self, routes):
        self.routes = routes

# Mock Flask
class MockRule:
    def __init__(self, rule, endpoint):
        self.rule = rule
        self.endpoint = endpoint

class MockUrlMap:
    def __init__(self, rules):
        self.rules = rules
    def iter_rules(self):
        return self.rules

class MockFlask:
    def __init__(self, rules, view_functions):
        self.url_map = MockUrlMap(rules)
        self.view_functions = view_functions

# Test functions
def perfect_func(item: str) -> str:
    return item

def missing_return(item: str):
    return item

def missing_input(item) -> str:
    return item

def missing_both(item):
    return item

def test_fastapi_checker():
    routes = [
        MockAPIRoute("/perfect", perfect_func),
        MockAPIRoute("/missing_return", missing_return),
        MockAPIRoute("/missing_input", missing_input),
        MockAPIRoute("/missing_both", missing_both),
        MockAPIRoute("/with_response_model", missing_return, response_model="SomeModel"),
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

def test_fastapi_allow_list():
    routes = [
        MockAPIRoute("/missing_both", missing_both),
        MockAPIRoute("/ignored", missing_both),
    ]
    app = MockFastAPI(routes)
    
    results = check_models(app, allow_list=["/ignored"])
    assert len(results) == 1
    assert results[0]['api'] == "/missing_both"

def test_flask_checker():
    rules = [
        MockRule("/perfect", "perfect_func"),
        MockRule("/missing_return", "missing_return"),
        MockRule("/static", "static"),
    ]
    view_functions = {
        "perfect_func": perfect_func,
        "missing_return": missing_return,
        "static": lambda: "static"
    }
    app = MockFlask(rules, view_functions)
    
    results = check_models(app)
    
    assert len(results) == 1
    assert results[0]['api'] == "/missing_return"
    assert results[0]['missing'] == ["response"]
