from txtgen import nodes
from txtgen.context import Context
from txtgen.optimizer import optimize
from txtgen.parser import DescentParser


def make(src: str, bind_ctx: dict = None) -> nodes.Grammar:
    """
    Parse & optimize a grammar from source code.
    Args:
        src (str): The grammar source.
        bind_ctx (Optional[dict]): The context to bind to the grammar.

    Returns:
        An optimized grammar object.
    """
    ctx = Context(bind_ctx) if bind_ctx else None

    p = DescentParser(src)
    return optimize(p.grammar(), ctx)
