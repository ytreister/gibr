"""Forgejo issue tracker integration."""

from gibr.registry import register_tracker
from gibr.trackers.base import IssueTracker


@register_tracker(
    key="forgejo",
    display_name="Forgejo",
    supported=False,
)
class ForgejoTracker(IssueTracker):
    """Stub tracker for Forgejo (not yet implemented)."""
