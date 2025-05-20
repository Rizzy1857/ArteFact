# Test Coverage

ArteFact uses pytest and pytest-cov to ensure all core modules and features are covered by automated tests. Coverage reports are generated on every CI run and uploaded to Codecov.

## How to Check Coverage Locally

```powershell
pytest --cov=artefact --cov-report=term --cov-report=html
```

- The HTML report will be available in the `htmlcov/` directory.
- Aim for 90%+ coverage on all business logic and plugin loading code.

## Coverage Badges

Add a Codecov badge to the README after the first successful upload.
