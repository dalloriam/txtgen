from txtgen.constants import PUNCTUATION
from txtgen.context import Context

from typing import Any, Dict, List, Optional, Tuple, Sequence, cast

import random


def sub_punctuation(node: "LiteralNode") -> "Node":
    """
    Prepends a space to non-punctuation literal nodes.
    Args:
        node (LiteralNode): The LiteralNode to replace.

    Returns:
        The processed node.
    """
    if node.value not in PUNCTUATION:
        return ListNode([LiteralNode(" "), node])
    return node


def exec_condition(node: "ConditionNode", ctx: Context = None) -> "Optional[Node]":
    """
    Tries to execute a condition node with information gathered from context and replace said node by its evaluated
    value.
    Args:
        node (ConditionNode): The node to evaluate.
        ctx (Context): The context object.

    Returns:
        The processed node.
    """
    try:
        (left_cond, right_cond) = node.condition
        assert left_cond is not None and right_cond is not None
        if left_cond.generate(ctx) != right_cond.generate(ctx):
            return node.else_expression
        return node.expression

    except (ValueError, RuntimeError):
        return node


class Node:
    """
    The base node.
    """

    def __init__(self) -> None:
        """
        Constructor.
        """
        self.type = self.__class__.__name__

    def generate(self, *args, **kwargs) -> str:
        """ Generate returns the value of the node. """
        raise NotImplementedError  # pragma: nocover


class Grammar(Node):
    """ Represents a context-free grammar. """

    def __init__(
        self, entities: Dict[str, "EntityNode"], macros: Dict[str, "MacroNode"]
    ) -> None:
        """
        Grammar constructor.
        Args:
            entities (Dict[str, EntityNode]): Entities defined in the grammar.
            macros (Dict[str, MacroNode]): Macros defined in the grammar.
        """
        super().__init__()
        self.entities = entities
        self.macros = macros

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Grammar):
            return NotImplemented  # pragma: nocover

        return self.entities == other.entities and self.macros == other.macros

    def generate(self, entity_name: str, ctx: dict = None) -> str:  # type: ignore
        """
        Generates a value for a specific entity.
        Args:
            entity_name (str): The name of the entity to generate.
            ctx (Optional[dict]): The generation context.

        Returns:
            The generated entity.
        """
        new_context = Context(ctx) if ctx else None
        return self.entities[entity_name].generate(ctx=new_context).strip()


class ConditionNode(Node):
    """
    Represents a condition to the generation of a branch. Both sides of the condition will first be generated,
    and ConditionNode will return the generated value for `expression` if both sides are equal, returning the value of
    `else_expression` otherwise.
    """

    def __init__(
        self,
        condition: Tuple[Optional[Node], Optional[Node]],
        expression: Node,
        else_expression: Node = None,
    ) -> None:
        """
        Constructor.
        Args:
            condition (Tuple[Node, Node]): The condition pair.
            expression (Node): The expression to evaluate if the condition is true.
            else_expression (Optional[Node]): The expression to evaluate if the condition is false.
        """
        super().__init__()
        self.condition = condition
        self.expression: Optional[Node] = expression
        self.else_expression: Optional[Node] = else_expression

    def __eq__(self, other: Any):
        if not isinstance(other, ConditionNode):
            return NotImplemented  # pragma: nocover

        return (
            self.condition == other.condition
            and self.expression == other.expression
            and self.else_expression == other.else_expression
        )

    def generate(self, ctx: Context = None) -> str:  # type: ignore
        """
        Evaluate the condition & evaluate the appropriate expression.
        Args:
            ctx (Optional[Context]): The generation context.

        Returns:
            The generated expression.
        """
        out_node = exec_condition(self, ctx)

        if out_node is self:
            raise RuntimeError("Could not execute conditions.")

        return out_node.generate(ctx) if out_node else ""


class LiteralNode(Node):
    """
    LiteralNode represents a literal string in the generation graph.
    """

    def __init__(self, value: str) -> None:
        """
        Constructor.
        Args:
            value (str): The literal value.
        """
        super().__init__()
        self.value = value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, LiteralNode):
            return NotImplemented

        return self.value == other.value

    def generate(self, ctx: Context = None) -> str:  # type: ignore
        """
        Generates by returning the literal value.
        Args:
            ctx (Optional[Context]): The generation context.

        Returns:
            The literal value.
        """
        return self.value


class PlaceholderNode(Node):
    """
    A placeholder holds the place for a value that will be substituted from the generation context - either at
    compile time or at runtime.
    """

    def __init__(self, key: str) -> None:
        """
        Constructor.
        Args:
            key (str): The context key.
        """
        super().__init__()
        self.key = key

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PlaceholderNode):
            return NotImplemented  # pragma: nocover

        return self.key == other.key

    def generate(self, ctx: Context = None):  # type: ignore
        """
        Substitutes the placeholder.
        Args:
            ctx (Optional[Context]): The generation context.

        Returns:
            A randomly selected value from the corresponding context key.
        """
        if ctx is None:
            raise RuntimeError(
                f"could not get value for placeholder [{self.key}] - no context provided"
            )

        try:
            val = ctx.get(self.key)
        except KeyError:
            raise RuntimeError(
                f"could not get value for placeholder [{self.key}] - key is missing"
            )

        if not val:
            return ""

        return sub_punctuation(LiteralNode(random.choice(val))).generate()


class ReferenceNode(Node):

    """
    References another entity.
    """

    def __init__(self, key: str) -> None:
        """
        Constructor.
        Args:
            key (str): The entity key.
        """
        super().__init__()
        self.key = key

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ReferenceNode):
            return NotImplemented  # pragma: nocover

        return self.key == other.key


