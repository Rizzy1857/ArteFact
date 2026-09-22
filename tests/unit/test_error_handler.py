import json

import pytest

from Artefact import error_handler
from Artefact.error_handler import (ConfigurationError, ProcessingError,
    ValidationError, get_error_statistics, handle_error, register_error_hook,
    safe_execute, save_error_statistics, validate_input, with_error_handling)


def test_validation_matrix(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("x")
    directory = tmp_path / "created"
    assert validate_input(file, "file")
    assert validate_input(directory, "directory", create_if_missing=True)
    assert validate_input("sha256", "hash_algorithm")
    assert validate_input("json", "output_format")
    assert validate_input(["jpg", "pdf"], "file_types")
    with pytest.raises(ValidationError):
        validate_input(tmp_path / "missing", "file")
    with pytest.raises(ValidationError):
        validate_input("rot13", "hash_algorithm")
    with pytest.raises(ValidationError):
        validate_input("yaml", "output_format")
    with pytest.raises(ValidationError):
        validate_input("made-up", "file_types")


def test_error_statistics_hooks_and_safe_execution(tmp_path):
    observed = []
    hook = lambda exception, context: observed.append((type(exception).__name__, context))
    register_error_hook(hook)
    handle_error(ConfigurationError("bad config"), "configuration")
    handle_error(ProcessingError("bad input"), "processor")
    assert observed[-1] == ("ProcessingError", "processor")
    stats = get_error_statistics()
    assert stats["ConfigurationError"]["count"] >= 1
    output = tmp_path / "errors.json"
    save_error_statistics(output)
    assert json.loads(output.read_text())["ProcessingError"]["count"] >= 1
    assert safe_execute(lambda: 3) == 3
    assert safe_execute(lambda: 1 / 0, context="division") is None


def test_error_decorator_preserves_and_reraises():
    @with_error_handling("decorated")
    def fail():
        """documentation"""
        raise ValueError("expected")

    assert fail.__name__ == "fail"
    assert fail.__doc__ == "documentation"
    with pytest.raises(ValueError, match="expected"):
        fail()
