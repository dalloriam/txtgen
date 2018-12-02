from txtgen import nodes
from txtgen.constants import PUNCTUATION
from txtgen.context import Context

from typing import Optional, Set

from unittest import mock

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
                Context({'a': 'asdf', 'b': 'something'}),
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


@pytest.mark.parametrize(
    'node_a,node_b,should_eq',
    [
        (
            nodes.ConditionNode((nodes.LiteralNode('a'), nodes.LiteralNode('b')), nodes.LiteralNode('c')),
            nodes.ConditionNode((nodes.LiteralNode('a'), nodes.LiteralNode('b')), nodes.LiteralNode('c')),
            True
        ),
        (
            nodes.ConditionNode((nodes.LiteralNode('b'), nodes.LiteralNode('b')), nodes.LiteralNode('c')),
            nodes.ConditionNode((nodes.LiteralNode('a'), nodes.LiteralNode('b')), nodes.LiteralNode('c')),
            False
        ),
        (
            nodes.ConditionNode((nodes.LiteralNode('a'), nodes.LiteralNode('x')), nodes.LiteralNode('c')),
            nodes.ConditionNode((nodes.LiteralNode('a'), nodes.LiteralNode('b')), nodes.LiteralNode('c')),
            False
        ),
        (
            nodes.ConditionNode((nodes.LiteralNode('a'), nodes.LiteralNode('x')), nodes.LiteralNode('c')),
            nodes.ConditionNode((nodes.LiteralNode('a'), nodes.LiteralNode('b')), nodes.LiteralNode('c')),
            False
        ),
        (
            nodes.ConditionNode((nodes.LiteralNode('a'), nodes.LiteralNode('b')), nodes.LiteralNode('a')),
            nodes.ConditionNode((nodes.LiteralNode('a'), nodes.LiteralNode('b')), nodes.LiteralNode('c')),
            False
        ),
        (
            nodes.ConditionNode(
                (nodes.LiteralNode('a'), nodes.LiteralNode('b')),
                nodes.LiteralNode('a'),
                nodes.LiteralNode('c')
            ),
            nodes.ConditionNode((nodes.LiteralNode('a'), nodes.LiteralNode('b')), nodes.LiteralNode('a')),
            False
        ),
        (
                nodes.ConditionNode(
                    (nodes.LiteralNode('a'), nodes.LiteralNode('b')),
                    nodes.LiteralNode('a'),
                    nodes.LiteralNode('c')
                ),
                nodes.ConditionNode(
                    (nodes.LiteralNode('a'), nodes.LiteralNode('b')),
                    nodes.LiteralNode('a'),
                    nodes.LiteralNode('d')
                ),
                False
        ),
        (
                nodes.ConditionNode(
                    (nodes.LiteralNode('a'), nodes.LiteralNode('b')),
                    nodes.LiteralNode('a'),
                    nodes.LiteralNode('c')
                ),
                nodes.ConditionNode(
                    (nodes.LiteralNode('a'), nodes.LiteralNode('b')),
                    nodes.LiteralNode('a'),
                    nodes.LiteralNode('c')
                ),
                True
        ),
    ]
)
def test_condition_node_eq(node_a: nodes.Node, node_b: nodes.Node, should_eq: bool) -> None:
    assert (node_a == node_b) == should_eq


@pytest.mark.parametrize(
    'node,ctx,expected_output,want_err',
    [
        (
            nodes.ConditionNode((nodes.LiteralNode('a'), nodes.LiteralNode('b')), nodes.LiteralNode('a')),
            {},
            '',
            None
        ),
        (
            nodes.ConditionNode(
                (nodes.LiteralNode('a'), nodes.LiteralNode('b')),
                nodes.LiteralNode('a'),
                nodes.LiteralNode('c')
            ),
            {},
            'c',
            None
        ),
        (
            nodes.ConditionNode((nodes.LiteralNode('a'), nodes.LiteralNode('a')), nodes.LiteralNode('a')),
            {},
            'a',
            None
        ),
        (
            nodes.ConditionNode(
                (nodes.PlaceholderNode('a'), nodes.PlaceholderNode('b')),
                nodes.LiteralNode('a'),
                nodes.LiteralNode('b')
            ),
            {'a': 'c', 'b': 'd'},
            'b',
            None
        ),
        (
            nodes.ConditionNode(
                (nodes.PlaceholderNode('a'), nodes.PlaceholderNode('b')),
                nodes.LiteralNode('a'),
                nodes.LiteralNode('b')
            ),
            {'a': 'd', 'b': 'd'},
            'a',
            None
        ),
        (
            nodes.ConditionNode(
                (nodes.PlaceholderNode('a'), nodes.PlaceholderNode('b')),
                nodes.LiteralNode('a'),
                nodes.LiteralNode('b')
            ),
            {'a': 'd'},
            '',
            RuntimeError
        ),
    ]
)
def test_condition_node_generate(
        node: nodes.ConditionNode, ctx: dict,
        expected_output: str, want_err: Optional[Exception]) -> None:

    if want_err:
        with pytest.raises(want_err):
            node.generate(ctx=Context(ctx))
    else:
        assert expected_output == node.generate(ctx=Context(ctx))