class ParameterNode(Node):
    """
    Holds parameter values in macros.
    """

    def __init__(self, name: str, value: Node = None) -> None:
        """
        Constructor.
        Args:
            name (str): Parameter name.
            value (Optional[Node]): Assigned value of the parameter.
        """
        super().__init__()
        self.name = name
        self.value = value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ParameterNode):
            return NotImplemented  # pragma: nocover

        return self.name == other.name and self.value == other.value

    def generate(self, ctx: Context = None):  # type: ignore
        """
        Evaluates the value set for the parameter.
        Args:
            ctx (Optional[Context]): The generation context.

        Returns:
            The evaluated parameter - if value is set.
        """
        if self.value is None:
            return ""
        return self.value.generate(ctx=ctx)


class MacroNode(Node):
    """
    Holds a macro definition.
    """

    def __init__(
        self,
        name: str,
        params: Sequence[ParameterNode],
        children: Sequence[Optional[Node]],
    ) -> None:
        """
        Constructor
        Args:
            name (str): The name of the macro.
            params (List[ParameterNode]): The macro parameters.
            children (List[Optional[Node]]): The macro body.
        """
        super().__init__()
        self.name = name
        self.params = params

        self.children = children

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MacroNode):
            return NotImplemented  # pragma: nocover

        return (
            self.name == other.name
            and self.params == other.params
            and self.children == other.children
        )


class MacroReferenceNode(Node):
    """
    References an existing macro. Used in entity definitions.
    """

    def __init__(self, key: str) -> None:
        """
        Constructor.
        Args:
            key (str): The macro reference key.
        """
        super().__init__()
        self.key = key

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MacroReferenceNode):
            return NotImplemented

        return self.key == other.key


class EntityNode(Node):
    """
    Represents a top-level entity that can be generated by the grammar.
    """

    def __init__(
        self,
        name: str,
        children: Sequence[Optional[Node]],
        macro: MacroReferenceNode = None,
    ) -> None:
        """
        Constructor.
        Args:
            name (str): Name of the entity.
            children (Sequence[Node]): Entity body.
            macro (Optional[MacroReferenceNode]): Macro to apply to the entity.
        """
        super().__init__()
        self.name = name
        self.macro = macro
        self.children = children

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, EntityNode):
            return NotImplemented  # pragma: nocover

        return (
            self.name == other.name
            and self.macro == other.macro
            and self.children == other.children
        )

    def generate(self, ctx: Context = None) -> str:  # type: ignore
        """
        Generates the entity.
        Args:
            ctx (Optional[Context]): The generation context.

        Returns:
            The evaluated entity.
        """
        return "".join(
            filter(
                lambda o: bool,
                (
                    next_node.generate(ctx=ctx)
                    for next_node in self.children
                    if next_node is not None
                ),
            )
        )


class AnyNode(Node):
    """
    The Any node returns _one_ of its children - at random - on every generation.
    """

    def __init__(self, children: Sequence[Optional[Node]]) -> None:
        """
        Constructor.
        Args:
            children (Sequence[Optional[Node]]): The node body.
        """
        super().__init__()
        self.children = children

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, AnyNode):
            return NotImplemented  # pragma: nocover

        return self.children == other.children

    def generate(self, ctx: Context = None) -> str:  # type: ignore
        """
        Randomly selects and evaluates a child.
        Args:
            ctx (Optional[Context]): The generation context.

        Returns:
            The evaluated node.
        """
        pick = random.choice(self.children)
        assert pick is not None
        return pick.generate(ctx=ctx)


class OptionalNode(Node):
    """ Optionally evaluates an expression at random. """

    def __init__(self, expression: Optional[Node]) -> None:
        """
        Constructor.
        Args:
            expression (Optional[Node]): The node body.
        """
        super().__init__()
        self.expression = expression

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, OptionalNode):
            return NotImplemented  # pragma: nocover

        return other.expression == self.expression

    def generate(self, ctx: Context = None) -> str:  # type: ignore
        """
        Evaluates the internal expression or returns an empty string.
        Args:
            ctx (Optional[Context]): The generation context.

        Returns:
            The evaluated expression.
        """
        # I use lambdas here as to delay the traversal of the optional node's expression until after
        # the random selection is done
        return random.choice(
            [lambda: "", lambda: cast(Node, self.expression).generate(ctx=ctx)]
        )()


class ListNode(Node):
    """
    ListNode represents a list of consecutive values.
    """

    def __init__(self, children: Sequence[Node]) -> None:
        """
        Constructor.
        Args:
            children (Sequence[Node]): The body of the node.
        """
        super().__init__()
        self.children = children

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ListNode):
            return NotImplemented  # pragma: nocover

        return self.children == other.children

    def generate(self, ctx: Context = None) -> str:  # type: ignore
        """
        Successively evaluates all the children of the node.
        Args:
            ctx (Optional[Context]): The generation context.

        Returns:
            The evaluated expression.
        """
        return "".join(
            filter(
                lambda o: bool,
                (
                    next_node.generate(ctx=ctx)
                    for next_node in self.children
                    if next_node is not None
                ),
            )
        )


class RepeatNode(Node):
    """ RepeatNode repeats its body n times. """

    def __init__(self, n_repeat: int, expression: Node) -> None:
        super().__init__()
        self.n_repeat = n_repeat
        self.expression = expression

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RepeatNode):
            return NotImplemented  # pragma: nocover

        return self.n_repeat == other.n_repeat and self.expression == other.expression

    def generate(self, ctx: Context = None) -> str:  # type: ignore
        body = ""
        for i in range(self.n_repeat):
            body += self.expression.generate(ctx=ctx)

        return body
