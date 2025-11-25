"""Unit tests for the GibrGroup command group."""

from unittest.mock import patch

import pytest
from click import Command

from gibr.cli import GibrGroup


def test_git_alias_moves_verbose_flag():
    """Test that 'git' alias moves global flags to the front."""
    group = GibrGroup(name="gibr")

    args = ["git", "issues", "--verbose", "--json"]

    # parse_args mutates args in-place
    args = group.handle_git_alias(args)

    assert args == ["--verbose", "issues", "--json"]


def test_non_git_alias_unchanged():
    """Test that non-'git' commands remain unchanged."""
    group = GibrGroup(name="gibr")

    args = [
        "gibr",
        "--verbose",
        "create",
        "123",
    ]

    # parse_args mutates args in-place
    args = group.handle_git_alias(args)

    assert args == ["gibr", "--verbose", "create", "123"]


@pytest.mark.parametrize(
    "jira_ret, linear_ret, expected",
    [
        (True, False, True),  # Jira match
        (False, True, True),  # Linear match
        (False, False, False),  # Neither match
    ],
)
def test_is_likely_non_digit_issue(jira_ret, linear_ret, expected):
    """Test is_likely_non_digit_issue with various tracker responses."""
    group = GibrGroup()

    with (
        patch("gibr.trackers.jira.JiraTracker.is_jira_issue", return_value=jira_ret),
        patch(
            "gibr.trackers.linear.LinearTracker.is_linear_issue",
            return_value=linear_ret,
        ),
    ):
        result = group.is_likely_non_digit_issue("ABC-123")
        assert result is expected


def test_handle_create_command_inserts_create_for_number_and_issue():
    """Test that 'create' is inserted for numeric and issue-like args."""
    group = GibrGroup()
    group.commands["issues"] = Command("issues")  # fake command

    # numeric
    args = ["123"]
    out = group.handle_create_command(args)
    assert out == ["create", "123"]

    # issue-like
    group.is_likely_non_digit_issue = lambda x: True  # force true
    args = ["ABC-99"]
    out = group.handle_create_command(args)
    assert out == ["create", "ABC-99"]


def test_handle_create_command_does_not_insert_for_existing_command():
    """Test that 'create' is not inserted for existing commands."""
    group = GibrGroup()
    group.commands["issues"] = Command("issues")

    args = ["issues"]
    out = group.handle_create_command(args)
    assert out == ["issues"]


def test_handle_create_command_skips_flags():
    """Test that 'create' is inserted after global flags."""
    group = GibrGroup()
    group.is_likely_non_digit_issue = lambda x: False

    args = ["--verbose", "123"]
    out = group.handle_create_command(args)
    assert out == ["--verbose", "create", "123"]
