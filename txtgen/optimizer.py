from copy import deepcopy

from txtgen import nodes
from txtgen.context import Context

from typing import cast, Dict, Optional, Union

import re


NodesWithChildren = Union[nodes.EntityNode, nodes.AnyNode, nodes.ListNode]


def camelcase(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class Optimizer:
    """
    The Optimizer traverses the generation graph and makes as many assumptions as possible to shorten the graph
    (and thus improve performance).
    """

    def __init__(self, entities: Dict[str, nodes.EntityNode],
                 macros: Dict[str, nodes.MacroNode], ctx: Context = None) -> None:
        """
        Constructor.
        Args:
            entities (Dict[str, nodes.EntityNode]: The defined entities.
            macros (Dict[str, nodes.MacroNode]: The defined macros.
            ctx (Optional[Context]): The generation context.
        """

        self._entities = entities
        self._macros = macros
        self._ctx = ctx

    @staticmethod
    def visit_any_node(node: nodes.AnyNode) -> Optional[nodes.Node]:
        """
        Optimizations:
            - Replaces the AnyNode by its first child it has only one.
        Args:
            node (nodes.AnyNode): The node to replace.

        Returns:
            The replaced node.
        """
        if len(node.children) == 1:
            return node.children[0]

        return node

    def visit_condition_node(self, node: nodes.ConditionNode) -> Optional[nodes.Node]:
        """
        Optimizations:
            - If all required context keys are defined, preemptively evaluate the condition and replace it by the
                appropriate expression.
        Args:
            node (nodes.ConditionNode): The condition to replace.

        Returns:
            The replaced node.
        """
        return nodes.exec_condition(node, self._ctx)

    def visit_macro_node(self, node: nodes.MacroNode) -> nodes.MacroNode:
        """
        Optimizations:
            - Replaces all references to parameters in the macro body by the actual parameter node.
        Args:
            node (nodes.MacroNode): The macro definition.

        Returns:
            The replaced node.
        """

        # Add the macro's params to current context & traverse the macro body to replace ReferenceNodes to params by
        # the actual param node.
        new_entities = {
            **self._entities,
            **{p.name: cast(nodes.EntityNode, p) for p in node.params}
        }

        optimizer = Optimizer(new_entities, self._macros)

        node.children = [optimizer.walk(child) for child in node.children]

        return node

    @staticmethod
    def visit_optional_node(node: nodes.OptionalNode) -> Optional[nodes.OptionalNode]:
        """
        Optimizations:
            - Remove the node if the internal value of the optional node is None.
        Args:
            node (nodes.OptionalNode): The node to replace.

        Returns:
            The replaced node.
        """
        if node.expression is None:
            return None

        return node

    def visit_entity_node(self, node: nodes.EntityNode) -> nodes.EntityNode:
        """
        Optimizations:
            - If a macro is defined, applies it to the entity.
        Args:
            node (nodes.EntityNode): The entity to replace.

        Returns:
            The replaced node.
        """
        if node.macro is not None:
            macro_copy = deepcopy(self._macros[node.macro.key])

            if len(macro_copy.params) != len(node.children):
                diff = abs(len(macro_copy.params) - len(node.children))
                raise SyntaxError(f"Macro {macro_copy.name} missing {diff} parameters.")

            for i, param in enumerate(macro_copy.params):
                param.value = node.children[i]

            node.children = macro_copy.children
            node.macro = None  # TODO: Support a list of macros

        return node

    def visit_reference_node(self, node: nodes.ReferenceNode) -> nodes.EntityNode:
        """
        Optimizations:
            - Replaces the node by the entity it references, raising if the entity is not defined.
        Args:
            node (nodes.ReferenceNode): Reference to replace.

        Returns:
            The replaced node.
        """
        if node.key not in self._entities:
            raise NameError(f'entity "{node.key}" is not defined')

        return self._entities[node.key]

    @staticmethod
    def visit_literal_node(node: nodes.LiteralNode) -> Optional[nodes.Node]:
        """
        Optimizations:
            - Prepends a space to the literal if its body is not punctuation.
            - Removes the node if the literal value is an empty string.
        Args:
            node (nodes.LiteralNode): The literal to replace.

        Returns:
            The replaced node.
        """
        if node.value == '':
            return None
        return nodes.sub_punctuation(node)

    def visit_placeholder_node(self, node: nodes.PlaceholderNode) -> Optional[nodes.Node]:
        """
        Optimizations:
            - If placeholder is defined in bound context, and placeholder key has a single value, replaces the
                placeholder by a LiteralNode having that value.
            - If placeholder is defined in bound context and placeholder key has multiple values, replaces the
                placeholder by an AnyNode of LiteralNodes corresponding to the context values.
        Args:
            node (nodes.PlaceholderNode): The placeholder to replace.

        Returns:
            The replaced node.
        """
        if not self._ctx:
            return node

        # Not the most elegant solution, could be improved
        # Have to manually call the visit literal method since new nodes will never be visited as tree is traversed
        # depth-first
        try:
            values = self._ctx.get(node.key)
        except KeyError:
            return node

        if len(values) == 1:
            if values[0] is None:
                return None
            return self.visit_literal_node(nodes.LiteralNode(values[0]))

        return nodes.AnyNode([self.visit_literal_node(nodes.LiteralNode(val)) for val in values])

    @staticmethod
    def visit_repeat_node(node: nodes.RepeatNode) -> nodes.Node:
        """
        Optimizations:
            - Replaces the repeat node by a list of its child, repeated n times.
        Args:
            node (nodes.RepeatNode): The node to replace.

        Returns:
            The replaced node.
        """
        return nodes.ListNode([node.expression for _ in range(node.n_repeat)])

    def walk(self, node: Optional[nodes.Node]) -> Optional[nodes.Node]:
        """
        Walks the whole tree and applies the optimizations as it goes.
        Args:
            node (nodes.Node): The starting node.

        Returns:
            The optimized node.
        """

        if node is None:
            return None

        if node.type == 'Grammar':
            node = cast(nodes.Grammar, node)

            for macro_name, macro in node.macros.items():
                new_macro = self.walk(macro)
                assert new_macro is not None
                node.macros[macro_name] = cast(nodes.MacroNode, new_macro)

            new_entities = cast(Dict[str, nodes.EntityNode], {})
            for entity_name, entity in node.entities.items():
                new_node = self.walk(entity)

                if new_node is not None:
                    new_entities[entity_name] = cast(nodes.EntityNode, new_node)

            node.entities = new_entities

        elif node.type in {'EntityNode', 'AnyNode', 'ListNode', 'UniqueNode'}:
            node = cast(NodesWithChildren, node)
            node.children = list(
                filter(lambda x: x is not None, [self.walk(child) for child in node.children])
            )

        elif node.type == 'ConditionNode':
            node = cast(nodes.ConditionNode, node)

            node.condition = (self.walk(node.condition[0]), self.walk(node.condition[1]))
            node.expression = self.walk(node.expression)
            node.else_expression = self.walk(node.else_expression)

        elif node.type == 'OptionalNode' or node.type == 'RepeatNode':
            node = cast(nodes.OptionalNode, node)
            node.expression = self.walk(node.expression)

        visit_name = f'visit_{camelcase(node.type)}'

        if hasattr(self, visit_name) and callable(getattr(self, visit_name)):
            node = getattr(self, visit_name)(node)

        return node


def optimize(grammar: nodes.Grammar, bind_ctx: Context = None) -> nodes.Grammar:
    """
    Optimizes a grammar with a given context.
    Args:
        grammar (nodes.Grammar): Grammar to optimize.
        bind_ctx (Optional[Context]): Context to bind.

    Returns:
        Optimized grammar.
    """
    optimizer = Optimizer(grammar.entities, grammar.macros, bind_ctx)
    return cast(nodes.Grammar, optimizer.walk(grammar))
