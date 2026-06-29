# Future Enhancements

- **Support for OpenAPI Extensions in Flask**: Currently, Bridgekeeper inspects raw view function type annotations for Flask. In the future, we should add support for checking OpenAPI metadata from modern Flask extensions (like `APIFlask`, `Flasgger`, `Flask-RESTX`) which is more robust than pure type hints.
- **Deep validation of models**: Currently, we check if a type hint exists. In the future, we could verify that the type hint is a valid structured model (Pydantic, Dataclass) rather than just a basic primitive type.

## Bridgekeeper 2.0 Roadmap (Based on early user feedback)

1. **Standalone CLI Entrypoint**: Provide a `bridgekeeper check app.main:app` command line tool that owns the exit reporting and supports `--format text|json|github`. This eliminates the need for users to write custom Python wrappers and `sys.exit` logic.
2. **Baseline / Ratchet Mode**: Introduce a `--baseline` (or config file like `.bridgekeeper.json`) mode. This allows the checker to record current violations and fail *only* on newly introduced routes, rather than failing the build on dozens of existing endpoints on day one.
3. **Allow List Pattern Matching**: Allow exact string paths to be replaced with globs/regex (e.g., `/api/auth/*` or `/api/kb/**`) so allow-lists are easier to maintain.
4. **Structured Result Objects**: Return a proper `CheckResult` object (with `.ok`, `.exit_code`, `.endpoints`) rather than a bare list of dictionaries for easier programmatic integration.
5. **Clear Expectation Settings on Auto Mocking**: As documented in the README, be explicit that `mock_modules(auto_mock_missing=True)` cannot magically mock core architectural dependencies (like SQLAlchemy `Base` classes or strict Pydantic definitions at import time). It's an engine feature, not a complete replacement for a proper `poetry install` environment in CI.
