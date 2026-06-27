import inspect
import os
import typing
from typing import Any, List, Dict, Optional, Literal, TypedDict, Callable

class MissingResult(TypedDict):
    api: str
    file: str
    missing: List[str]

def _get_relative_path(func: Callable[..., Any]) -> str:
    try:
        abs_path = inspect.getfile(func)
        return os.path.relpath(abs_path, os.getcwd())
    except (TypeError, ValueError):
        return "unknown"

def _check_missing(func: Callable[..., Any], allow_any: bool) -> List[str]:
    missing: List[str] = []
    
    try:
        # Unwrap function if it's wrapped (common in Flask decorators)
        unwrapped_func = inspect.unwrap(func)
        sig = inspect.signature(unwrapped_func)
    except (ValueError, TypeError):
        return []
        
    # Check input types
    missing_request = False
    for param_name, param in sig.parameters.items():
        if param_name in ('self', 'cls', 'request', 'response'):
            continue
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if param.annotation == inspect.Parameter.empty:
            missing_request = True
            break
        if not allow_any and param.annotation is typing.Any:
            missing_request = True
            break
            
    if missing_request:
        missing.append("request")
        
    # Check return type
    if sig.return_annotation == inspect.Signature.empty:
        missing.append("response")
    elif not allow_any and sig.return_annotation is typing.Any:
        missing.append("response")
        
    return missing

def check_models(
    app: Any,
    allow_list: Optional[List[str]] = None,
    check_only: Optional[Literal["request", "response"]] = None,
    allow_any: bool = False
) -> List[MissingResult]:
    """
    Checks if API routes have input (request) and output (response) type annotations.
    
    :param app: The FastAPI or Flask application instance.
    :param allow_list: A list of API paths to ignore (e.g., ["/health"]).
    :param check_only: If specified, restricts the check to either "request" or "response" only.
    :param allow_any: If False, endpoints using `typing.Any` for models will be flagged as missing.
    :return: List of dictionaries with missing annotations.
    """
    if allow_list is None:
        allow_list = []
        
    results: List[MissingResult] = []
    
    def process_missing(api_path: str, func: Callable[..., Any], explicit_has_response: bool = False) -> None:
        missing = _check_missing(func, allow_any)
        
        if explicit_has_response and 'response' in missing:
            missing.remove('response')
            
        if check_only:
            # Filter the missing list based on check_only
            missing = [m for m in missing if m == check_only]
            
        if missing:
            results.append({
                "api": api_path,
                "file": _get_relative_path(func),
                "missing": missing
            })

    if hasattr(app, 'url_map') and hasattr(app, 'view_functions'):
        for rule in app.url_map.iter_rules():
            api_path = rule.rule
            if api_path in allow_list:
                continue
                
            endpoint = rule.endpoint
            if endpoint == 'static':
                continue
                
            view_func = app.view_functions.get(endpoint)
            if not view_func:
                continue
                
            process_missing(api_path, view_func)
                
    elif hasattr(app, 'routes'):
        for route in getattr(app, 'routes', []):
            if not hasattr(route, 'endpoint'):
                continue
                
            api_path = getattr(route, 'path', '')
            if api_path in allow_list:
                continue
                
            endpoint = getattr(route, 'endpoint')
            
            # FastAPI specific: check if response_model is explicitly set
            has_response_model = getattr(route, 'response_model', None) is not None
            
            process_missing(api_path, endpoint, explicit_has_response=has_response_model)
                
    return results