@pytest.mark.parametrize(
    'node_a,node_b,should_equal',
    [
        (nodes.LiteralNode('a'), nodes.LiteralNode('b'), False),
        (nodes.LiteralNode('a'), nodes.LiteralNode('a'), True)
    ]
)
def test_literal_node_eq(node_a: nodes.Node, node_b: nodes.Node, should_equal: bool):
    assert (node_a == node_b) == should_equal


def test_literal_node_generate():
    for val in ['asdf', 'hello', 'world', 'hey_there', '1234', ',']:
        n = nodes.LiteralNode(val)
        assert n.generate() == val


@pytest.mark.parametrize(
    'node_a,node_b,should_eq',
    [
        (nodes.PlaceholderNode('a'), nodes.PlaceholderNode('b'), False),
        (nodes.PlaceholderNode('a'), nodes.PlaceholderNode('a'), True)
    ]
)
def test_placeholder_node_eq(node_a: nodes.Node, node_b: nodes.Node, should_eq: bool) -> None:
    assert (node_a == node_b) == should_eq


@pytest.mark.parametrize(
    'node,ctx,expected_output,want_err',
    [
        (nodes.PlaceholderNode('a'), None, '', RuntimeError),
        (nodes.PlaceholderNode('a'), {}, '', RuntimeError),
        (nodes.PlaceholderNode('a'), {'a': 'hello'}, ' hello', None),
        (nodes.PlaceholderNode('a'), {'a': ','}, ',', None),
        (nodes.PlaceholderNode('a'), {'a': []}, '', None)
    ]
)
def test_placeholder_node_generate(
        node: nodes.PlaceholderNode,
        ctx: dict,
        expected_output: str,
        want_err: Optional[Exception]) -> None:

    if want_err is not None:
        with pytest.raises(want_err):
            node.generate(ctx=Context(ctx) if ctx is not None else None)
    else:
        assert expected_output == node.generate(ctx=Context(ctx))


@pytest.mark.parametrize(
    'node_a,node_b,should_eq',
    [
        (nodes.ReferenceNode('a'), nodes.ReferenceNode('b'), False),
        (nodes.ReferenceNode('a'), nodes.ReferenceNode('a'), True)
    ]
)
def test_reference_node_eq(node_a: nodes.Node, node_b: nodes.Node, should_eq: bool) -> None:
    assert (node_a == node_b) == should_eq


@pytest.mark.parametrize(
    'node_a,node_b,should_eq',
    [
        (nodes.ParameterNode('a'), nodes.ParameterNode('b'), False),
        (nodes.ParameterNode('a'), nodes.ParameterNode('a'), True),
        (nodes.ParameterNode('a'), nodes.ParameterNode('a', nodes.LiteralNode('a')), False),
        (nodes.ParameterNode('a', nodes.LiteralNode('a')), nodes.ParameterNode('a', nodes.LiteralNode('a')), True),
    ]
)
def test_parameter_node_eq(node_a: nodes.Node, node_b: nodes.Node, should_eq: bool) -> None:
    assert (node_a == node_b) == should_eq


@pytest.mark.parametrize(
    'node,ctx,expected_output,want_err',
    [
        (nodes.ParameterNode('hello'), {}, '', None),
        (nodes.ParameterNode('hello', nodes.LiteralNode('asdf')), {}, 'asdf', None),
        (nodes.ParameterNode('hello', nodes.PlaceholderNode('a')), {}, '', RuntimeError),
        (nodes.ParameterNode('hello', nodes.PlaceholderNode('a')), {'a': 'asdf'}, ' asdf', None)
    ]
)
def test_parameter_node_generate(node: nodes.ParameterNode, ctx: dict, expected_output: str,
                                 want_err: Optional[Exception]) -> None:
    if want_err:
        with pytest.raises(want_err):
            node.generate(ctx=Context(ctx))
    else:
        assert expected_output == node.generate(ctx=Context(ctx))


