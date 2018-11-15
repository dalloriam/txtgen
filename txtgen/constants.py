from enum import Enum


class TokenType(Enum):
    AngleOpen = '<'
    AngleClose = '>'

    BracketOpen = '['
    BracketClose = ']'

    Entity = 'entity'
    Equal = '='

    Function = 'function'

    Grammar = 'grammar'

    Literal = 'literal'

    Macro = 'macro'

    ParenOpen = '('
    ParenClose = ')'

    Placeholder = 'placeholder'

    Symbol = 'symbol'


class Function(Enum):
    Any = 'any'
    If = 'if'

