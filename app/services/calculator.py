"""Safe arithmetic expression parser used by the backend.

The parser accepts numbers, parentheses, arithmetic operators, power, percent,
factorial, square root, absolute value, constants, and the previous answer.
It never evaluates user input as Python code.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, getcontext

getcontext().prec = 28

CONSTANTS = {
    "pi": Decimal("3.141592653589793238462643383"),
    "e": Decimal("2.718281828459045235360287471"),
}
FUNCTIONS = {"sqrt", "abs"}


class CalculationError(ValueError):
    """Raised when an expression is syntactically or mathematically invalid."""


@dataclass(frozen=True)
class Token:
    kind: str
    value: str


class Lexer:
    def __init__(self, expression: str) -> None:
        self.expression = expression
        self.index = 0

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while self.index < len(self.expression):
            char = self.expression[self.index]
            if char.isspace():
                self.index += 1
                continue
            if char.isdigit() or char == ".":
                tokens.append(self._read_number())
                continue
            if char.isalpha() or char == "_":
                tokens.append(self._read_name())
                continue
            if char in "+-*/^":
                tokens.append(Token("OP", char))
                self.index += 1
                continue
            if char == "(":
                tokens.append(Token("LPAREN", char))
                self.index += 1
                continue
            if char == ")":
                tokens.append(Token("RPAREN", char))
                self.index += 1
                continue
            if char == "%":
                tokens.append(Token("PERCENT", char))
                self.index += 1
                continue
            if char == "!":
                tokens.append(Token("FACTORIAL", char))
                self.index += 1
                continue
            raise CalculationError(f"Unsupported character: {char}")
        if not tokens:
            raise CalculationError("Expression cannot be empty")
        return tokens

    def _read_number(self) -> Token:
        start = self.index
        dot_count = 0
        digit_count = 0
        while self.index < len(self.expression):
            char = self.expression[self.index]
            if char == ".":
                dot_count += 1
                if dot_count > 1:
                    raise CalculationError("Invalid decimal number")
                self.index += 1
                continue
            if not char.isdigit():
                break
            digit_count += 1
            self.index += 1
        value = self.expression[start : self.index]
        if digit_count == 0:
            raise CalculationError("A decimal point must be followed by digits")
        try:
            Decimal(value)
        except InvalidOperation as exc:
            raise CalculationError("Invalid decimal number") from exc
        return Token("NUMBER", value)

    def _read_name(self) -> Token:
        start = self.index
        while self.index < len(self.expression):
            char = self.expression[self.index]
            if not (char.isalnum() or char == "_"):
                break
            self.index += 1
        return Token("IDENT", self.expression[start : self.index].lower())


def format_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise CalculationError("Result is not finite")
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in {"", "-0"}:
        return "0"
    return text


class Parser:
    def __init__(self, tokens: list[Token], ans: Decimal | None = None) -> None:
        self.tokens = tokens
        self.position = 0
        self.ans = ans
        self.steps: list[str] = []

    def parse(self) -> Decimal:
        result = self._expression()
        if self.position != len(self.tokens):
            token = self.tokens[self.position]
            raise CalculationError(f"Unexpected token: {token.value}")
        return result

    def _expression(self) -> Decimal:
        result = self._term()
        while self._match_operator("+", "-"):
            operator = self._previous().value
            left = result
            right = self._term()
            result = left + right if operator == "+" else left - right
            self.steps.append(
                f"{format_decimal(left)} {operator} {format_decimal(right)} = {format_decimal(result)}"
            )
        return result

    def _term(self) -> Decimal:
        result = self._unary()
        while self._match_operator("*", "/"):
            operator = self._previous().value
            left = result
            right = self._unary()
            if operator == "*":
                result = left * right
            else:
                if right == 0:
                    raise CalculationError("Division by zero is not allowed")
                result = left / right
            self.steps.append(
                f"{format_decimal(left)} {operator} {format_decimal(right)} = {format_decimal(result)}"
            )
        return result

    def _unary(self) -> Decimal:
        if self._match_operator("+", "-"):
            operator = self._previous().value
            value = self._unary()
            return value if operator == "+" else -value
        return self._power()

    def _power(self) -> Decimal:
        result = self._postfix()
        if self._match_operator("^"):
            exponent = self._unary()
            powered = self._apply_power(result, exponent)
            self.steps.append(f"{format_decimal(result)} ^ {format_decimal(exponent)} = {format_decimal(powered)}")
            return powered
        return result

    def _postfix(self) -> Decimal:
        value = self._primary()
        while True:
            if self._match("FACTORIAL"):
                factorial_value = self._factorial(value)
                self.steps.append(f"{format_decimal(value)}! = {format_decimal(factorial_value)}")
                value = factorial_value
                continue
            if self._match("PERCENT"):
                percent_value = value / Decimal(100)
                self.steps.append(f"{format_decimal(value)}% = {format_decimal(percent_value)}")
                value = percent_value
                continue
            return value

    def _primary(self) -> Decimal:
        if self._match("NUMBER"):
            return Decimal(self._previous().value)
        if self._match("IDENT"):
            return self._identifier(self._previous().value)
        if self._match("LPAREN"):
            value = self._expression()
            if not self._match("RPAREN"):
                raise CalculationError("Missing closing parenthesis")
            return value
        if self._match("RPAREN"):
            raise CalculationError("Unexpected closing parenthesis")
        raise CalculationError("Expected a number or opening parenthesis")

    def _identifier(self, name: str) -> Decimal:
        if name == "ans":
            if self._check("LPAREN"):
                raise CalculationError("Ans is a value, not a function")
            if self.ans is None:
                raise CalculationError("Ans is not available yet. Complete a calculation first")
            return self.ans
        if name in CONSTANTS:
            if self._check("LPAREN"):
                raise CalculationError(f"{name} is a constant, not a function")
            return CONSTANTS[name]
        if name in FUNCTIONS:
            if not self._match("LPAREN"):
                raise CalculationError(f"Expected '(' after {name}")
            argument = self._expression()
            if not self._match("RPAREN"):
                raise CalculationError("Missing closing parenthesis")
            if name == "sqrt":
                if argument < 0:
                    raise CalculationError("Square root of a negative number is not allowed")
                result = argument.sqrt()
            else:
                result = abs(argument)
            self.steps.append(f"{name}({format_decimal(argument)}) = {format_decimal(result)}")
            return result
        raise CalculationError(f"Unknown name: {name}")

    def _apply_power(self, base: Decimal, exponent: Decimal) -> Decimal:
        if abs(exponent) > 1000:
            raise CalculationError("Exponent is too large")
        try:
            result = base ** exponent
        except (InvalidOperation, ValueError, ArithmeticError):
            try:
                numeric = float(base) ** float(exponent)
            except (OverflowError, ValueError, ArithmeticError, ZeroDivisionError) as exc:
                raise CalculationError("Power result is not a real number") from exc
            if not math.isfinite(numeric):
                raise CalculationError("Power result is not finite")
            result = Decimal(str(numeric))
        if not result.is_finite():
            raise CalculationError("Power result is not finite")
        return result

    def _factorial(self, value: Decimal) -> Decimal:
        if value != value.to_integral_value() or value < 0 or value > 170:
            raise CalculationError("Factorial is only defined for integers from 0 to 170")
        result = Decimal(1)
        for number in range(2, int(value) + 1):
            result *= number
        return result

    def _match(self, kind: str) -> bool:
        if self.position < len(self.tokens) and self.tokens[self.position].kind == kind:
            self.position += 1
            return True
        return False

    def _check(self, kind: str) -> bool:
        return self.position < len(self.tokens) and self.tokens[self.position].kind == kind

    def _match_operator(self, *operators: str) -> bool:
        if self.position >= len(self.tokens):
            return False
        token = self.tokens[self.position]
        if token.kind == "OP" and token.value in operators:
            self.position += 1
            return True
        return False

    def _previous(self) -> Token:
        return self.tokens[self.position - 1]


def explain_expression(expression: str, ans: float | None = None) -> tuple[float, list[str]]:
    if len(expression) > 200:
        raise CalculationError("Expression is too long")
    ans_value = None if ans is None else Decimal(str(ans))
    parser = Parser(Lexer(expression.strip()).tokenize(), ans_value)
    result = parser.parse()
    if not result.is_finite():
        raise CalculationError("Result is not finite")
    numeric_result = float(result)
    if not math.isfinite(numeric_result):
        raise CalculationError("Result is not finite")
    normalized = 0.0 if numeric_result == 0 else numeric_result
    return normalized, parser.steps


def calculate_expression(expression: str, ans: float | None = None) -> float:
    value, _steps = explain_expression(expression, ans)
    return value
