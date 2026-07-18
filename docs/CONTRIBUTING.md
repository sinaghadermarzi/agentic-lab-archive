# Contributing

Keep examples safe to run and easy to inspect.

- Prefer synthetic data and local deterministic doubles.
- Put live provider calls behind an explicit environment-variable check.
- Do not commit API keys, `.env` files, private files, or notebook outputs containing secrets.
- Add a test for every framework-neutral behavior.
- Link to primary documentation for framework-specific claims.
- Keep notebooks focused: explain one pattern, show the smallest useful example, and name the trade-off.
