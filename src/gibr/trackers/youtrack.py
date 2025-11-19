"""YouTrack issue tracker implementation."""

from http import HTTPStatus

import click
import requests

from gibr.issue import Issue
from gibr.notify import error
from gibr.registry import register_tracker
from gibr.trackers.base import IssueTracker


@register_tracker(key="youtrack", display_name="YouTrack", numeric_issues=False)
class YouTrackTracker(IssueTracker):
    """YouTrack issue tracker."""

    FIELDS = "idReadable,summary,customFields(name,value(name,login))"

    def __init__(self, url: str, token: str, project: str | None = None):
        """Construct YouTrackTracker object."""
        self.url = url.rstrip("/")
        self.token = token
        self.project = project

    @classmethod
    def configure_interactively(cls) -> dict:
        """Prompt user for YouTrack-specific configuration."""
        url = click.prompt("YouTrack base URL (e.g. https://project.youtrack.cloud)")
        project = click.prompt(
            "YouTrack project short name (optional, e.g. PROJ)",
            default="",
            show_default=False,
        ).strip()
        token_var = click.prompt(
            "Environment variable for your YouTrack token", default="YOUTRACK_TOKEN"
        )
        cls.check_token(token_var)
        cfg = {"url": url, "token": f"${{{token_var}}}"}
        if project:
            cfg["project"] = project
        return cfg

    @classmethod
    def from_config(cls, config: dict):
        """Create YouTrackTracker from config dictionary."""
        try:
            url = config["url"]
            token = config["token"]
            project = config.get("project")
        except KeyError as e:
            raise ValueError(f"Missing key in 'youtrack' config: {e.args[0]}")
        return cls(url=url, token=token, project=project)

    @classmethod
    def describe_config(cls, config: dict) -> str:
        """Return a short string describing the config."""
        return f"""YouTrack:
        URL                : {config.get("url")}
        Project            : {config.get("project")}
        Token              : {config.get("token")}"""

    @staticmethod
    def _get_custom_field_value(issue: dict, field_name: str):
        """Get custom field value from YouTrack issue payload."""
        for field in issue.get("customFields", []):
            if field.get("name", "").lower() == field_name.lower():
                return field.get("value")
        return None

    def _get_assignee(self, issue: dict):
        """Get issue assignee from YouTrack issue payload."""
        val = self._get_custom_field_value(issue, "Assignee")
        if isinstance(val, dict):
            return val.get("login")
        return None

    def _get_type(self, issue: dict):
        """Get issue type from YouTrack issue payload."""
        val = self._get_custom_field_value(issue, "Type")
        if isinstance(val, dict):
            return val.get("name")
        return None

    def _headers(self) -> dict:
        token = self.token.replace("${", "").replace("}", "")
        return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    def get_issue(self, issue_id: str) -> dict:
        """Fetch issue details by issue id (e.g. PROJ-123 or 123)."""
        if issue_id.isdigit():
            if not self.project:
                error("Numeric issue id given but no project is configured.")
            readable_id = f"{self.project}-{issue_id}"
        else:
            readable_id = issue_id

        url = f"{self.url}/api/issues/{readable_id}"
        params = {"fields": self.FIELDS}

        resp = requests.get(url, headers=self._headers(), params=params)
        if resp.status_code == HTTPStatus.NOT_FOUND:
            error(f"Issue {readable_id} not found.")
        if resp.status_code != HTTPStatus.OK:
            error(f"YouTrack API request failed: {resp.text}")
        issue = resp.json()
        return Issue(
            id=issue.get("idReadable"),
            title=issue.get("summary"),
            assignee=self._get_assignee(issue),
            type=self._get_type(issue) or "issue",
        )

    def list_issues(self) -> list:
        """List open issues. If `project` configured, scope to that project."""
        query = (
            "#Unresolved"
            if not self.project
            else f"project: {self.project} #Unresolved"
        )

        params = {
            "fields": self.FIELDS,
            "query": query,
            "$top": 50,
        }
        url = f"{self.url}/api/issues"
        resp = requests.get(url, headers=self._headers(), params=params)
        if resp.status_code != HTTPStatus.OK:
            error(f"YouTrack API request failed: {resp.text}")
        issues = resp.json() or []
        return [
            Issue(
                id=issue.get("idReadable"),
                title=issue.get("summary"),
                assignee=self._get_assignee(issue),
                type=self._get_type(issue) or "issue",
            )
            for issue in issues
        ]