@pytest.mark.parametrize(
    'node_a,node_b,should_eq',
    [
        (nodes.MacroNode('asdf', [], []), nodes.MacroNode('asdf', [], []), True),
        (nodes.MacroNode('asdf', [], []), nodes.MacroNode('something', [], []), False),
        (
            nodes.MacroNode(
                'asdf',
                [nodes.ParameterNode('a')],
                []
            ),
            nodes.MacroNode(
                'asdf',
                [nodes.ParameterNode('a')],
                []
            ),
            True
        ),
        (
                nodes.MacroNode(
                    'asdf',
                    [nodes.ParameterNode('a')],
                    []
                ),
                nodes.MacroNode(
                    'asdf',
                    [nodes.ParameterNode('b')],
                    []
                ),
                False
        ),
        (
                nodes.MacroNode(
                    'asdf',
                    [],
                    [nodes.LiteralNode('a')],
                ),
                nodes.MacroNode(
                    'asdf',
                    [],
                    [nodes.LiteralNode('a')],
                ),
                True
        ),
        (
                nodes.MacroNode(
                    'asdf',
                    [],
                    [nodes.LiteralNode('a')],
                ),
                nodes.MacroNode(
                    'asdf',
                    [],
                    [nodes.LiteralNode('b')],
                ),
                False
        ),
    ]
)
def test_macro_node_eq(node_a: nodes.Node, node_b: nodes.Node, should_eq: bool) -> None:
    assert should_eq == (node_a == node_b)


def test_macro_node_generate_not_implemented():
    m = nodes.MacroNode('some_macro', [], [])
    with pytest.raises(NotImplementedError):
        m.generate()


@pytest.mark.parametrize(
    'node_a,node_b,should_eq',
    [
        (nodes.MacroReferenceNode('a'), nodes.MacroReferenceNode('a'), True),
        (nodes.MacroReferenceNode('a'), nodes.MacroReferenceNode('b'), False),
    ]
)
def test_macro_reference_node_eq(node_a: nodes.Node, node_b: nodes.Node, should_eq: bool) -> None:
    assert should_eq == (node_a == node_b)


def test_macro_reference_node_generate_not_implemented():
    m = nodes.MacroReferenceNode('some_macro')
    with pytest.raises(NotImplementedError):
        m.generate()


@pytest.mark.parametrize(
    'node_a,node_b,should_eq',
    [
        (nodes.EntityNode('a', []), nodes.EntityNode('a', []), True),
        (nodes.EntityNode('a', []), nodes.EntityNode('b', []), False),
        (nodes.EntityNode('a', [nodes.LiteralNode('a')]), nodes.EntityNode('a', []), False),
        (nodes.EntityNode('a', [nodes.LiteralNode('a')]), nodes.EntityNode('a', [nodes.LiteralNode('b')]), False),
        (nodes.EntityNode('a', [], macro=nodes.MacroReferenceNode('a')), nodes.EntityNode('a', []), False),
        (
            nodes.EntityNode(
                'a', [], macro=nodes.MacroReferenceNode('a')
            ),
            nodes.EntityNode(
                'a', [], nodes.MacroReferenceNode('a')
            ), True
        )
    ]
)
def test_entity_node_eq(node_a: nodes.Node, node_b: nodes.Node, should_eq: bool) -> None:
    assert should_eq == (node_a == node_b)


@pytest.mark.parametrize(
    'node,ctx,expected_output,want_err',
    [
        (nodes.EntityNode('a', [nodes.LiteralNode('some'), nodes.LiteralNode('BODY')]), {}, 'someBODY', None),
        (nodes.EntityNode('a', [nodes.LiteralNode('some'), None, nodes.LiteralNode('BODY')]), {}, 'someBODY', None),
        (nodes.EntityNode(
            'a',
            [nodes.LiteralNode('some'), nodes.LiteralNode(''), nodes.LiteralNode('BODY')]
        ), {}, 'someBODY', None),
        (nodes.EntityNode('a', [nodes.PlaceholderNode('a')]), {}, '', RuntimeError),
        (nodes.EntityNode('a', [nodes.PlaceholderNode('a')]), {'a': 'someBODY'}, ' someBODY', None),
    ]
)
def test_entity_node_generate(node: nodes.EntityNode, ctx: dict, expected_output: str,
                              want_err: Optional[Exception]) -> None:
    if want_err:
        with pytest.raises(want_err):
            node.generate(ctx=Context(ctx))
    else:
        assert expected_output == node.generate(ctx=Context(ctx))


@pytest.mark.parametrize(
    'node_a,node_b,should_eq',
    [
        (nodes.AnyNode([]), nodes.AnyNode([]), True),
        (nodes.AnyNode([nodes.LiteralNode('a')]), nodes.AnyNode([]), False),
        (nodes.AnyNode([nodes.LiteralNode('a')]), nodes.AnyNode([nodes.LiteralNode('a')]), True),
    ]
)
def test_any_node_eq(node_a: nodes.Node, node_b: nodes.Node, should_eq: bool) -> None:
    assert should_eq == (node_a == node_b)


