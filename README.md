# Bridgekeeper
Fail tests if API's do not have input or output models  

**Supports:**
- FastAPI
- Flask

## Usage

You can use Bridgekeeper to validate your API endpoints and ensure they have explicitly typed input and output models. 

### Basic Example

```python
from fastapi import FastAPI
from bridgekeeper import check_models

app = FastAPI()

@app.get("/items/{item_id}")
def read_item(item_id: int) -> dict:
    return {"item_id": item_id}

# Run the checker against your initialized app
results = check_models(app)

# `results` will contain a list of endpoints missing type models
print(results)
```

### Options

`check_models(app, allow_list=None, check_only=None)`

- **`allow_list` (list of strings, optional)**: A list of API paths to ignore (e.g., `["/health", "/metrics"]`). If an endpoint matches a path in the list, it is skipped.
- **`check_only` (literal string, optional)**: If you only want to validate inputs or outputs exclusively, pass `"request"` or `"response"`.
- **`allow_any` (boolean, optional)**: Defaults to `False`. When `False`, explicitly typing a parameter or return type as `typing.Any` is flagged as missing a strict model. Set to `True` if you want to allow `Any` as a valid type hint.

```python
results = check_models(
    app, 
    allow_list=["/health"], 
    check_only="response",  # Will strictly look for missing return types
    allow_any=False         # typing.Any will be rejected
)
```

## Handling Complex Apps (Databases/Secrets)

If your FastAPI or Flask app connects to a database (like Postgres) or external service (like Redis) during initialization, trying to run `bridgekeeper` in a GitHub Action might crash when the app imports, before the tests even run.

Bridgekeeper provides generic mocking utilities to safely bypass these side effects:

```python
from bridgekeeper import mock_modules, mock_env

# 1. Mock critical environment variables
mock_env({
    "DATABASE_URL": "sqlite:///:memory:",
    "SECRET_KEY": "dummy_secret_for_ci"
})

# 2. Mock external services completely BEFORE importing the app
# You can pass a List of module names to auto-apply MagicMock
mock_modules([
    "app.core.db",
    "redis",
    "fastapi_cache",
    "boto3"
])

# Or pass a Dictionary if you want to provide your own mock instances
# mock_modules({"app.core.db": PostgresTestDb})

# 3. Now it is safe to import the app
from myapp.main import app
from bridgekeeper import check_models

results = check_models(app)
```

## Why the name bridgekeeper?  
He guards the [Bridge of Death](https://montypython.fandom.com/wiki/Bridge_of_Death) and requires travelers to answer "questions three" before crossing safely.
