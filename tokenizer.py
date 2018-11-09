from typing import Any, Iterator, Tuple


class Token:

    def __init__(self, token_type: str, value: Any) -> None:
        self.type = token_type
        self.value = value

    def __str__(self) -> str:
        return f"<{self.type} value='{self.value}'>"

    def __repr__(self) -> str:
        return str(self)


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
        yield Token('paren_c', ')')

    elif head == '=':
        yield Token('equal', '=')

    elif head == '(':
        yield Token('paren_o', '(')

    elif head == '<':
        yield Token('angle_o', '<')

    elif head == '>':
        yield Token('angle_c', '>')

    elif head == '[':
        yield Token('bracket_o', '[')

    elif head == ']':
        yield Token('bracket_c', ']')

    elif head.isspace() or head == ',':
        # We want to ignore whitespace & commas in enumerations
        pass

    elif head == '$':
        body, tail = extract_string(tail)
        yield Token('placeholder', body)

    elif validate_alpha(head):
        body, tail = extract_string(input_string)

        if body == 'grammar':
            yield Token('grammar', body)

        elif body == 'entity':
            yield Token('entity', body)

        elif body == 'macro':
            yield Token('macro', body)

        elif body in ['any', 'unique', 'if']:
            yield Token('function', body)

        else:
            yield Token('symbol', body)

    elif head == '"':
        body, tail = extract_literal(tail)
        yield Token('literal', body)

    else:
        raise SyntaxError(f"Unknown Token: '{head}'")

    yield from tokenize(tail)
