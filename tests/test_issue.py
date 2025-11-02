"""Tests for the Issue dataclass."""

from unittest.mock import patch

from gibr.issue import Issue


def test_issue_initialization():
    """Test that Issue initializes correctly with given attributes."""
    issue = Issue(id=1, title="Bug in login flow", type="bug", assignee="username")

    assert issue.id == 1
    assert issue.title == "Bug in login flow"
    assert issue.type == "bug"
    assert issue.assignee == "username"


@patch("gibr.issue.slugify", return_value="fake-slug")
def test_sanitized_title_uses_slugify_and_default_issue(mock_slugify):
    """Ensure sanitized_title delegates to slugify with the issue title."""
    issue = Issue(id=1, title="Example Title", assignee="username")
    assert issue.type == "issue"
    result = issue.sanitized_title

    mock_slugify.assert_called_once_with("Example Title")
    assert result == "fake-slug"
