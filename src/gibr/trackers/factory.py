"""Factory for issue trackers."""

from .github import GithubTracker


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
    else:
        raise ValueError(f"Unsupported tracker type: {tracker_type}")
