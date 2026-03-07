# Test Layout

Use this directory for tests that mirror the design documents.

The bootstrap stub includes:

- `unit/test_app.py` for core app behavior
- `unit/test_config.py` for Hydra config composition
- `unit/test_main.py` for FastMCP server wiring

Run the template tests through normal packaging flow:

```bash
pip install -e . --no-deps
pytest
```

Suggested subdirectories:

- `unit/`
- `integration/`
- `spec/`

Recommended coverage:

- config validation
- policy enforcement
- normalized errors
- per-tool behavior
- logging side effects and audit side effects when applicable
