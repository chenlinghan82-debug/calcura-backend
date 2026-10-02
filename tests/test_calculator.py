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
        ("2^3", 8),
        ("2^3^2", 512),
        ("-2^2", -4),
        ("50%", 0.5),
        ("200*10%", 20),
        ("5!", 120),
        ("sqrt(16)", 4),
        ("abs(-3.5)", 3.5),
        ("sin(30)", 0.5),
        ("cos(60)", 0.5),
        ("tan(45)", 1),
        ("ln(1)", 0),
        ("log(100)", 2),
        ("log(1000)", 3),
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
        "sqrt(-1)",
        "1.5!",
        "2^10000",
        "ln(0)",
        "log(-2)",
        "tan(90)",
    ],
)
def test_invalid_expressions(expression: str) -> None:
    with pytest.raises(CalculationError):
        calculate_expression(expression)


def test_no_python_code_execution() -> None:
    with pytest.raises(CalculationError):
        calculate_expression("__import__('os').system('whoami')")


def test_previous_answer_and_explanation_steps() -> None:
    from app.services.calculator import explain_expression

    value, steps = explain_expression("(2+3)*4")
    assert value == 20
    assert "2 + 3 = 5" in steps
    assert "5 * 4 = 20" in steps
    assert calculate_expression("Ans*3", ans=4) == 12
