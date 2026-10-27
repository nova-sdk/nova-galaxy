"""Report class for standardizing command-line interface outputs."""

import json
from typing import Any, Dict, List, Optional


class Report:
    """A command's result."""

    def __init__(self, payload: Optional[Dict[str, Any]] = None, title: str = "", indent: int = 2) -> None:
        self.payload: Dict[str, Any] = payload if payload is not None else {}
        self.title = title
        self.indent = indent

    def __str__(self) -> str:
        """Return a human-readable string representation of the object."""
        return self.get_text()

    def get_text(self) -> str:
        return "\n".join([self.title, *self._expand(self.payload, depth=1)])

    def get_json(self) -> str:
        return json.dumps(self.payload, indent=self.indent)

    def _expand(self, value: Any, depth: int) -> List[str]:
        """Render the contents of a dict or a list as indented lines, one entry per line.

        Anything else, and any empty dict or list, has no contents to expand and gives no lines;
        :func:`_field` prints those on the line of the key that holds them.
        """
        if isinstance(value, dict):
            return [line for key, item in value.items() for line in self._field(f"{key}:", item, depth)]
        if isinstance(value, list):
            return [line for item in value for line in self._field("-", item, depth)]
        return []

    def _field(self, label: str, value: Any, depth: int) -> List[str]:
        """Render one entry: a scalar beside its label, a dict or a list indented beneath it."""
        nested = self._expand(value, depth + 1)
        if nested:
            return [f"{' ' * self.indent * depth}{label}", *nested]
        return [f"{' ' * self.indent * depth}{label} {value}"]
