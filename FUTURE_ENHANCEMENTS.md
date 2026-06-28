# Future Enhancements

- **Support for OpenAPI Extensions in Flask**: Currently, Bridgekeeper inspects raw view function type annotations for Flask. In the future, we should add support for checking OpenAPI metadata from modern Flask extensions (like `APIFlask`, `Flasgger`, `Flask-RESTX`) which is more robust than pure type hints.
- **Deep validation of models**: Currently, we check if a type hint exists. In the future, we could verify that the type hint is a valid structured model (Pydantic, Dataclass) rather than just a basic primitive type.
