from txtgen.parser import Expression, DescentParser
from txtgen import nodes

import pytest


@pytest.mark.parametrize(
    'text,expected_expression',
    [
        ('"hello world"', nodes.LiteralNode(value='hello world')),
        ('$hello.world', nodes.PlaceholderNode(key='hello.world')),
        ('hello_world', nodes.ReferenceNode(key='hello_world')),
        ('[hello_world]', nodes.OptionalNode(nodes.ReferenceNode('hello_world'))),
        ('(a b c)', nodes.ListNode([nodes.ReferenceNode('a'), nodes.ReferenceNode('b'), nodes.ReferenceNode('c')])),
        ('(any a b)', nodes.AnyNode([nodes.ReferenceNode('a'), nodes.ReferenceNode('b')])),
        ('(if $a=$b (a b))',
            nodes.ConditionNode(
                {'a': 'b'},
                nodes.ListNode([nodes.ReferenceNode('a'), nodes.ReferenceNode('b')]),
                nodes.ReferenceNode('c')
            ))
    ]
)
def test_parser_expression(text: str, expected_expression: Expression) -> None:
    p = DescentParser(text)
    expr = p.expression()
    assert expected_expression == expr
