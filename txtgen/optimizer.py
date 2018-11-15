from copy import deepcopy

from txtgen import nodes
from txtgen.context import Context

from typing import cast, Optional, Union


NodesWithChildren = Union[nodes.EntityNode, nodes.AnyNode, nodes.ListNode]


class Optimizer:

    def __init__(self, entities, macros, ctx: Context = None) -> None:
        self._entities = entities
        self._macros = macros
        self._ctx = ctx

    def visit_AnyNode(self, node: nodes.AnyNode, parent: nodes.Node) -> nodes.Node:
        if len(node.children) == 1:
            return node.children[0]

        return node

    def visit_ConditionNode(self, node: nodes.ConditionNode, parent: nodes.Node) -> nodes.Node:
        return nodes.exec_condition(node)

    def visit_MacroNode(self, node: nodes.MacroNode, parent: nodes.Node) -> nodes.MacroNode:
        # Add the macro's params to current context & traverse the macro body to replace ReferenceNodes to params by
        # the actual param node.
        new_entities = {
            **self._entities,
            **{p.name: p for p in node.params}
        }

        optimizer = Optimizer(new_entities, self._macros)

        node.children = [optimizer.walk(child, node) for child in node.children]

        return node

    def visit_OptionalNode(self, node: nodes.OptionalNode, parent: nodes.Node) -> Optional[nodes.OptionalNode]:
        if node.expression is None:
            return None

        return node

    def visit_EntityNode(self, node: nodes.EntityNode, parent: nodes.Node) -> nodes.EntityNode:
        if node.macro is not None:
            macro_copy = deepcopy(self._macros[node.macro.key])

            if len(macro_copy.params) != len(node.children):
                diff = abs(len(macro_copy.params) - len(node.children))
                raise SyntaxError(f"Macro {macro_copy.name} missing {diff} parameters.")

            for i, param in enumerate(macro_copy.params):
                param.value = node.children[i]

            node.children = macro_copy.children

        return node

    def visit_ReferenceNode(self, node: nodes.ReferenceNode, parent: nodes.Node) -> nodes.EntityNode:
        return self._entities[node.key]

    @staticmethod
    def visit_LiteralNode(node: nodes.LiteralNode, parent: nodes.Node) -> Optional[nodes.Node]:
        if node.value == '':
            return None
        return nodes.sub_punctuation(node)

    def visit_PlaceholderNode(self, node: nodes.PlaceholderNode, parent: nodes.Node) -> nodes.Node:
        if not self._ctx:
            return node

        # Not the most elegant solution, could be improved
        # Have to manually call the visit literal method since new nodes will never be visited as tree is traversed
        # depth-first
        try:
            values = self._ctx.get(node.key)
        except KeyError:
            return node

        return nodes.AnyNode([self.visit_LiteralNode(nodes.LiteralNode(val), parent) for val in values])

    def walk(self, node: nodes.Node, parent: nodes.Node = None) -> Optional[nodes.Node]:

        if node is None:
            return None

        if node.type == 'Grammar':
            node = cast(nodes.Grammar, node)

            for macro_name, macro in node.macros.items():
                node.macros[macro_name] = self.walk(macro, parent=node)

            new_entities = {}
            for entity_name, entity in node.entities.items():
                new_node = self.walk(entity, parent=node)

                if new_node is not None:
                    new_entities[entity_name] = new_node

            node.entities = new_entities

        elif node.type in {'EntityNode', 'AnyNode', 'ListNode', 'UniqueNode'}:
            node = cast(NodesWithChildren, node)
            node.children = list(
                filter(lambda x: x is not None, [self.walk(child, parent=node) for child in node.children])
            )

        elif node.type == 'ConditionNode':
            node = cast(nodes.ConditionNode, node)

            node.conditions = {self.walk(k, parent=node): self.walk(v, parent=node) for k, v in node.conditions.items()}
            node.expression = self.walk(node.expression, parent=node)
            node.else_expression = self.walk(node.else_expression, parent=node)

        elif node.type == 'OptionalNode':
            node = cast(nodes.OptionalNode, node)
            node.expression = self.walk(node.expression, parent=node)

        visit_name = f'visit_{node.type}'

        if hasattr(self, visit_name) and callable(getattr(self, visit_name)):
            node = getattr(self, visit_name)(node, parent=parent)

        return node


def optimize(grammar: nodes.Grammar, bind_ctx: Context = None) -> nodes.Grammar:
    optimizer = Optimizer(grammar.entities, grammar.macros, bind_ctx)
    return cast(nodes.Grammar, optimizer.walk(grammar))
