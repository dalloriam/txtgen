from copy import deepcopy as copy

from dalloriam.generation import nodes

from typing import Dict, Optional, Union, cast

import random


NodesWithChildren = Union[nodes.EntityNode, nodes.AnyNode, nodes.ListNode, nodes.UniqueNode]


class TreeTraverser:

    def __init__(self, ctx, entities: Dict[str, nodes.EntityNode], macros) -> None:
        self.context = ctx
        self.entities = entities
        self.macros = macros

    def visit_AnyNode(self, node: nodes.AnyNode, parent: nodes.Node) -> nodes.Node:
        if len(node.children) == 1:
            return node.children[0]

        return node

    def visit_ConditionNode(self, node: nodes.ConditionNode, parent: nodes.Node) -> nodes.Node:
        for k, v in node.conditions.items():
            if k.generate() != v.generate():
                return node.else_expression
        return node.expression

    def visit_MacroNode(self, node: nodes.MacroNode, parent: nodes.Node) -> nodes.MacroNode:
        # Add the macro's params to current context & traverse the macro body to replace ReferenceNodes to params by
        # the actual param node.
        new_entities = {
            **self.entities,
            **{p.name: p for p in node.params}
        }

        traverser = TreeTraverser(self.context, new_entities, self.macros)

        node.children = [traverser.walk(child, node) for child in node.children]

        return node

    def visit_OptionalNode(self, node: nodes.OptionalNode, parent: nodes.Node) -> Optional[nodes.OptionalNode]:
        if node.expression is None:
            return None

        return node

    def visit_EntityNode(self, node: nodes.EntityNode, parent: nodes.Node) -> nodes.EntityNode:
        if node.macro is not None:
            macro_copy = copy(self.macros[node.macro.key])

            if len(macro_copy.params) != len(node.children):
                diff = abs(len(macro_copy.params) - len(node.children))
                raise SyntaxError(f"Macro {macro_copy.name} missing {diff} parameters.")

            for i, param in enumerate(macro_copy.params):
                param.value = node.children[i]

            node.children = macro_copy.children

        return node

    def visit_ReferenceNode(self, node: nodes.ReferenceNode, parent: nodes.Node) -> nodes.EntityNode:
        return self.entities[node.key]

    def visit_LiteralNode(self, node: nodes.LiteralNode, parent: nodes.Node) -> Optional[nodes.Node]:

        if node.value == '':
            return None

        if node.value not in [',', '.', ':', ';', '!', '?']:
            return nodes.ListNode([
                nodes.LiteralNode(' '),
                node
            ])
        return node

    def visit_UniqueNode(self, node: nodes.UniqueNode, parent: nodes.Node) -> nodes.Node:

        if len(node.children) == 1 and node.children[0].type == 'PlaceholderNode':
            # Have to manually call the visit literal method since new nodes will never be visited as tree is traversed
            # depth-first
            node.children = [
                self.visit_LiteralNode(nodes.LiteralNode(val), parent) for val in self.context.get(node.children[0].key)
            ]
            random.shuffle(node.children)

        return node

    def visit_PlaceholderNode(self, node: nodes.PlaceholderNode, parent: nodes.Node) -> nodes.Node:
        # Not the most elegant solution, could be improved
        if parent.type != 'UniqueNode':
            # Have to manually call the visit literal method since new nodes will never be visited as tree is traversed
            # depth-first
            return nodes.AnyNode([
                self.visit_LiteralNode(nodes.LiteralNode(val), parent) for val in self.context.get(node.key)
            ])

        return node

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
