from txtgen.constants import TokenType, Function
from txtgen.tokenizer import (
    Token,
    extract_integer,
    extract_literal,
    extract_string,
    tokenize,
    validate_alpha,
)

from typing import Any, List

import pytest


def test_token_initialize_stores_type_and_value():
    t = Token(TokenType.ParenClose, "hello")
    assert t.type == TokenType.ParenClose
    assert t._value == "hello"

    t = Token(TokenType.Function, None)
    assert t._value is None


@pytest.mark.parametrize(
    "token_type,token_value,expected_property_value",
    [(TokenType.ParenClose, "hello", "hello"), (TokenType.ParenClose, None, ")")],
)
def test_token_value_returns_correct_values(
    token_type: TokenType, token_value: Any, expected_property_value: Any
) -> None:

    t = Token(token_type, token_value)
    assert expected_property_value == t.value


@pytest.mark.parametrize(
    "token_type,token_value,expected_serialized",
    [
        (TokenType.ParenClose, None, "<ParenClose value=')'>"),
        (TokenType.ParenClose, "asdf", "<ParenClose value='asdf'>"),
    ],
)
def test_token_serialization(
    token_type: TokenType, token_value: Any, expected_serialized: str
):
    t = Token(token_type, token_value)
    serialized = str(t)

    assert expected_serialized == serialized == t.__repr__()


@pytest.mark.parametrize(
    "in_str,expected",
    [
        ("asdf", True),
        ("d", True),
        ("", False),
        ("_", True),
        (".", True),
        ("6", False),
        ("é", True),
        ("%", False),
    ],
)
def test_validate_alpha(in_str: str, expected: bool):
    assert expected == validate_alpha(in_str)


@pytest.mark.parametrize(
    "in_str,expected_head,expected_tail",
    [
        ("hello world", "hello", list(" world")),
        ("hello_world there", "hello_world", list(" there")),
        ("hello_world", "hello_world", []),
    ],
)
def test_extract_string(in_str: str, expected_head: str, expected_tail: str):
    head, tail = extract_string(in_str)
    assert expected_head == head
    assert expected_tail == tail


@pytest.mark.parametrize(
    "in_str,expected_head,expected_tail",
    [
        ("145hello world", "145", list("hello world")),
        ("14.38hello world", "14", list(".38hello world")),
    ],
)
def test_extract_integer(in_str: str, expected_head: str, expected_tail: str) -> None:
    head, tail = extract_integer(in_str)
    assert expected_head == head
    assert expected_tail == tail


@pytest.mark.parametrize(
    "in_str,expected_head,expected_tail",
    [
        ('hello world" hello hello', "hello world", list(" hello hello")),
        ("hello world", "hello world", []),
    ],
)
def test_extract_literal(in_str: str, expected_head: str, expected_tail: str):
    head, tail = extract_literal(in_str)
    assert expected_head == head
    assert expected_tail == tail


@pytest.mark.parametrize(
    "in_str,expected_tokens",
    [
        (
            "()[]<>",
            [
                Token(TokenType.ParenOpen),
                Token(TokenType.ParenClose),
                Token(TokenType.BracketOpen),
                Token(TokenType.BracketClose),
                Token(TokenType.AngleOpen),
                Token(TokenType.AngleClose),
            ],
        ),
        (
            "(=)",
            [
                Token(TokenType.ParenOpen),
                Token(TokenType.Equal),
                Token(TokenType.ParenClose),
            ],
        ),
        ("( (   (,  , , , , (", [Token(TokenType.ParenOpen)] * 4),
        (
            '$hello.world_s "my man"',
            [
                Token(TokenType.Placeholder, "hello.world_s"),
                Token(TokenType.Literal, "my man"),
            ],
        ),
        (
            "grammar entity ( macro",
            [
                Token(TokenType.Grammar),
                Token(TokenType.Entity),
                Token(TokenType.ParenOpen),
                Token(TokenType.Macro),
            ],
        ),
        (
            "(any if hello)",
            [
                Token(TokenType.ParenOpen),
                Token(TokenType.Function, Function.Any),
                Token(TokenType.Function, Function.If),
                Token(TokenType.Symbol, "hello"),
                Token(TokenType.ParenClose),
            ],
        ),
        (
            "(145)",
            [
                Token(TokenType.ParenOpen),
                Token(TokenType.Integer, 145),
                Token(TokenType.ParenClose),
            ],
        ),
    ],
)
def test_tokenize_valid_tokens(in_str: str, expected_tokens: List[Token]):
    tokens = list(tokenize(in_str))
    assert expected_tokens == tokens


def test_tokenize_raises_syntax_error():
    tokens = []

    with pytest.raises(SyntaxError):
        for itm in tokenize('(entity asdf "hello" % something)'):
            tokens.append(itm)

    expected_tokens = [
        Token(TokenType.ParenOpen),
        Token(TokenType.Entity),
        Token(TokenType.Symbol, "asdf"),
        Token(TokenType.Literal, "hello"),
    ]

    assert expected_tokens == tokens
