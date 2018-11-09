from typing import Any, Dict, List


class Context:

    def __init__(self, ctx_dict: Dict[str, Any]) -> None:
        self.ctx = ctx_dict if ctx_dict is not None else {}

    def get(self, key: str) -> List[str]:
        split_path = key.split('.')

        current_val = self.ctx
        for path_segment in split_path:
            current_val = current_val[path_segment]

        if not isinstance(current_val, list):
            current_val = [str(current_val)]

        else:
            current_val = [str(item) for item in current_val]

        return current_val
