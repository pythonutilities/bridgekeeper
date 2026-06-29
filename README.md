# Bridgekeeper
Fail tests if API's do not have input or output models  

**Supports:**
- FastAPI
- Flask

## Current Scope & Philosophy

*Note: `api-bridgekeeper` is currently designed as an **engine**, not a fully-featured drop-in CLI tool.*

Right now, getting a complex app properly imported in CI is 90% of the work. As such, Bridgekeeper provides the underlying checking engine (`check_models`) which you are expected to embed into your own Python CI scripts (see the GitHub Actions example below) rather than providing a magic `bridgekeeper check` command. 

Future roadmaps include a full CLI, baseline modes, and glob pattern matching for allow-lists, but for now, you adopt the engine and build the car yourself.

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

Bridgekeeper provides generic mocking utilities to safely bypass these side effects. For highly complex apps where you don't want to list out every single dependency, you can use `auto_mock_missing=True` to seamlessly mock any module that isn't installed!

```python
from bridgekeeper import mock_modules, mock_env

# 1. Mock critical environment variables
mock_env({
    "DATABASE_URL": "sqlite:///:memory:",
    "SECRET_KEY": "dummy_secret_for_ci"
})

# 2. Automatically mock ANY missing dependency!
# This is extremely useful if you don't want to install heavy libraries (like SQLAlchemy, boto3, etc.)
# just to run a quick static analysis check.
mock_modules(auto_mock_missing=True)

# You can also explicitly mock specific modules with custom fakes:
# mock_modules({"app.core.db": PostgresTestDb}, auto_mock_missing=True)

# 3. Now it is safe to import the app
from myapp.main import app
from bridgekeeper import check_models

results = check_models(app)
```

### Caveats & Limitations of Auto Mocking

While `auto_mock_missing=True` is powerful, it only safely stubs modules that your app imports but **never actually uses at import time**. Since the mocked modules return `MagicMock` instances, they cannot seamlessly replace core architectural dependencies during class definition or route evaluation. 

For highly complex applications (like those interacting with massive ORMs or custom routing), you may still need to install your true dependency tree (e.g. via `poetry install`) because:

1. **Pydantic/FastAPI**: `check_models` inspects the real Pydantic classes on each route. If you mock them, it can't tell a valid model from a non-model.
2. **Type Validation (e.g. email-validator)**: If a model uses `EmailStr`, it requires the real dependency.
3. **Core App Configurations**: If routing relies on variables like `settings.API_V1_STR` and it becomes a `MagicMock`, it produces invalid route paths (e.g. `<MagicMock>/openapi.json`).
4. **SQLAlchemy Declarative Base**: If your database models subclass a real SQLAlchemy declarative base, a mocked `Base` throws a metaclass conflict at class-definition time. This is unmockable in principle.

**The Solution:** For these complex scenarios, the maintainable choice is to install your full dependency tree (leveraging caching like `poetry` venv caching to speed up CI) and use `mock_env` strictly for bypassing secrets or cloud credentials without hitting the network.

## Why the name bridgekeeper?  
He guards the [Bridge of Death](https://montypython.fandom.com/wiki/Bridge_of_Death) and requires travelers to answer "questions three" before crossing safely.

## GitHub Actions Integration

If you want to enforce that all pull requests have strictly typed endpoints, you can add `api-bridgekeeper` directly to your CI/CD pipeline. 

For complex projects, you may want to install your full dependency tree (e.g., via `poetry`) and mock out network calls or secrets manually before running `check_models`.

Here is an example `.github/workflows/api-schema-check.yml` that only runs when backend files change, installs dependencies, mocks out cloud secrets, and enforces the schema rules:

```yaml
name: API Schema Check

on:
  pull_request:
    branches: [main, develop]
    types: [opened, synchronize, reopened]

jobs:
  api-schema-check:
    name: api-schema-check
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Fetch base branch
        run: git fetch origin ${{ github.base_ref }}

      - name: Check for backend changes
        id: check
        run: |
          CHANGED=$(git diff --name-only origin/${{ github.base_ref }}...HEAD -- 'backend/' | head -1)
          if [ -n "$CHANGED" ]; then
            echo "changed=true" >> $GITHUB_OUTPUT
          else
            echo "changed=false" >> $GITHUB_OUTPUT
            echo "No backend changes — skipping API schema check"
          fi

      - name: Set up Python
        if: steps.check.outputs.changed == 'true'
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        if: steps.check.outputs.changed == 'true'
        working-directory: backend
        run: |
          python -m pip install --upgrade pip setuptools wheel
          python -m venv venv
          source venv/bin/activate
          pip install poetry==1.8.5
          
          poetry config virtualenvs.create false
          poetry install --no-root
          
          # Install bridgekeeper in the action
          pip install api-bridgekeeper
          deactivate

      - name: Run API schema check (api-bridgekeeper)
        if: steps.check.outputs.changed == 'true'
        working-directory: backend
        env:
          PYTHONPATH: ${{ github.workspace }}/backend:${{ github.workspace }}/backend/app
        run: |
          source venv/bin/activate
          python - <<'PY'
          import sys
          from unittest import mock

          # Example: Mock out external secrets managers or cloud calls that happen at import time
          # mock.patch("your_app.secrets.AWSSecretsManager.get_secret", return_value="dummy").start()

          from bridgekeeper import check_models
          from app.main import app

          # Endpoints that currently lack a request/response model. 
          # New endpoints NOT in this list must declare typed models or this check fails.
          ALLOW_LIST = [
              "/api/legacy-endpoint/",
              "/api/health/",
          ]

          results = check_models(app, allow_list=ALLOW_LIST)

          if not results:
              print("✅ All API endpoints declare request/response models "
                    f"(allow-list exempts {len(ALLOW_LIST)} known gaps).")
              sys.exit(0)

          print(f"❌ {len(results)} endpoint(s) are missing typed models:\n")
          for r in results:
              missing = ", ".join(r["missing"])
              print(f"  {r['api']}")
              print(f"      missing: {missing}   ({r['file']})")
          
          print(
              "\nDeclare a Pydantic model for the request body and/or pass "
              "`response_model=` when registering the route. If a gap is "
              "intentional, add the path to ALLOW_LIST in the workflow file."
          )
          sys.exit(1)
          PY
          deactivate
```
