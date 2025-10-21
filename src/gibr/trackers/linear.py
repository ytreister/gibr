"""Linear issue tracker integration."""

from gibr.registry import register_tracker
from gibr.trackers.base import IssueTracker


@register_tracker(
    key="linear",
    display_name="Linear",
    supported=False,
)
class LinearTracker(IssueTracker):
    """Stub tracker for Linear (not yet implemented)."""
