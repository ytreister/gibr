"""YouTrack issue tracker integration."""

from gibr.registry import register_tracker
from gibr.trackers.base import IssueTracker


@register_tracker(
    key="youtrack",
    display_name="YouTrack",
    supported=False,
)
class YouTrackTracker(IssueTracker):
    """Stub tracker for YouTrack (not yet implemented)."""
