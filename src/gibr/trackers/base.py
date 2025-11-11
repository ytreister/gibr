"""Base class for issue trackers."""

import os
from abc import ABC, abstractmethod
from http import HTTPStatus

import click
import requests

from gibr.notify import error, party, warning


class IssueTracker(ABC):
    """Abstract base class for all issue trackers."""

    @abstractmethod
    def _get_assignee(self, issue):
        """Return a slug-safe assignee identifier string, or None."""
        pass

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

    @classmethod
    def import_error(cls, dependency, name):
        """Error notification with details of the import error."""
        error(
            f"{dependency} not installed.\n"
            "Install optional dependency with:\n"
            + click.style(f"  pip install gibr[{name}]", fg="yellow")
            + "\n(or if you use uv: "
            + click.style(f"uv tool install --with {name} gibr", fg="yellow")
            + ")"
        )

    def _graphql_request(self, query: str, variables: dict | None = None):
        """Make a GraphQL request."""
        headers = {
            "Authorization": self.token.replace("${", "").replace("}", ""),
            "Content-Type": "application/json",
        }
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        response = requests.post(self.API_URL, json=payload, headers=headers)
        if response.status_code != HTTPStatus.OK:
            error(f"{self.display_name} API request failed: {response.text}")
        data = response.json()
        if "errors" in data:
            error(f"{self.display_name} API returned errors: {data['errors']}")
        return data.get("data", {})
