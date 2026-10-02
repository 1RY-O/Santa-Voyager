from models import InputValidator


def test_budget_valid():
    ok, val = InputValidator.validate_budget("20")
    assert ok and val == "20.0"
    ok, val = InputValidator.validate_budget("$45.50")
    assert ok and float(val) == 45.50


def test_budget_empty_means_no_limit():
    ok, val = InputValidator.validate_budget("")
    assert ok and val is None
    ok, val = InputValidator.validate_budget(None)
    assert ok and val is None


def test_budget_invalid():
    ok, err = InputValidator.validate_budget("abc")
    assert not ok and "valid number" in err
    ok, err = InputValidator.validate_budget("20000")
    assert not ok and "exceed" in err
    ok, err = InputValidator.validate_budget("0")
    assert not ok and "at least" in err


def test_required_text():
    ok, _ = InputValidator.validate_required_text(("Occasion", "birthday"))
    assert ok
    ok, err = InputValidator.validate_required_text(("Occasion", "   "))
    assert not ok and "required" in err
    ok, err = InputValidator.validate_required_text(("X", "a" * 501))
    assert not ok and "too long" in err


def test_optional_text_and_normalize():
    ok, _ = InputValidator.validate_optional_text(("Dislikes", ""))
    assert ok
    assert InputValidator.normalize_list(" a, ,b,, ") == ["a", "b"]
    assert InputValidator.normalize_list("") == []
