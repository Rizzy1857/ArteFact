# ArteFact Test Suite

This directory contains the automated test suite for ArteFact. The tests are organized into different categories based on their scope and purpose.

## Test Organization

- `unit/`: Unit tests for individual modules and components
  - Tests are isolated and focus on single components
  - Fast execution and high coverage
  - Named with pattern `test_*.py`

- `integration/`: Integration tests for module interactions
  - Tests interaction between multiple components
  - Verifies modules work together correctly
  - May require more complex setup

- `system/`: System-level and end-to-end tests
  - Full system testing with real-world scenarios
  - Comprehensive testing of entire workflows
  - Includes performance and stress testing
  - Run with `--run-system` flag

- `fixtures/`: Test data and fixtures
  - Sample files for testing
  - Mock data and configurations
  - Shared resources

## Running Tests

Basic test execution:

```bash
pytest                    # Run unit and integration tests
pytest --run-system      # Include system tests
pytest --performance     # Include performance tests (performance tests are ye to be added)
pytest -v                # Verbose output
pytest -k "hasher"       # Run tests matching "hasher"
```

### Test Categories

- Unit Tests: `pytest tests/unit`
- Integration Tests: `pytest tests/integration`
- System Tests: `pytest tests/system --run-system`
- Performance Tests: `pytest --performance`

## Adding New Tests

1. Create test file in appropriate directory
2. Use proper markers:

   ```python
   @pytest.mark.unit
   @pytest.mark.integration
   @pytest.mark.system
   @pytest.mark.performance
   ```

3. Follow naming conventions:
   - Files: `test_*.py`
   - Functions: `test_*`
   - Classes: `Test*`

## Test Configuration

See `conftest.py` for shared fixtures and configuration.
See `pytest.ini` for pytest configuration and custom markers.
