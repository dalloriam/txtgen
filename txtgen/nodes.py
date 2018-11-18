from txtgen.context import Context

from typing import Any, Dict, List, Optional, Tuple

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
        (left_cond, right_cond) = node.condition
        if left_cond.generate(ctx) != right_cond.generate(ctx):
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

    def __init__(self, entities: Dict[str, 'EntityNode'], macros: Dict[str, 'MacroNode']) -> None:
        super().__init__()
        self.entities = entities
        self.macros = macros

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Grammar):
            return NotImplemented

        return self.entities == other.entities and self.macros == other.macros

    def generate(self, entity_name: str, ctx: dict = None) -> str:
        ctx = Context(ctx) if ctx else None
        return self.entities[entity_name].generate(ctx=ctx).strip()


class ConditionNode(Node):

    def __init__(self, condition: Tuple[Node, Node], expression: Node, else_expression: Node = None) -> None:
        super().__init__()
        self.condition = condition
        self.expression = expression
        self.else_expression = else_expression

    def __eq__(self, other: Any):
        if not isinstance(other, ConditionNode):
            return NotImplemented

        return self.condition[0] == other.condition[0] and \
            other.condition[1] == other.condition[1] and \
            self.expression == self.expression and \
            self.else_expression == other.else_expression

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

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ParameterNode):
            return NotImplemented

        return self.name == other.name and self.value == other.value

    def generate(self, ctx: Context = None):
        if self.value is None:
            return ''
        return self.value.generate(ctx=ctx)


class MacroNode(Node):

    def __init__(self, name: str, params: List[ParameterNode], children: List[Node]) -> None:
        super().__init__()
        self.name = name
        self.params = params

        self.children = children

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MacroNode):
            return NotImplemented

        return self.name == other.name and \
            self.params == other.params and \
            self.children == other.children


class MacroReferenceNode(Node):

    def __init__(self, key: str) -> None:
        super().__init__()
        self.key = key

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MacroReferenceNode):
            return NotImplemented

        return self.key == other.key


class EntityNode(Node):

    def __init__(self, name: str, children: List[Node], macro=None) -> None:
        super().__init__()
        self.name = name
        self.macro = macro
        self.children = children

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, EntityNode):
            return NotImplemented

        return self.name == other.name and \
            self.macro == other.macro and \
            self.children == other.children

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

        return self.children == other.children

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

        return self.children == other.children

    def generate(self, ctx: Context = None) -> str:
        return ''.join(filter(lambda o: bool, (next_node.generate(ctx=ctx) for next_node in self.children)))
