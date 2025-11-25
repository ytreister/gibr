"""Tests for CLI notification utilities."""

from unittest.mock import patch

import click
import pytest

from gibr.notify import error, info, party, safe_echo, success, warning


@patch("gibr.notify.click.secho")
@pytest.mark.parametrize(
    "params",
    [
        (info, "info message", "blue", {}, "ℹ️"),
        (success, "success message", "green", {"bold": True}, "✅"),
        (party, "party time", "magenta", {"bold": True}, "🎉"),
        (warning, "be careful", "yellow", {}, "⚠️"),
    ],
)
def test_click_messages(mock_secho, params):
    """Verify each notification function calls click.secho with proper styling."""
    func, msg, fg, kwargs, icon = params
    func(msg)
    mock_secho.assert_called_once_with(f"{icon}  {msg}", fg=fg, **kwargs)


@patch("gibr.notify.click.secho")
def test_error_function_raises_abort(mock_secho):
    """Ensure error() prints and then raises click.Abort."""
    with pytest.raises(click.Abort):
        error("fatal")

    mock_secho.assert_called_once_with("❌  fatal", fg="red", bold=True)


@patch("gibr.notify.sys.stdout")
def test_safe_echo(mock_stdout):
    """Test that safe_echo writes UTF-8 encoded text to stdout buffer."""
    mock_buffer = mock_stdout.buffer
    text = "hello ✓"

    safe_echo(text)

    mock_buffer.write.assert_called_once_with(text.encode("utf-8") + b"\n")
