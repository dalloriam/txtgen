from txtgen.context import Context

from typing import Any, Dict, List, Optional

import random


def sub_punctuation(node: 'LiteralNode') -> 'Node':
    if node.value not in [',', '.', ':', ';', '!', '?', '-']:
        return ListNode([
            LiteralNode(' '),
            node
        ])
    return node


def exec_condition(node: 'ConditionNode', ctx: Context = None) -> 'Node':
    try:
        for k, v in node.conditions.items():
            if k.generate(ctx) != v.generate(ctx):
                return node.else_expression
        return node.expression

    except ValueError:
        return node


class Node:

    def __init__(self) -> None:
        self.type = self.__class__.__name__

    def generate(self, *args, **kwargs) -> str:
        """ Generate returns the value of the node. """
        raise NotImplementedError

    def display(self, padding: str = ''):
        print(f'{padding}{self}')
        if hasattr(self, 'children'):
            for child in self.children:
                child.display('    ' + padding)


class Grammar(Node):

    def __init__(self, entities: Dict[str, 'EntityNode'], macros) -> None:
        super().__init__()
        self.entities = entities
        self.macros = macros

    def generate(self, entity_name: str, ctx: dict = None) -> str:
        ctx = Context(ctx) if ctx else None
        return self.entities[entity_name].generate(ctx=ctx).strip()


class ConditionNode(Node):

    def __init__(self, conditions: Dict[Node, Node], expression: Node, else_expression: Node = None) -> None:
        super().__init__()
        self.conditions = conditions
        self.expression = expression
        self.else_expression = else_expression

    def generate(self, ctx: Context = None) -> str:
        out_node = exec_condition(self, ctx)

        if out_node is self:
            raise RuntimeError('Could not execute conditions.')

        return out_node.generate(ctx) if out_node else ""


class LiteralNode(Node):

    def __init__(self, value: str) -> None:
        super().__init__()
        self.value = value

    def generate(self, ctx=None) -> str:
        return self.value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, LiteralNode):
            return NotImplemented

        return self.value == other.value

    def __str__(self) -> str:
        return f"<LiteralNode value=[{self.value}]>'"

    def __repr__(self):
        return str(self)


class PlaceholderNode(Node):

    def __init__(self, key: str) -> None:
        super().__init__()
        self.key = key

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PlaceholderNode):
            return NotImplemented

        return self.key == other.key

    def generate(self, ctx: Context = None):
        if ctx is None:
            raise ValueError(f"No context provided for key [{self.key}]")

        val = ctx.get(self.key)
        if not val:
            return ''

        if isinstance(val, str):
            return val

        return sub_punctuation(LiteralNode(random.choice(val))).generate()


class ReferenceNode(Node):

    def __init__(self, key: str) -> None:
        super().__init__()
        self.key = key

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ReferenceNode):
            return NotImplemented

        return self.key == other.key


class ParameterNode(Node):

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.value: Optional[Node] = None

    def generate(self, ctx: Context = None):
        if self.value is None:
            return ''
        return self.value.generate(ctx=ctx)


class MacroNode(Node):

    def __init__(self, name: str, params, children: List[Node]) -> None:
        super().__init__()
        self.name = name
        self.params = params

        self.children = children


class MacroReferenceNode(Node):

    def __init__(self, key: str) -> None:
        super().__init__()
        self.key = key


class EntityNode(Node):

    def __init__(self, name: str, children: List[Node], macro=None) -> None:
        super().__init__()
        self.name = name
        self.macro = macro
        self.children = children

    def generate(self, ctx: Context = None) -> str:
        return ''.join(
            filter(lambda o: bool, (
                next_node.generate(ctx=ctx) for next_node in self.children if next_node is not None))
        )


class AnyNode(Node):

    def __init__(self, children: List[Node]) -> None:
        super().__init__()
        self.children = children

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, AnyNode):
            return NotImplemented

        return all(self.children[i] == c for i, c in enumerate(other.children)) and \
            len(other.children) == len(self.children)

    def generate(self, ctx: Context = None) -> str:
        return random.choice(self.children).generate(ctx=ctx)


class OptionalNode(Node):

    def __init__(self, expression: Node) -> None:
        super().__init__()
        self.expression = expression

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, OptionalNode):
            return NotImplemented

        return other.expression == self.expression

    def generate(self, ctx: Context = None) -> str:
        # I use lambdas here as to delay the traversal of the optional node's expression until after
        # the random selection is done
        return random.choice([lambda: "", lambda: self.expression.generate(ctx=ctx)])()


class ListNode(Node):
    """ ListNode represents a list of consecutive values"""
    def __init__(self, children: List[Node]) -> None:
        super().__init__()
        self.children = children

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ListNode):
            return NotImplemented

        return all(self.children[i] == c for i, c in enumerate(other.children)) and \
            len(other.children) == len(self.children)

    def generate(self, ctx: Context = None) -> str:
        return ''.join(filter(lambda o: bool, (next_node.generate(ctx=ctx) for next_node in self.children)))
