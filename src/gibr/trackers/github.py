"""GitHub issue tracker implementation."""

from github import Auth, Github
from github.GithubException import UnknownObjectException

from gibr.issue import Issue
from gibr.notify import error

from .base import IssueTracker


class GithubTracker(IssueTracker):
    """GitHub issue tracker using PyGithub."""

    def __init__(self, repo: str, token: str):
        """Construct GithubTracker object."""
        self.client = Github(auth=Auth.Token(token))
        self.repo = self.client.get_repo(repo)

    def get_issue(self, issue_id: str) -> dict:
        """Fetch issue details by issue number."""
        try:
            issue = self.repo.get_issue(number=int(issue_id))
        except UnknownObjectException:
            error(f"Issue #{issue_id} not found in repository.")
        return Issue(
            id=issue.number,
            title=issue.title,
            type="issue",
        )

    def list_issues(self) -> list[dict]:
        """List open issues from the GitHub repository."""
        issues = self.repo.get_issues(state="open")
        return [
            Issue(
                id=issue.number,
                title=issue.title,
                type="issue",
            )
            for issue in issues
        ]
