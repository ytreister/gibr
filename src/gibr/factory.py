"""Factory for issue trackers."""

from gibr.registry import get_tracker_class
from gibr.trackers.base import IssueTracker


def get_tracker(config) -> IssueTracker:
    """Return issue tracker instance based on config."""
    try:
        tracker_type = config["issue-tracker"]["name"]
    except KeyError:
        raise ValueError("Missing 'issue-tracker.name' in config.")

    tracker_cls = get_tracker_class(tracker_type)

    # Expect each tracker to implement a from_config() constructor.
    if hasattr(tracker_cls, "from_config"):
        return tracker_cls.from_config(config.get(tracker_type, {}))
    else:
        raise TypeError(
            f"{tracker_cls.__name__} must implement from_config(config_dict)."
        )
