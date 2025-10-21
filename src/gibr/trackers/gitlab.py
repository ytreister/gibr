"""GitLab issue tracker integration."""

from gibr.registry import register_tracker
from gibr.trackers.base import IssueTracker


@register_tracker(
    key="gitlab",
    display_name="GitLab",
    supported=False,
)
class GitlabTracker(IssueTracker):
    """Stub tracker for GitLab (not yet implemented)."""
