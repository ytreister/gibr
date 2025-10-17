"""Factory for issue trackers."""

from .github import GithubTracker


def get_tracker(config):
    """Return issue tracker based on config."""
    tracker_type = config["issue-tracker"]["name"]
    if tracker_type == "github":
        return GithubTracker(
            repo=config["github"]["repo"], token=config["github"]["token"]
        )
    else:
        raise ValueError(f"Unsupported tracker type: {tracker_type}")
