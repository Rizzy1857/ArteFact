from Artefact.health import dependency_health


def test_dependency_health_has_actionable_results():
    result = dependency_health()
    assert isinstance(result["healthy"], bool)
    assert result["python"]
    assert all({"name", "available", "required", "purpose", "fix"} <= set(check)
               for check in result["checks"])
    required = [check for check in result["checks"] if check["required"]]
    assert required and all(check["available"] for check in required)
