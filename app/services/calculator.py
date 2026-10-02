"""Safe arithmetic expression parser used by the backend.

The parser intentionally supports only numeric literals, parentheses and the
four arithmetic operators. It never evaluates user input as Python code.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, getcontext

getcontext().prec = 28


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
            if char in "+-*/":
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


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.position = 0

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
            right = self._term()
            result = result + right if operator == "+" else result - right
        return result

    def _term(self) -> Decimal:
        result = self._unary()
        while self._match_operator("*", "/"):
            operator = self._previous().value
            right = self._unary()
            if operator == "*":
                result *= right
            else:
                if right == 0:
                    raise CalculationError("Division by zero is not allowed")
                result /= right
        return result

    def _unary(self) -> Decimal:
        if self._match_operator("+", "-"):
            operator = self._previous().value
            value = self._unary()
            return value if operator == "+" else -value
        return self._primary()

    def _primary(self) -> Decimal:
        if self._match("NUMBER"):
            return Decimal(self._previous().value)
        if self._match("LPAREN"):
            value = self._expression()
            if not self._match("RPAREN"):
                raise CalculationError("Missing closing parenthesis")
            return value
        if self._match("RPAREN"):
            raise CalculationError("Unexpected closing parenthesis")
        raise CalculationError("Expected a number or opening parenthesis")

    def _match(self, kind: str) -> bool:
        if self.position < len(self.tokens) and self.tokens[self.position].kind == kind:
            self.position += 1
            return True
        return False

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


def calculate_expression(expression: str) -> float:
    if len(expression) > 200:
        raise CalculationError("Expression is too long")
    tokens = Lexer(expression.strip()).tokenize()
    result = Parser(tokens).parse()
    if not result.is_finite():
        raise CalculationError("Result is not finite")
    numeric_result = float(result)
    return 0.0 if numeric_result == 0 else numeric_result
