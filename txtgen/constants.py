from enum import Enum


PUNCTUATION = [',', '.', ':', ';', '!', '?', '-']


class TokenType(Enum):
    """
    TokenType represents the available token types.
    """
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

    Integer = 'integer'

    ParenOpen = '('
    ParenClose = ')'

    Placeholder = 'placeholder'

    Symbol = 'symbol'


class Function(Enum):
    """
    Function represents the supported functions.
    """
    Any = 'any'
    If = 'if'
    Repeat = 'repeat'

