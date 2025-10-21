"""Jira issue tracker implementation."""

import click
from jira import JIRA
from jira.exceptions import JIRAError

from gibr.issue import Issue
from gibr.notify import error
from gibr.registry import register_tracker

from .base import IssueTracker


@register_tracker(
    key="jira",
    display_name="Jira",
)
class JiraTracker(IssueTracker):
    """Jira issue tracker."""

    def __init__(self, url: str, user: str, token: str, project_key: str):
        """Construct JiraTracker object."""
        self.project_key = project_key
        try:
            self.client = JIRA(server=url, basic_auth=(user, token))
        except JIRAError as e:
            raise ValueError(f"Failed to connect to Jira: {e.text}")

    @classmethod
    def configure_interactively(cls) -> dict:
        """Prompt user for Jira-specific configuration."""
        url = click.prompt("Jira base URL (e.g. https://company.atlassian.net)")
        project_key = click.prompt("Jira project key (e.g. PROJ)")
        user = click.prompt("Jira username/email")
        token_var = click.prompt(
            "Environment variable for your Jira token", default="JIRA_TOKEN"
        )
        cls.check_token(token_var)
        return {
            "url": url,
            "project_key": project_key,
            "user": user,
            "token": f"${{{token_var}}}",
        }

    @classmethod
    def from_config(cls, config):
        """Create JiraTracker from config dictionary."""
        try:
            url = config["url"]
            user = config["user"]
            token = config["token"]
            project_key = config["project_key"]
        except KeyError as e:
            raise ValueError(f"Missing key in 'jira' config: {e.args[0]}")
        return cls(url=url, user=user, token=token, project_key=project_key)

    @classmethod
    def describe_config(cls, config: dict) -> str:
        """Return a string summarizing the JIRA tracker configuration."""
        return f"""Jira:
        URL                : {config.get("url")}
        Project Key        : {config.get("project_key")}
        User               : {config.get("user")}
        Token              : {config.get("token")}"""

    def get_issue(self, issue_id: str) -> dict:
        """Fetch issue details by issue number (using project key)."""
        issue_key = f"{self.project_key}-{issue_id}"
        try:
            issue = self.client.issue(issue_key)
        except JIRAError:
            error(f"Issue {issue_key} not found in Jira project {self.project_key}.")

        return Issue(
            id=issue.key,
            title=issue.fields.summary,
            type=issue.fields.issuetype.name,
        )

    def list_issues(self) -> list[dict]:
        """List open issues in the Jira project."""
        jql = (
            f'project = "{self.project_key}" '
            "AND statusCategory != Done "
            "ORDER BY created DESC"
        )
        issues = self.client.search_issues(jql)
        return [
            Issue(
                id=issue.key,
                title=issue.fields.summary,
                type=issue.fields.issuetype.name,
            )
            for issue in issues
        ]
