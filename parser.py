from dalloriam.generation import nodes
from dalloriam.generation.context import Context
from dalloriam.generation.traverser import TreeTraverser
from dalloriam.generation.tokenizer import tokenize, Token

from typing import Any, Dict, Optional, Union


Expression = Union[
    nodes.LiteralNode,
    nodes.PlaceholderNode,
    nodes.ReferenceNode,
    nodes.OptionalNode,
    nodes.AnyNode,
    nodes.UniqueNode,
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

    def _accept(self, token_type: str) -> bool:
        if self.next_token and self.next_token.type == token_type:
            self._advance()
            return True

        return False

    def _expect(self, token_type: str) -> None:
        if not self._accept(token_type):
            raise SyntaxError(f'Expected {token_type}, got {self.current_token.type} instead')

    def generate(self, entity_name: str, ctx: Dict[str, Any] = None) -> str:
        return "NONE"

        ctx = Context(ctx)
        grammar = self.grammar()
        return grammar

        #grammar = TreeTraverser(ctx, grammar.entities, grammar.macros).walk(grammar)
        return grammar.generate(entity_name)

    def grammar(self) -> nodes.Grammar:
        self._expect('paren_o')
        self._expect('grammar')

        entities = {}
        macros = {}

        while not self._accept('paren_c'):
            self._expect('paren_o')

            if self._accept('entity'):
                new_entity = self.entity()
                entities[new_entity.name] = new_entity

            else:
                self._expect('macro')
                new_macro = self.macro()
                macros[new_macro.name] = new_macro

        return nodes.Grammar(entities, macros)

    def macro(self) -> nodes.MacroNode:
        self._expect('symbol')
        macro_name = self.current_token.value

        macro_params = []
        self._expect('paren_o')
        while self._accept('symbol'):
            macro_params.append(nodes.ParameterNode(self.current_token.value))
        self._expect('paren_c')

        macro_children = []
        while not self._accept('paren_c'):
            macro_children.append(self.expression())

        return nodes.MacroNode(macro_name, macro_params, macro_children)

    def entity(self) -> nodes.EntityNode:
        entity_macro = None

        if self._accept('angle_o'):
            self._expect('symbol')
            entity_macro = nodes.MacroReferenceNode(self.current_token.value)
            self._expect('angle_c')

        self._expect('symbol')
        entity_name = self.current_token.value

        entity_children = []

        while not self._accept('paren_c'):
            entity_children.append(self.expression())

        return nodes.EntityNode(entity_name, entity_children, macro=entity_macro)

    def expression(self) -> Expression:
        if self._accept('literal'):
            return nodes.LiteralNode(value=self.current_token.value)

        if self._accept('placeholder'):
            return nodes.PlaceholderNode(key=self.current_token.value)

        if self._accept('symbol'):
            return nodes.ReferenceNode(key=self.current_token.value)

        if self._accept('bracket_o'):
            optional_expr = self.expression()
            self._expect('bracket_c')
            return nodes.OptionalNode(optional_expr)

        self._expect('paren_o')
        if self._accept('function'):
            fn_type = self.current_token.value

            if fn_type == 'if':
                condition = self.condition()
                return condition

            children = []

            while not self._accept('paren_c'):
                children.append(self.expression())

            if fn_type == 'any':
                return nodes.AnyNode(children)

            elif fn_type == 'unique':
                return nodes.UniqueNode(children)

        children = []
        while not self._accept('paren_c'):
            children.append(self.expression())

        return nodes.ListNode(children)

    def condition(self) -> nodes.ConditionNode:
        left_side = self.expression()
        self._expect('equal')
        right_side = self.expression()

        body = self.expression()

        if self._accept('paren_c'):
            return nodes.ConditionNode({left_side: right_side}, body)

        else_expr = self.expression()
        self._expect('paren_c')
        return nodes.ConditionNode({left_side: right_side}, body, else_expr)
