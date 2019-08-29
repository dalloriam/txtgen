from typing import Any, Dict, List, cast


class Context:
    """
    Context is a small wrapper around a dict that allows to fetch values from nested keys in a single call.
    """

    def __init__(self, ctx_dict: Dict[str, Any] = None) -> None:
        """
        Constructor.
        Args:
            ctx_dict (Optional[Dict[str, Any]]): Context dictionary.
        """
        self.ctx = ctx_dict if ctx_dict is not None else {}

    def get(self, key: str) -> List[str]:
        """
        Fetches a (possibly nested) key from the context.
        Args:
            key (str): The key to fetch.

        Returns:
            A list of values corresponding to the key.
        """
        split_path = key.split(".")

        current_val: Any = self.ctx
        for path_segment in split_path:
            current_val = current_val[path_segment]

        if not isinstance(current_val, list):
            current_val = [str(current_val)]

        else:
            current_val = [str(item) for item in current_val]

        return cast(List[str], current_val)
