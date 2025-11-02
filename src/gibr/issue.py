"""Data class for issue representation."""

from dataclasses import dataclass

from slugify import slugify


@dataclass
class Issue:
    """Simple representation of an issue from any tracker."""

    id: int
    title: str
    assignee: str
    type: str = "issue"

    @property
    def sanitized_title(self) -> str:
        """Sanitized title."""
        return slugify(self.title)
