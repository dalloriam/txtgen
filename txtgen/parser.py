from txtgen import nodes
from txtgen.constants import Function, TokenType
from txtgen.tokenizer import tokenize, Token

from typing import Optional, Union


Expression = Union[
    nodes.LiteralNode,
    nodes.PlaceholderNode,
    nodes.ReferenceNode,
    nodes.OptionalNode,
    nodes.AnyNode,
    nodes.ListNode,
    nodes.ConditionNode
]


class DescentParser:

    def __init__(self, text: str) -> None:
        self.text = text

        self._initialize()
        self._advance()

    def _initialize(self) -> None:
        self.tokens = tokenize(self.text)
        self.current_token: Optional[Token] = None
        self.next_token: Optional[Token] = None

    def _advance(self) -> None:
        self.current_token, self.next_token = self.next_token, next(self.tokens, None)

    def _accept(self, token_type: TokenType) -> bool:
        if self.next_token and self.next_token.type == token_type:
            self._advance()
            return True

        return False

    def _expect(self, token_type: TokenType) -> None:
        if not self._accept(token_type):
            if self.current_token:
                raise SyntaxError(
                    f'Expected {token_type.name}, got {self.current_token.type.name} '
                    f'with value [{self.current_token.value}] instead'
                )
            else:
                raise SyntaxError(f'Expected {token_type.name}, got EOF instead.')  # pragma: nocover

    def grammar(self) -> nodes.Grammar:
        self._expect(TokenType.ParenOpen)
        self._expect(TokenType.Grammar)

        entities = {}
        macros = {}

        while not self._accept(TokenType.ParenClose):
            self._expect(TokenType.ParenOpen)

            if self._accept(TokenType.Entity):
                new_entity = self.entity()
                entities[new_entity.name] = new_entity

            else:
                self._expect(TokenType.Macro)
                new_macro = self.macro()
                macros[new_macro.name] = new_macro

        return nodes.Grammar(entities, macros)

    def macro(self) -> nodes.MacroNode:
        self._expect(TokenType.Symbol)
        macro_name = self.current_token.value

        macro_params = []
        self._expect(TokenType.ParenOpen)
        while self._accept(TokenType.Symbol):
            macro_params.append(nodes.ParameterNode(self.current_token.value))
        self._expect(TokenType.ParenClose)

        macro_children = []
        while not self._accept(TokenType.ParenClose):
            macro_children.append(self.expression())

        return nodes.MacroNode(macro_name, macro_params, macro_children)

    def entity(self) -> nodes.EntityNode:
        entity_macro = None

        self._expect(TokenType.Symbol)
        entity_name = self.current_token.value

        if self._accept(TokenType.AngleOpen):
            self._expect(TokenType.Symbol)
            entity_macro = nodes.MacroReferenceNode(self.current_token.value)
            self._expect(TokenType.AngleClose)

        entity_children = []

        while not self._accept(TokenType.ParenClose):
            entity_children.append(self.expression())

        return nodes.EntityNode(entity_name, entity_children, macro=entity_macro)

    def expression(self) -> Expression:
        if self._accept(TokenType.Literal):
            return nodes.LiteralNode(value=self.current_token.value)

        if self._accept(TokenType.Placeholder):
            return nodes.PlaceholderNode(key=self.current_token.value)

        if self._accept(TokenType.Symbol):
            return nodes.ReferenceNode(key=self.current_token.value)

        if self._accept(TokenType.BracketOpen):
            optional_expr = self.expression()
            self._expect(TokenType.BracketClose)
            return nodes.OptionalNode(optional_expr)

        self._expect(TokenType.ParenOpen)
        if self._accept(TokenType.Function):
            fn_type = self.current_token.value

            if fn_type == Function.If:
                condition = self.condition()
                return condition

            children = []

            while not self._accept(TokenType.ParenClose):
                children.append(self.expression())

            if fn_type == Function.Any:
                return nodes.AnyNode(children)

        children = []
        while not self._accept(TokenType.ParenClose):
            children.append(self.expression())

        return nodes.ListNode(children)

    def condition(self) -> nodes.ConditionNode:
        left_side = self.expression()
        self._expect(TokenType.Equal)
        right_side = self.expression()

        body = self.expression()

        if self._accept(TokenType.ParenClose):
            return nodes.ConditionNode((left_side, right_side), body)

        else_expr = self.expression()
        self._expect(TokenType.ParenClose)
        return nodes.ConditionNode((left_side, right_side), body, else_expr)
