from txtgen import nodes
from txtgen.constants import PUNCTUATION
from txtgen.context import Context

import pytest


@pytest.mark.parametrize(
    'input_node,expected_output',
    [
        (nodes.LiteralNode('hello'), nodes.ListNode([nodes.LiteralNode(' '), nodes.LiteralNode('hello')])),
        *[(nodes.LiteralNode(x), nodes.LiteralNode(x)) for x in PUNCTUATION]
    ]
)
def test_sub_punctuation(input_node: nodes.LiteralNode, expected_output: nodes.Node) -> None:
    assert nodes.sub_punctuation(input_node) == expected_output


@pytest.mark.parametrize(
    'input_node,input_ctx,expected_node',
    [
        (
                nodes.ConditionNode((nodes.PlaceholderNode("a"), nodes.PlaceholderNode("b")), nodes.LiteralNode("a")),
                Context({}),
                nodes.ConditionNode((nodes.PlaceholderNode("a"), nodes.PlaceholderNode("b")), nodes.LiteralNode("a"))
        ),
        (
                nodes.ConditionNode((nodes.PlaceholderNode("a"), nodes.PlaceholderNode("b")), nodes.LiteralNode("a")),
                Context({'a': 'asdf', 'b': 'asdf'}),
                nodes.LiteralNode('a')
        ),
        (
                nodes.ConditionNode(
                    (nodes.PlaceholderNode("a"), nodes.PlaceholderNode("b")),
                    nodes.LiteralNode("a"),
                    nodes.LiteralNode('b')
                ),
                Context({'a': 'asdf', 'b': 'fdsa'}),
                nodes.LiteralNode('b')
        ),
    ]
)
def test_exec_condition(input_node: nodes.ConditionNode, input_ctx: Context, expected_node: nodes.Node) -> None:
    assert nodes.exec_condition(input_node, input_ctx) == expected_node


def test_grammar_node_eq():
    g1 = nodes.Grammar({}, {})
    g2 = nodes.Grammar({'asdf': nodes.EntityNode('some_entity', [])}, {})
    assert g1 != g2

    g3 = nodes.Grammar(
        {'asdf': nodes.EntityNode('some_other', [])},
        {'some_macro': nodes.MacroNode('some_macro', [], [])}
    )
    assert g2 != g3

    g2.macros['some_macro'] = nodes.MacroNode('some_macro', [], [])

    assert g2 != g3

    g3.entities['asdf'].name = 'some_entity'

    assert g2 == g3


def test_grammar_node_generate():
    grammar = nodes.Grammar(
        {'some_entity': nodes.EntityNode('some_entity', [nodes.LiteralNode("a"), nodes.PlaceholderNode("a")])},
        {}
    )

    assert grammar.generate('some_entity', {'a': 'sdf'}) == 'a sdf'
