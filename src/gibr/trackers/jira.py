"""Jira issue tracker implementation."""

import logging
import re
from textwrap import dedent

import click
from slugify import slugify

from gibr.issue import Issue
from gibr.notify import error
from gibr.registry import register_tracker

from .base import IssueTracker


@register_tracker(key="jira", display_name="Jira", numeric_issues=False)
class JiraTracker(IssueTracker):
    """Jira issue tracker."""

    def __init__(self, url: str, user: str, token: str, project_key: str = None):
        """Construct JiraTracker object."""
        try:
            from jira import JIRA
            from jira.exceptions import JIRAError

            self.JIRAError = JIRAError
        except ImportError:
            self.import_error("jira", "jira")
        self.project_key = project_key
        try:
            self.client = JIRA(server=url, basic_auth=(user, token))
        except JIRAError as e:
            raise ValueError(f"Failed to connect to Jira: {e.text}")

    @classmethod
    def is_jira_issue(cls, issue: str) -> bool:
        """Check if the issue matches JIRA issue key format (e.g. FOO-123)."""
        issue = issue.strip()
        return bool(re.match(r"^[A-Z][A-Z0-9_]*-\d+$", issue))

    @classmethod
    def is_jira_project_key(cls, key: str) -> bool:
        """Return True if key looks like a valid Jira project key (e.g. PROJ)."""
        key = key.strip()
        return bool(re.match(r"^[A-Z][A-Z0-9_]*$", key))

    @classmethod
    def configure_interactively(cls) -> dict:
        """Prompt user for Jira-specific configuration."""
        url = click.prompt("Jira base URL (e.g. https://company.atlassian.net)")
        project_key = click.prompt(
            "Jira project key (optional, e.g. PROJ)", default="", show_default=False
        ).strip()

        # Validate if provided
        if project_key and not cls.is_jira_project_key(project_key):
            error(
                f"Invalid Jira project key: {project_key}. "
                "Must start with a letter and contain only A–Z, 0–9, or underscores."
            )

        user = click.prompt("Jira username/email")
        token_var = click.prompt(
            "Environment variable for your Jira token", default="JIRA_TOKEN"
        )
        cls.check_token(token_var)

        config = {
            "url": url,
            "user": user,
            "token": f"${{{token_var}}}",
        }

        if project_key:
            config["project_key"] = project_key

        return config

    @classmethod
    def from_config(cls, config):
        """Create JiraTracker from config dictionary."""
        try:
            url = config["url"]
            user = config["user"]
            token = config["token"]
            project_key = config.get("project_key", None)
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

    def _get_assignee(self, issue):
        """Return a slug-safe username-like string."""
        logging.debug("Getting Jira assignee")
        assignee = issue.fields.assignee

        if not assignee:
            logging.debug("No assignee for this issue")
            return None

        # Prefer real username on self-hosted Jira
        if getattr(assignee, "name", None):
            logging.debug("assignee name found, using it")
            return slugify(assignee.name)

        # Fallback to something deterministic on Cloud
        if getattr(assignee, "displayName", None):
            logging.debug("displayName found, using it")
            return slugify(assignee.displayName)

        # Last resort: use part of the accountId (not pretty, but stable)
        if getattr(assignee, "accountId", None):
            logging.debug("accountId found, using it")
            return re.sub(r"[^a-z0-9]+", "", assignee.accountId.lower())[:12]

        return None

    def get_issue(self, issue_id: str) -> dict:
        """Fetch issue details by issue number (using project key)."""
        if issue_id.isdigit() and not self.project_key:
            error(
                dedent(f"""
                Invalid issue id provided: {issue_id}
                To use numeric issue IDs, you must add project key to your .gibrconfig:
                [jira]
                project_key = PROJ
            """)
            )
        issue_key = (
            f"{self.project_key}-{issue_id}"
            if issue_id.isdigit() and self.project_key
            else issue_id
        )
        try:
            issue = self.client.issue(issue_key)
        except self.JIRAError:
            if self.project_key:
                error(
                    f"Issue {issue_key} not found in Jira project {self.project_key}."
                )
            else:
                error(f"Issue {issue_key} not found in Jira instance.")

        return Issue(
            id=issue.key,
            title=issue.fields.summary,
            type=issue.fields.issuetype.name,
            assignee=self._get_assignee(issue),
        )

    def list_issues(self) -> list[dict]:
        """List open issues in the Jira project."""
        jql = (
            f'project = "{self.project_key}" AND ' if self.project_key else ""
        ) + "statusCategory != Done ORDER BY created DESC"
        issues = self.client.search_issues(jql)
        return [
            Issue(
                id=issue.key,
                title=issue.fields.summary,
                type=issue.fields.issuetype.name,
                assignee=self._get_assignee(issue),
            )
            for issue in issues
        ]
