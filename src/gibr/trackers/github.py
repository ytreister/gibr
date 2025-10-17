"""GitHub issue tracker implementation."""

from github import Github
from github.GithubException import UnknownObjectException

from gibr.error import IssueNotFoundError
from gibr.issue import Issue

from .base import IssueTracker


class GithubTracker(IssueTracker):
    """GitHub issue tracker using PyGithub."""

    def __init__(self, repo: str, token: str):
        """Construct GithubTracker object."""
        self.client = Github(token)
        self.repo = self.client.get_repo(repo)

    def get_issue(self, issue_id: str) -> dict:
        """Fetch issue details by issue number."""
        try:
            issue = self.repo.get_issue(number=int(issue_id))
        except UnknownObjectException:
            raise IssueNotFoundError(
                f"Issue #{issue_id} not found in GitHub repository."
            )
        return Issue(
            id=issue.number,
            title=issue.title,
            type="issue",
        )
