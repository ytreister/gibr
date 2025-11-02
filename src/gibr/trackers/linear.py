"""Linear issue tracker implementation."""

import re
from http import HTTPStatus
from textwrap import dedent

import click
import requests

from gibr.issue import Issue
from gibr.notify import error
from gibr.registry import register_tracker

from .base import IssueTracker


@register_tracker(key="linear", display_name="Linear", numeric_issues=False)
class LinearTracker(IssueTracker):
    """Linear issue tracker."""

    API_URL = "https://api.linear.app/graphql"

    def __init__(self, token: str, team: str | None = None):
        """Construct LinearTracker object."""
        self.token = token
        if team and not self.is_linear_team_key(team):
            error(
                f"Invalid Linear team key: {team}. "
                "Must start with a letter and contain only A–Z, 0–9 and be 1-5 chars."
            )
        self.team = team

    @classmethod
    def is_linear_issue(cls, issue: str) -> bool:
        """Check if the issue matches Linear team key format (e.g. ENG-123)."""
        issue = issue.strip()
        return bool(re.match(r"^[A-Z][A-Z0-9]*-\d+$", issue))

    @classmethod
    def is_linear_team_key(cls, key: str) -> bool:
        """Validate Linear team key (e.g. ENG)."""
        key = key.strip()
        return bool(re.match(r"^[A-Z][A-Z0-9]{0,4}$", key))

    @classmethod
    def configure_interactively(cls) -> dict:
        """Prompt user for Linear-specific configuration."""
        team = click.prompt(
            "Linear team key (optional, e.g. ENG)", default="", show_default=False
        ).strip()

        if team and not cls.is_linear_team_key(team):
            error(
                f"Invalid Linear team key: {team}. "
                "Must start with a letter and contain only A–Z, 0–9 and be 1-5 chars."
            )

        token_var = click.prompt(
            "Environment variable for your Linear API key",
            default="LINEAR_TOKEN",
        )
        cls.check_token(token_var)

        config = {"token": f"${{{token_var}}}"}
        if team:
            config["team"] = team

        return config

    @classmethod
    def from_config(cls, config):
        """Create LinearTracker from config dictionary."""
        try:
            token = config["token"]
            team = config.get("team", None)
        except KeyError as e:
            raise ValueError(f"Missing key in 'linear' config: {e.args[0]}")
        return cls(token=token, team=team)

    @classmethod
    def describe_config(cls, config: dict) -> str:
        """Return a summary of the Linear configuration."""
        return f"""Linear:
        Team Key           : {config.get("team")}
        Token              : {config.get("token")}"""

    def _graphql_request(self, query: str, variables: dict | None = None):
        """Make a GraphQL request to Linear."""
        headers = {
            "Authorization": self.token.replace("${", "").replace("}", ""),
            "Content-Type": "application/json",
        }
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        response = requests.post(self.API_URL, json=payload, headers=headers)
        if response.status_code != HTTPStatus.OK:
            error(f"Linear API request failed: {response.text}")
        data = response.json()
        if "errors" in data:
            error(f"Linear API returned errors: {data['errors']}")
        return data.get("data", {})

    def _get_assignee(self, issue):
        """Get issue assignee."""
        return (
            issue.get("assignee", {}).get("displayName")
            if issue.get("assignee")
            else None
        )

    def get_issue(self, issue_id: str) -> dict:
        """Fetch issue details by issue key (TEAM-123) or number."""
        if issue_id.isdigit():
            if not self.team:
                error(
                    dedent(f"""
                    Invalid issue id provided: {issue_id}
                    To use numeric issue IDs, you must add team key to your .gibrconfig:
                    [linear]
                    team = ENG
                """)
                )
            team_key = self.team
            number = issue_id
        else:
            team_key, number = issue_id.split("-")
        number = int(number)
        query = """
            query ($teamKey: String!, $number: Float!) {
                issues(
                    filter: {
                        team: { key: { eq: $teamKey } },
                        number: { eq: $number }
                    }
                ) {
                    nodes {
                        id
                        identifier
                        title
                        assignee {
                            displayName
                        }
                    }
                }
            }
        """
        data = self._graphql_request(query, {"teamKey": team_key, "number": number})
        issues = data.get("issues", {}).get("nodes", [])
        if not issues:
            error(f"Issue {team_key}-{number} not found in Linear.")

        issue = issues[0]
        return Issue(
            id=issue["identifier"],
            title=issue["title"],
            assignee=self._get_assignee(issue),
        )

    def list_issues(self) -> list[dict]:
        """List open issues from the Linear team (if configured)."""
        team_filter = 'team: { key: { eq: "%s" } },' % self.team if self.team else ""  # noqa: UP031
        query = (
            """
            query {
                issues(filter: {
                    %s
                    state: { type: { neq: "completed" } }
                }) {
                    nodes {
                        identifier
                        title
                        assignee {
                            displayName
                        }
                    }
                }
            }
        """  # noqa: UP031
            % team_filter
        )
        data = self._graphql_request(query)
        issues = data.get("issues", {}).get("nodes", [])
        return [
            Issue(
                id=issue["identifier"],
                title=issue["title"],
                assignee=self._get_assignee(issue),
            )
            for issue in issues
        ]