@pytest.mark.parametrize(
    'node,ctx,value_set',
    [
        (nodes.AnyNode([nodes.LiteralNode('a'), nodes.LiteralNode('b')]), {}, {'a', 'b'}),
        (nodes.AnyNode(
            [nodes.LiteralNode('a'), nodes.PlaceholderNode('b')]
        ), {'b': ['c', 'x', 'z']}, {'a', ' c', ' x', ' z'})
    ]
)
def test_any_node_generate(node: nodes.AnyNode, ctx: dict, value_set: Set[str]) -> None:
    for i in range(1000):
        assert node.generate(ctx=Context(ctx)) in value_set


@pytest.mark.parametrize(
    'node_a,node_b,should_eq',
    [
        (nodes.OptionalNode(nodes.LiteralNode('a')), nodes.OptionalNode(nodes.LiteralNode('a')), True),
        (nodes.OptionalNode(nodes.LiteralNode('a')), nodes.OptionalNode(nodes.LiteralNode('b')), False),
    ]
)
def test_optional_node_eq(node_a: nodes.Node, node_b: nodes.Node, should_eq: bool) -> None:
    assert should_eq == (node_a == node_b)


def test_optional_node_generate():
    expected_value = 'a'
    node = nodes.OptionalNode(nodes.LiteralNode(expected_value))

    for i in range(1000):
        with mock.patch.object(node.expression, 'generate', return_value=node.expression.generate()) as mock_gen:
            val = node.generate()
            if val == '':
                mock_gen.assert_not_called()
            else:
                assert expected_value == val


@pytest.mark.parametrize(
    'node_a,node_b,should_eq',
    [
        (nodes.ListNode([]), nodes.ListNode([]), True),
        (nodes.ListNode([nodes.LiteralNode('a')]), nodes.ListNode([]), False),
        (nodes.ListNode([nodes.LiteralNode('a')]), nodes.ListNode([nodes.LiteralNode('b')]), False),
        (nodes.ListNode([nodes.LiteralNode('a')]), nodes.ListNode([nodes.LiteralNode('a')]), True),
    ]
)
def test_list_node_eq(node_a: nodes.Node, node_b: nodes.Node, should_eq: bool) -> None:
    assert should_eq == (node_a == node_b)


@pytest.mark.parametrize(
    'node,ctx,expected_output,want_err',
    [
        (nodes.ListNode([nodes.LiteralNode('some'), nodes.LiteralNode('BODY')]), {}, 'someBODY', None),
        (nodes.ListNode([nodes.LiteralNode('some'), None, nodes.LiteralNode('BODY')]), {}, 'someBODY', None),
        (nodes.ListNode(
            [nodes.LiteralNode('some'), nodes.LiteralNode(''), nodes.LiteralNode('BODY')]
        ), {}, 'someBODY', None),
        (nodes.ListNode([nodes.PlaceholderNode('a')]), {}, '', RuntimeError),
        (nodes.ListNode([nodes.PlaceholderNode('a')]), {'a': 'someBODY'}, ' someBODY', None),
    ]
)
def test_list_node_generate(node: nodes.ListNode, ctx: dict, expected_output: str,
                            want_err: Optional[Exception]) -> None:
    if want_err:
        with pytest.raises(want_err):
            node.generate(ctx=Context(ctx))
    else:
        assert expected_output == node.generate(ctx=Context(ctx))


@pytest.mark.parametrize(
    'node_a,node_b,should_eq',
    [
        (nodes.RepeatNode(8, nodes.LiteralNode('a')), nodes.RepeatNode(8, nodes.LiteralNode('b')), False),
        (nodes.RepeatNode(8, nodes.LiteralNode('a')), nodes.RepeatNode(1, nodes.LiteralNode('a')), False),
        (nodes.RepeatNode(8, nodes.LiteralNode('a')), nodes.RepeatNode(8, nodes.LiteralNode('a')), True),
    ]
)
def test_repeat_node_eq(node_a: nodes.Node, node_b: nodes.Node, should_eq: bool) -> None:
    assert should_eq == (node_a == node_b)


@pytest.mark.parametrize(
    'node,ctx,expected_output',
    [
        (nodes.RepeatNode(3, nodes.LiteralNode('a')), {}, 'aaa'),
        (nodes.RepeatNode(3, nodes.PlaceholderNode('a')), {'a': 'b'}, ' b b b'),
    ]
)
def test_repeat_node_generate(node: nodes.RepeatNode, ctx: dict, expected_output: str) -> None:
    assert expected_output == node.generate(ctx=Context(ctx))
