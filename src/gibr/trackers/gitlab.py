"""GitLab issue tracker integration."""

import click

from gibr.issue import Issue
from gibr.notify import error
from gibr.registry import register_tracker
from gibr.trackers.base import IssueTracker


@register_tracker(
    key="gitlab",
    display_name="GitLab",
)
class GitlabTracker(IssueTracker):
    """GitLab issue tracker using python-gitlab."""

    def __init__(self, url: str, token: str, project: str):
        """Initialize GitlabTracker with connection to specified project."""
        try:
            from gitlab import Gitlab
            from gitlab.exceptions import GitlabGetError

            self.GitlabGetError = GitlabGetError
        except ImportError:
            self.import_error("python-gitlab", "gitlab")
        self.url = url
        self.project_name = project
        try:
            self.client = Gitlab(url, private_token=token)
            self.project = self.client.projects.get(project)
        except Exception as e:
            raise ValueError(f"Failed to connect to GitLab: {e}")

    @classmethod
    def configure_interactively(cls) -> dict:
        """Interactively prompt user for GitLab configuration."""
        url = click.prompt(
            "GitLab base URL (e.g. https://gitlab.com)", default="https://gitlab.com"
        )
        project = click.prompt("GitLab project path (e.g. group/project)")
        token_var = click.prompt(
            "Environment variable for your GitLab token", default="GITLAB_TOKEN"
        )
        cls.check_token(token_var)
        return {
            "url": url,
            "project": project,
            "token": f"${{{token_var}}}",
        }

    @classmethod
    def from_config(cls, config):
        """Create GitlabTracker from config dictionary."""
        try:
            url = config["url"]
            token = config["token"]
            project = config["project"]
        except KeyError as e:
            raise ValueError(f"Missing key in 'gitlab' config: {e.args[0]}")
        return cls(url=url, token=token, project=project)

    @classmethod
    def describe_config(cls, config: dict) -> str:
        """Return a short string describing the config."""
        return f"""GitLab:
            URL                : {config.get("url")}
            Project            : {config.get("project")}
            Token              : {config.get("token")}"""

    def _get_assignee(self, issue):
        """Get issue assignee."""
        # Multi-assignee first (newer GitLab versions)
        if getattr(issue, "assignees", None):
            assignees = issue.assignees
            if isinstance(assignees, list) and len(assignees) > 0:
                return assignees[0].get("username")

        # Fallback: single-assignee field (older versions)
        if getattr(issue, "assignee", None):
            return issue.assignee.get("username")

        # No assignee found
        return None

    def get_issue(self, issue_id: str) -> dict:
        """Fetch issue details by issue id."""
        try:
            issue = self.project.issues.get(issue_id)
        except self.GitlabGetError:
            error(f"Issue #{issue_id} not found in GitLab project {self.project_name}.")
        return Issue(
            id=issue.iid, title=issue.title, assignee=self._get_assignee(issue)
        )

    def list_issues(self) -> list[dict]:
        """List all open issues in the project."""
        issues = self.project.issues.list(state="opened", all=True)
        return [
            Issue(id=issue.iid, title=issue.title, assignee=self._get_assignee(issue))
            for issue in issues
        ]
