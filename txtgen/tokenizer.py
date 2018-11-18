from txtgen.constants import Function, TokenType
from typing import Any, Iterator, Tuple


class Token:

    def __init__(self, token_type: TokenType, value: Any = None) -> None:
        self.type = token_type
        self._value = value

    @property
    def value(self) -> str:
        return self._value or self.type.value

    def __str__(self) -> str:
        return f"<{self.type.name} value='{self.value or self.type.value}'>"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Token):
            return NotImplemented  # pragma: nocover

        return other.value == self.value and other.type == self.type


def validate_alpha(char: str) -> bool:
    return char.isalpha() or char == '_' or char == '.'


def extract_string(input_string: str) -> Tuple[str, str]:
    head, *tail = input_string

    if len(tail) != 0 and validate_alpha(tail[0]):
        body, next_tail = extract_string(tail)
        return ''.join([head, body]), next_tail

    # Alphanum chain has stopped.
    return head, tail


def extract_literal(input_string: str) -> Tuple[str, str]:
    head, *tail = input_string

    if len(tail) >= 1 and tail[0] != '"':
        body, next_tail = extract_literal(tail)
        return ''.join([head, body]), next_tail

    return head, tail[1:]  # Skip closing double-quote


def tokenize(input_string: str) -> Iterator[Token]:
    if not input_string:
        return

    head, *tail = input_string

    if head == ')':
        yield Token(TokenType.ParenClose)

    elif head == '=':
        yield Token(TokenType.Equal)

    elif head == '(':
        yield Token(TokenType.ParenOpen)

    elif head == '<':
        yield Token(TokenType.AngleOpen)

    elif head == '>':
        yield Token(TokenType.AngleClose)

    elif head == '[':
        yield Token(TokenType.BracketOpen)

    elif head == ']':
        yield Token(TokenType.BracketClose)

    elif head.isspace() or head == ',':
        # We want to ignore whitespace & commas in enumerations
        pass

    elif head == '$':
        body, tail = extract_string(tail)
        yield Token(TokenType.Placeholder, body)

    elif validate_alpha(head):
        body, tail = extract_string(input_string)

        if body == 'grammar':
            yield Token(TokenType.Grammar)

        elif body == 'entity':
            yield Token(TokenType.Entity)

        elif body == 'macro':
            yield Token(TokenType.Macro)

        elif body in ['any', 'if']:
            for enum_itm in [Function.Any, Function.If]:
                if body == enum_itm.value:
                    yield Token(TokenType.Function, enum_itm)
                    break

        else:
            yield Token(TokenType.Symbol, body)

    elif head == '"':
        body, tail = extract_literal(tail)
        yield Token(TokenType.Literal, body)

    else:
        raise SyntaxError(f"Unknown Token: '{head}'")

    yield from tokenize(tail)
