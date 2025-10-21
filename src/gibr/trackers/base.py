"""Base class for issue trackers."""

import os
from abc import ABC, abstractmethod

import click

from gibr.notify import party, warning


class IssueTracker(ABC):
    """Abstract base class for all issue trackers."""

    @abstractmethod
    def get_issue(self, issue_id: str) -> dict:
        """Return issue details as a dictionary."""
        pass

    @abstractmethod
    def list_issues(self) -> list:
        """Return list of open issues."""
        pass

    @classmethod
    def configure_interactively(cls) -> dict:
        """Prompt user for tracker-specific configuration (override in subclasses)."""
        raise NotImplementedError

    @classmethod
    def describe_config(cls, config: dict) -> str:
        """Return formatted summary string of configuration (override in subclasses)."""
        raise NotImplementedError

    @classmethod
    def from_config(cls, config):
        """Create tracker instance from config dictionary (override in subclasses)."""
        raise NotImplementedError

    @classmethod
    def check_token(cls, var_name: str) -> str:
        """Check if a token exists in env or prompt to create it."""
        token = os.getenv(var_name)
        if token:
            party(f"Found {cls.display_name} token in environment ({var_name})")
            return

        warning(f"No {cls.display_name} token found in environment ({var_name}).")
        click.echo("You can set it by running:")
        click.echo(f'  export {var_name}="your_token_here"  (macOS/Linux)')
        click.echo(f'  setx {var_name} "your_token_here"     (Windows)\n')
