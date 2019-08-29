from txtgen.parser import Expression, DescentParser
from txtgen import nodes

from typing import Optional

import pytest


@pytest.mark.parametrize(
    "text,expected_expression",
    [
        ('"hello world"', nodes.LiteralNode(value="hello world")),
        ("$hello.world", nodes.PlaceholderNode(key="hello.world")),
        ("hello_world", nodes.ReferenceNode(key="hello_world")),
        ("[hello_world]", nodes.OptionalNode(nodes.ReferenceNode("hello_world"))),
        (
            "(a b c)",
            nodes.ListNode(
                [
                    nodes.ReferenceNode("a"),
                    nodes.ReferenceNode("b"),
                    nodes.ReferenceNode("c"),
                ]
            ),
        ),
        (
            "(any a b)",
            nodes.AnyNode([nodes.ReferenceNode("a"), nodes.ReferenceNode("b")]),
        ),
        (
            "(if $a=$b a)",
            nodes.ConditionNode(
                (nodes.PlaceholderNode("a"), nodes.PlaceholderNode("b")),
                nodes.ReferenceNode("a"),
            ),
        ),
        (
            "(if $a=$b (a b) c)",
            nodes.ConditionNode(
                (nodes.PlaceholderNode("a"), nodes.PlaceholderNode("b")),
                nodes.ListNode([nodes.ReferenceNode("a"), nodes.ReferenceNode("b")]),
                nodes.ReferenceNode("c"),
            ),
        ),
        ('(repeat 4 "hello")', nodes.RepeatNode(4, nodes.LiteralNode("hello"))),
    ],
)
def test_parser_expression(text: str, expected_expression: Expression) -> None:
    p = DescentParser(text)
    expr = p.expression()
    assert expected_expression == expr


@pytest.mark.parametrize(
    "text,expected_entity,want_err",
    [
        ("hello $a)", nodes.EntityNode("hello", [nodes.PlaceholderNode("a")]), None),
        (
            'hello $a "b")',
            nodes.EntityNode(
                "hello", [nodes.PlaceholderNode("a"), nodes.LiteralNode("b")]
            ),
            None,
        ),
        ('hello $a "b"', None, SyntaxError),
        ("hello)", nodes.EntityNode("hello", []), None),
        (
            "hello<some_macro> $a)",
            nodes.EntityNode(
                "hello",
                [nodes.PlaceholderNode("a")],
                nodes.MacroReferenceNode("some_macro"),
            ),
            None,
        ),
    ],
)
def test_parser_entity(
    text: str, expected_entity: nodes.EntityNode, want_err: Optional[Exception]
) -> None:
    p = DescentParser(text)
    if want_err is not None:
        with pytest.raises(want_err):
            p.entity()
    else:
        entity = p.entity()
        assert expected_entity == entity


@pytest.mark.parametrize(
    "text,expected_macro,want_err",
    [
        (
            "some_macro (a b) a [b])",
            nodes.MacroNode(
                "some_macro",
                [nodes.ParameterNode("a"), nodes.ParameterNode("b")],
                [
                    nodes.ReferenceNode("a"),
                    nodes.OptionalNode(nodes.ReferenceNode("b")),
                ],
            ),
            None,
        ),
        ("some_macro (ab )", None, SyntaxError),
        ("some_macro a b)", None, SyntaxError),
    ],
)
def test_parser_macro(
    text: str, expected_macro: nodes.MacroNode, want_err: Optional[Exception]
) -> None:
    p = DescentParser(text)
    if want_err is not None:
        with pytest.raises(want_err):
            p.macro()
    else:
        macro = p.macro()
        assert expected_macro == macro


@pytest.mark.parametrize(
    "text,expected_grammar,want_err",
    [
        ("(grammar)", nodes.Grammar({}, {}), None),
        (
            '(grammar (entity a "hello"))',
            nodes.Grammar(
                {"a": nodes.EntityNode("a", [nodes.LiteralNode("hello")])}, {}
            ),
            None,
        ),
        (
            '(grammar (macro some_macro (a b) b a) (entity a "hello"))',
            nodes.Grammar(
                {"a": nodes.EntityNode("a", [nodes.LiteralNode("hello")])},
                {
                    "some_macro": nodes.MacroNode(
                        "some_macro",
                        [nodes.ParameterNode("a"), nodes.ParameterNode("b")],
                        [nodes.ReferenceNode("b"), nodes.ReferenceNode("a")],
                    )
                },
            ),
            None,
        ),
        ("grammar ", None, SyntaxError),
        ("(grammar", None, SyntaxError),
        ("(grammar () ", None, SyntaxError),
    ],
)
def test_parser_grammar(
    text: str, expected_grammar: nodes.Grammar, want_err: Optional[Exception]
) -> None:
    p = DescentParser(text)
    if want_err is not None:
        with pytest.raises(want_err):
            p.grammar()
    else:
        grammar = p.grammar()
        assert expected_grammar == grammar
