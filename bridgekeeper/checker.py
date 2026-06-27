import inspect
import os

def _get_relative_path(func):
    try:
        abs_path = inspect.getfile(func)
        return os.path.relpath(abs_path, os.getcwd())
    except (TypeError, ValueError):
        return "unknown"

def _check_missing(func):
    missing = []
    
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
            
    if missing_request:
        missing.append("request")
        
    # Check return type
    if sig.return_annotation == inspect.Signature.empty:
        missing.append("response")
        
    return missing

def check_models(app, allow_list=None):
    """
    Checks if API routes have input (request) and output (response) type annotations.
    
    :param app: The FastAPI or Flask application instance.
    :param allow_list: A list of API paths to ignore (e.g., ["/health"]).
    :return: List of dictionaries with missing annotations.
    """
    if allow_list is None:
        allow_list = []
        
    results = []
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
                
            missing = _check_missing(view_func)
            if missing:
                results.append({
                    "api": api_path,
                    "file": _get_relative_path(view_func),
                    "missing": missing
                })
                
    elif hasattr(app, 'routes'):
        for route in getattr(app, 'routes', []):
            if not hasattr(route, 'endpoint'):
                continue
                
            api_path = getattr(route, 'path', '')
            if api_path in allow_list:
                continue
                
            endpoint = route.endpoint
            missing = _check_missing(endpoint)
            
            # FastAPI specific: check if response_model is explicitly set
            has_response_model = getattr(route, 'response_model', None) is not None
            if has_response_model and 'response' in missing:
                missing.remove('response')
                
            if missing:
                results.append({
                    "api": api_path,
                    "file": _get_relative_path(endpoint),
                    "missing": missing
                })
                
    return results
