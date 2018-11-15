from txtgen.context import Context

import pytest


def test_context_initialize_with_none():
    c = Context()
    assert {} == c.ctx


def test_get_flat_values():
    c = Context({
        'hello': 'world',
        'a': 42,
        'b': True,
        'c': 42.42,
        'rdm': ['a', 's', 'd', 'f']
    })

    assert ['world'] == c.get('hello')
    assert ['42'] == c.get('a')
    assert ['True'] == c.get('b')
    assert ['42.42'] == c.get('c')
    assert ['a', 's', 'd', 'f'] == c.get('rdm')

    with pytest.raises(KeyError):
        c.get('unknown')


def test_get_nested_values():
    c = Context({
        'a': {
            'b': {
                'c': [18, 19],
                'a': 'world'
            },
            'a': 'hello'
        }
    })

    assert ['hello'] == c.get('a.a')
    assert ['world'] == c.get('a.b.a')
    assert ["{'c': [18, 19], 'a': 'world'}"] == c.get('a.b')
    assert ['18', '19'] == c.get('a.b.c')
