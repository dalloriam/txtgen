from txtgen import nodes
from txtgen.context import Context
from txtgen.optimizer import Optimizer

from typing import Dict, Optional

import pytest


@pytest.mark.parametrize(
    'node,expected',
    [
        (nodes.AnyNode([nodes.LiteralNode('a')]), nodes.LiteralNode('a')),
        (
                nodes.AnyNode([nodes.LiteralNode('a'), nodes.LiteralNode('b')]),
                nodes.AnyNode([nodes.LiteralNode('a'), nodes.LiteralNode('b')])
        )
    ]
)
def test_optimizer_visit_any_node(node: nodes.Node, expected: nodes.Node) -> None:
    o = Optimizer({}, {})
    assert expected == o.visit_any_node(node)


@pytest.mark.parametrize(
    'node,ctx,expected',
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
                Context({'a': 'asdf', 'b': 'asdf asdf'}),
                nodes.LiteralNode('b')
        ),
    ]
)
def test_optimizer_visit_condition_node(node: nodes.ConditionNode, ctx: Context,
                                        expected: nodes.Node) -> None:
    o = Optimizer({}, {}, ctx=ctx)
    assert expected == o.visit_condition_node(node)


@pytest.mark.parametrize(
    'node,entities,macros,expected',
    [
        (
            nodes.MacroNode(
                'some_macro',
                [nodes.ParameterNode('a'), nodes.ParameterNode('b')],
                [nodes.AnyNode([nodes.ReferenceNode('a'), nodes.ReferenceNode('b')])]
            ),
            {},
            {},
            nodes.MacroNode(
                'some_macro',
                [nodes.ParameterNode('a'), nodes.ParameterNode('b')],
                [nodes.AnyNode([nodes.ParameterNode('a'), nodes.ParameterNode('b')])]
            )
        ),
    ]
)
def test_optimizer_visit_macro_node(node: nodes.MacroNode, entities: Dict[str, nodes.EntityNode],
                                    macros: Dict[str, nodes.MacroNode], expected: nodes.Node) -> None:
    o = Optimizer(entities, macros)
    assert expected == o.visit_macro_node(node)


@pytest.mark.parametrize(
    'node,expected',
    [
        (nodes.OptionalNode(None), None),
        (nodes.OptionalNode(nodes.LiteralNode('a')), nodes.OptionalNode(nodes.LiteralNode('a')))
    ]
)
def test_optimizer_visit_optional_node(node: nodes.OptionalNode, expected: nodes.Node) -> None:
    o = Optimizer({}, {})
    assert expected == o.visit_optional_node(node)


def test_optimizer_visit_entity_node_does_nothing_without_macro() -> None:
    o = Optimizer({}, {})
    entity_1 = nodes.EntityNode('some_entity', [nodes.LiteralNode('a'), nodes.LiteralNode('b')])
    entity_2 = nodes.EntityNode('some_entity', [nodes.LiteralNode('a'), nodes.LiteralNode('b')])

    assert entity_2 == o.visit_entity_node(entity_1)


def test_optimizer_visit_entity_node_with_macro() -> None:
    parameters = [nodes.ParameterNode('a'), nodes.ParameterNode('b')]

    o = Optimizer({}, {
        'macro_a': nodes.MacroNode(
            'macro_a',
            parameters,
            parameters[::-1]
        )
    })

    entity_1 = nodes.EntityNode(
        'some_entity',
        [nodes.LiteralNode('a'), nodes.LiteralNode('b')],
        macro=nodes.MacroReferenceNode('macro_a')
    )

    expected_entity = nodes.EntityNode(
        'some_entity',
        [nodes.ParameterNode('b', nodes.LiteralNode('b')), nodes.ParameterNode('a', nodes.LiteralNode('a'))]
    )

    assert expected_entity == o.visit_entity_node(entity_1)


@pytest.mark.parametrize(
    'node,entities,expected,want_err',
    [
        (
            nodes.ReferenceNode('a'),
            {'a': nodes.EntityNode('a', [nodes.LiteralNode('a')])},
            nodes.EntityNode('a', [nodes.LiteralNode('a')]),
            None
        ),
        (
            nodes.ReferenceNode('a'),
            {'b': nodes.EntityNode('a', [nodes.LiteralNode('a')])},
            None,
            NameError
        ),
    ]
)
def test_optimizer_visit_reference_node(node: nodes.ReferenceNode, entities: Dict[str, nodes.EntityNode],
                                        expected: nodes.Node, want_err: Optional[Exception]) -> None:
    o = Optimizer(entities, {})
    if want_err:
        with pytest.raises(want_err):
            o.visit_reference_node(node)
    else:
        assert expected == o.visit_reference_node(node)


@pytest.mark.parametrize(
    'node,expected',
    [
        (nodes.LiteralNode(''), None),
        (nodes.LiteralNode('asdf'), nodes.ListNode([nodes.LiteralNode(' '), nodes.LiteralNode('asdf')])),
        (nodes.LiteralNode(','), nodes.LiteralNode(','))
    ]
)
def test_optimizer_visit_literal_node(node: nodes.LiteralNode, expected: Optional[nodes.Node]) -> None:
    o = Optimizer({}, {})
    assert expected == o.visit_literal_node(node)


@pytest.mark.parametrize(
    'node,ctx,expected',
    [
        (
            nodes.PlaceholderNode('a'),
            Context({'a': ['hello', 'world']}),
            nodes.AnyNode([
                nodes.ListNode([nodes.LiteralNode(' '), nodes.LiteralNode('hello')]),
                nodes.ListNode([nodes.LiteralNode(' '), nodes.LiteralNode('world')])
            ])
        ),
        (
            nodes.PlaceholderNode('a'),
            None,
            nodes.PlaceholderNode('a')
        ),
        (
            nodes.PlaceholderNode('a'),
            Context({'b': 'hello'}),
            nodes.PlaceholderNode('a')
        ),
        (
            nodes.PlaceholderNode('a'),
            Context({'a': 'hello'}),
            nodes.ListNode([nodes.LiteralNode(' '), nodes.LiteralNode('hello')])
        )
    ]
)
def test_optimizer_visit_placeholder_node(node: nodes.PlaceholderNode, ctx: Optional[Context],
                                          expected: nodes.Node) -> None:
    o = Optimizer({}, {}, ctx=ctx)
    assert expected == o.visit_placeholder_node(node)

# TODO: Tests for the walk() method.
