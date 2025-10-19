"""Factory for issue trackers."""

from .github import GithubTracker
from .jira import JiraTracker


def get_tracker(config):
    """Return issue tracker based on config."""
    try:
        tracker_type = config["issue-tracker"]["name"]
    except KeyError:
        raise ValueError("Missing 'issue-tracker.name' in config.")
    if tracker_type == "github":
        try:
            github_config = config["github"]
        except KeyError:
            raise ValueError("Missing 'github' config.")
        try:
            repo = github_config["repo"]
            token = github_config["token"]
        except KeyError as e:
            raise ValueError(f"Missing key in 'github' config: {e.args[0]}")
        return GithubTracker(repo=repo, token=token)
    elif tracker_type == "jira":
        try:
            jira_config = config["jira"]
        except KeyError:
            raise ValueError("Missing 'jira' config.")
        try:
            url = jira_config["url"]
            user = jira_config["user"]
            token = jira_config["token"]
            project_key = jira_config["project_key"]
        except KeyError as e:
            raise ValueError(f"Missing key in 'jira' config: {e.args[0]}")
        return JiraTracker(url=url, token=token, user=user, project_key=project_key)
    else:
        raise ValueError(f"Unsupported tracker type: {tracker_type}")
