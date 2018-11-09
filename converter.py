from collections import defaultdict

from typing import Dict, List


class State:

    def __init__(self, starting: bool = False, terminating: bool = False):
        self.starting = starting
        self.terminating = terminating

        self._transitions: Dict[str, List[State]] = defaultdict(lambda: [])

    def connect_to(self, state: 'State', transition: str) -> None:
        self._transitions[transition].append(state)

