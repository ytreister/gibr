"""Base class for issue trackers."""

from abc import ABC, abstractmethod


class IssueTracker(ABC):
    """Abstract base class for all issue trackers."""

    @abstractmethod
    def get_issue(self, issue_id: str) -> dict:
        """Return issue details as a dictionary."""
        pass
