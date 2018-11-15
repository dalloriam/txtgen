from txtgen import nodes
from txtgen.context import Context
from txtgen.optimizer import optimize
from txtgen.parser import DescentParser


def make(src: str, bind_ctx: dict = None) -> nodes.Grammar:
    ctx = Context(bind_ctx) if bind_ctx else None

    p = DescentParser(src)
    return optimize(p.grammar(), ctx)
