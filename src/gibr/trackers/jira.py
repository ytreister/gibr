"""Jira issue tracker implementation."""

from jira import JIRA
from jira.exceptions import JIRAError

from gibr.issue import Issue
from gibr.notify import error

from .base import IssueTracker


class JiraTracker(IssueTracker):
    """Jira issue tracker."""

    def __init__(self, url: str, user: str, token: str, project_key: str):
        """Construct JiraTracker object."""
        self.project_key = project_key
        try:
            self.client = JIRA(server=url, basic_auth=(user, token))
        except JIRAError as e:
            raise ValueError(f"Failed to connect to Jira: {e.text}")

    def get_issue(self, issue_id: str) -> dict:
        """Fetch issue details by issue number (using project key)."""
        issue_key = f"{self.project_key}-{issue_id}"
        try:
            issue = self.client.issue(issue_key)
        except JIRAError:
            error(f"Issue {issue_key} not found in Jira project {self.project_key}.")
            return None

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
        try:
            issues = self.client.search_issues(jql, maxResults=50)
        except JIRAError as e:
            error(f"Failed to list issues for project {self.project_key}: {e.text}")
            return []

        return [
            Issue(
                id=issue.key,
                title=issue.fields.summary,
                type=issue.fields.issuetype.name,
            )
            for issue in issues
        ]
