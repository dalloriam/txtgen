from copy import deepcopy

from dalloriam.generation.converter import State

from typing import Dict, List, Optional, Tuple

import random


class Node:

    def __init__(self) -> None:
        self.type = self.__class__.__name__

    def generate(self, *args, **kwargs) -> str:
        """ Generate returns the value of the node. """
        raise NotImplementedError

    def state(self) -> Tuple[State, List[State]]:
        """ Attach self to current head state """
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

    def generate(self, entity_name: str) -> str:
        return self.entities[entity_name].generate().strip()


class ConditionNode(Node):

    def __init__(self, conditions, expression, else_expression=None) -> None:
        super().__init__()
        self.conditions = conditions
        self.expression = expression
        self.else_expression = else_expression


class LiteralNode(Node):

    def __init__(self, value: str) -> None:
        super().__init__()
        self.value = value

    def state(self) -> Tuple[State, List[State]]:
        a = State()
        b = State()
        a.connect_to(b, self.value)
        return a, [b]

    def generate(self) -> str:
        return self.value

    def __str__(self) -> str:
        return f"<LiteralNode value=[{self.value}]>'"

    def __repr__(self):
        return str(self)


class PlaceholderNode(Node):

    def __init__(self, key: str) -> None:
        super().__init__()
        self.key = key


class ReferenceNode(Node):

    def __init__(self, key: str) -> None:
        super().__init__()
        self.key = key


class ParameterNode(Node):

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.value: Optional[Node] = None

    def state(self) -> Tuple[State, List[State]]:

        if self.value is None:
            a = State()
            return a, [a]

        return self.value.state()

    def generate(self):
        if self.value is None:
            return ''
        return self.value.generate()


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

    def state(self) -> Tuple[State, List[State]]:
        a = State()

        heads = [a]
        for itm in self.children:
            in_state, out_states = itm.state()

            for head in heads:
                head.connect_to(in_state, '')

            heads = out_states

        return a, heads

    def generate(self) -> str:
        return ''.join(
            filter(lambda o: bool, (next_node.generate() for next_node in self.children if next_node is not None))
        )


class AnyNode(Node):

    def __init__(self, children: List[Node]) -> None:
        super().__init__()
        self.children = children

    def state(self) -> Tuple[State, List[State]]:
        a = State()
        exiting = []
        for itm in self.children:
            in_s, exits = itm.state()
            a.connect_to(in_s, '')
            exiting += exits
        return a, exiting

    def generate(self) -> str:
        return random.choice(self.children).generate()


class OptionalNode(Node):

    def __init__(self, expression: Node) -> None:
        super().__init__()
        self.expression = expression

    def state(self) -> Tuple[State, List[State]]:
        a = State()

        empty_state = State()
        took_state, out_states = self.expression.state()

        a.connect_to(empty_state, '')
        a.connect_to(took_state, '')

        return a, [*out_states, empty_state]

    def generate(self) -> str:
        # I use lambdas here as to delay the traversal of the optional node's expression until after
        # the random selection is done
        return random.choice([lambda: "", lambda: self.expression.generate()])()


class ListNode(Node):
    """ ListNode represents a list of consecutive values"""
    def __init__(self, children: List[Node]) -> None:
        super().__init__()
        self.children = children

    def state(self) -> Tuple[State, List[State]]:
        a = State()

        heads = [a]
        for itm in self.children:
            in_state, out_states = itm.state()

            for head in heads:
                head.connect_to(in_state, '')

            heads = out_states

        return a, heads

    def generate(self) -> str:
        return ''.join(filter(lambda o: bool, (next_node.generate() for next_node in self.children)))


class UniqueNode(Node):

    def __init__(self, children: List[Node]) -> None:
        super().__init__()
        self.children = children

    def state(self) -> Tuple[State, List[State]]:
        all_children = [c for c in self.children]

        entry = State()
        exits = []

        for child in self.children:
            assert isinstance(child, Node)
            self.children = [c for c in all_children if c != child]
            in_s, out_ss = child.state()
            entry.connect_to(in_s, '')
            exits += out_ss

        return entry, exits

    def generate(self) -> str:
        current_length = len(self.children)
        if current_length == 0:
            return ''

        i = random.randrange(current_length)

        return self.children.pop(i).generate()
