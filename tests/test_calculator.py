import pytest

from app.services.calculator import CalculationError, calculate_expression


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("12 + 8", 20),
        ("1 + 2 * 3", 7),
        ("(1 + 2) * 3", 9),
        ("10 / 2 + 7", 12),
        ("8 - 3 * 2", 2),
        ("-5 + 8", 3),
        ("3 * -2", -6),
        ("0.1 + 0.2", 0.3),
        ("--5", 5),
    ],
)
def test_valid_expressions(expression: str, expected: float) -> None:
    assert calculate_expression(expression) == pytest.approx(expected)


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "1 / 0",
        "1 +",
        "(1 + 2",
        "1 + 2)",
        "2..3",
        "2 ** 3",
        "2 + abc",
    ],
)
def test_invalid_expressions(expression: str) -> None:
    with pytest.raises(CalculationError):
        calculate_expression(expression)


def test_no_python_code_execution() -> None:
    with pytest.raises(CalculationError):
        calculate_expression("__import__('os').system('whoami')")
