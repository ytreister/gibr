"""Error classes for Gibr."""


class GibrError(Exception):
    """Base class for all Gibr errors."""


class IssueNotFoundError(GibrError):
    """Raised when an issue cannot be found in the tracker."""
