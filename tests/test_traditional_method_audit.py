from scripts.validate_traditional_method_audit import validate


def test_traditional_method_audit_registry_is_complete_and_consistent() -> None:
    assert validate() == []
