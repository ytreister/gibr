"""Monday.com issue tracker integration."""

from gibr.registry import register_tracker
from gibr.trackers.base import IssueTracker


@register_tracker(
    key="monday",
    display_name="Monday.com",
    supported=False,
)
class MondayTracker(IssueTracker):
    """Stub tracker for Monday.com (not yet implemented)."""
