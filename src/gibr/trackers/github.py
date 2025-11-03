"""GitHub issue tracker implementation."""

import click

from gibr.issue import Issue
from gibr.notify import error
from gibr.registry import register_tracker

from .base import IssueTracker


@register_tracker(
    key="github",
    display_name="GitHub",
)
class GithubTracker(IssueTracker):
    """GitHub issue tracker using PyGithub."""

    def __init__(self, repo: str, token: str):
        """Construct GithubTracker object."""
        try:
            from github import Auth, Github
            from github.GithubException import UnknownObjectException

            self.UnknownObjectException = UnknownObjectException
        except ImportError:
            self.import_error("PyGithub", "github")
        self.client = Github(auth=Auth.Token(token))
        try:
            self.repo = self.client.get_repo(repo)
        except UnknownObjectException:
            error(f"The specified repo could not be found: {repo}")

    @classmethod
    def configure_interactively(cls) -> dict:
        """Prompt user for GitHub-specific configuration."""
        repo = click.prompt("GitHub repository (e.g. user/repo)")
        token_var = click.prompt(
            "Environment variable for your GitHub token", default="GITHUB_TOKEN"
        )
        cls.check_token(token_var)
        return {"repo": repo, "token": f"${{{token_var}}}"}

    @classmethod
    def from_config(cls, config):
        """Create GithubTracker from config dictionary."""
        try:
            repo = config["repo"]
            token = config["token"]
        except KeyError as e:
            raise ValueError(f"Missing key in 'github' config: {e.args[0]}")
        return cls(repo=repo, token=token)

    @classmethod
    def describe_config(cls, config: dict) -> str:
        """Return a short string describing the config."""
        return f"""Github:
        Repo               : {config.get("repo")}
        Token              : {config.get("token")}"""

    def _get_assignee(self, issue):
        """Get issue assignee."""
        return issue.assignee.login if issue.assignee else None

    def get_issue(self, issue_id: str) -> dict:
        """Fetch issue details by issue number."""
        try:
            issue = self.repo.get_issue(number=int(issue_id))
        except self.UnknownObjectException:
            error(f"Issue #{issue_id} not found in repository.")
        return Issue(
            id=issue.number, title=issue.title, assignee=self._get_assignee(issue)
        )

    def list_issues(self) -> list[dict]:
        """List open issues from the GitHub repository."""
        issues = self.repo.get_issues(state="open")
        return [
            Issue(
                id=issue.number, title=issue.title, assignee=self._get_assignee(issue)
            )
            for issue in issues
            if getattr(issue, "pull_request", None) is None
        ]
