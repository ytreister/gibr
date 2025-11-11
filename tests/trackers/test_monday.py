"""Tests for the MondayTracker class."""

from http import HTTPStatus
from unittest.mock import MagicMock, patch

import click
import pytest

from gibr.issue import Issue
from gibr.trackers.monday import MondayTracker


@pytest.fixture
def mock_post():
    """Fixture to mock requests.post."""
    with patch("gibr.trackers.base.requests.post") as mock_post:
        yield mock_post


def make_response(status=HTTPStatus.OK, json_data=None):
    """Create a mock response object."""
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.json.return_value = json_data or {}
    mock_resp.text = "mocked response"
    return mock_resp


def test_from_config_creates_instance():
    """from_config should create MondayTracker with correct params."""
    config = {"token": "secret", "board_id": "123"}
    tracker = MondayTracker.from_config(config)
    assert isinstance(tracker, MondayTracker)
    assert tracker.token == "secret"
    assert tracker.board_id == "123"


@pytest.mark.parametrize("missing_key", ["token", "board_id"])
def test_from_config_raises_valueerror_for_missing_keys(missing_key):
    """from_config should raise ValueError for missing required keys."""
    bad_config = {"board_id": "123"} if missing_key == "token" else {"token": "abc"}
    with pytest.raises(ValueError) as excinfo:
        MondayTracker.from_config(bad_config)
    assert f"Missing key in 'monday' config: {missing_key}" in str(excinfo.value)


@patch("gibr.trackers.base.requests.post")
def test_get_issue_success(mock_post):
    """get_issue should return Issue when Monday returns valid data."""
    tracker = MondayTracker(token="t", board_id="123")
    mock_post.return_value = make_response(
        json_data={
            "data": {
                "items": [
                    {
                        "id": "456",
                        "name": "Fix something",
                        "column_values": [],
                    }
                ]
            }
        }
    )

    issue = tracker.get_issue("456")

    assert isinstance(issue, Issue)
    assert issue.id == "456"
    assert issue.title == "Fix something"
    assert issue.type == "issue"


@patch("gibr.trackers.monday.error", side_effect=click.Abort)
@patch("gibr.trackers.base.requests.post")
def test_get_issue_not_found_triggers_error(mock_post, mock_error):
    """Should call error() if issue not found."""
    tracker = MondayTracker(token="t", board_id="123")
    mock_post.return_value = make_response(json_data={"data": {"items": []}})

    with pytest.raises(click.Abort):
        tracker.get_issue("999")

    mock_error.assert_called_once()
    assert "not found" in mock_error.call_args[0][0]


@patch("gibr.trackers.monday.error", side_effect=click.Abort)
def test_init_invalid_board_id_triggers_error(mock_error):
    """Invalid board_id should call error()."""
    with pytest.raises(click.Abort):
        MondayTracker(token="abc", board_id="not_numeric")
    mock_error.assert_called_once()


def test_describe_config_returns_expected_format():
    """describe_config should return a formatted summary string."""
    config = {"token": "${MONDAY_TOKEN}", "board_id": "123"}
    result = MondayTracker.describe_config(config)

    assert result.startswith("Monday.dev:")
    assert "Board ID" in result
    assert "Token" in result
    assert "123" in result
    assert "${MONDAY_TOKEN}" in result


@patch.object(MondayTracker, "check_token")
@patch("click.prompt", side_effect=["123", "MONDAY_TOKEN"])
def test_configure_interactively(mock_prompt, mock_check_token):
    """Should prompt for board_id and token and return correct config."""
    result = MondayTracker.configure_interactively()
    expected_count = 2
    assert mock_prompt.call_count == expected_count
    mock_check_token.assert_called_once_with("MONDAY_TOKEN")
    assert result == {"board_id": "123", "token": "${MONDAY_TOKEN}"}


@patch("gibr.trackers.monday.error")
@patch.object(MondayTracker, "check_token")
@patch("click.prompt", side_effect=["BAD", "MONDAY_TOKEN"])
def test_configure_interactively_invalid_board_id(
    mock_prompt, mock_check_token, mock_error
):
    """Invalid board_id should trigger error()."""
    mock_error.side_effect = click.Abort
    with pytest.raises(click.Abort):
        MondayTracker.configure_interactively()
    mock_error.assert_called_once()


@patch("gibr.trackers.base.requests.post")
def test_list_issues_returns_list(mock_post):
    """list_issues should return list of Issue objects."""
    tracker = MondayTracker(token="t", board_id="123")

    mock_post.return_value = make_response(
        json_data={
            "data": {
                "boards": [
                    {
                        "items_page": {
                            "items": [
                                {
                                    "id": "1",
                                    "name": "Do something",
                                    "column_values": [],
                                }
                            ]
                        }
                    }
                ]
            }
        }
    )

    result = tracker.list_issues()

    assert isinstance(result, list)
    assert len(result) == 1
    issue = result[0]
    assert isinstance(issue, Issue)
    assert issue.id == "1"
    assert issue.title == "Do something"
    assert issue.type == "issue"
    mock_post.assert_called_once()


@patch("gibr.trackers.monday.error", side_effect=click.Abort)
@patch("gibr.trackers.base.requests.post")
def test_list_issues_board_not_found_triggers_error(mock_post, mock_error):
    """Should error if board is missing or inaccessible."""
    tracker = MondayTracker(token="t", board_id="123")
    mock_post.return_value = make_response(json_data={"data": {"boards": []}})

    with pytest.raises(click.Abort):
        tracker.list_issues()

    mock_error.assert_called_once()


@patch.object(
    MondayTracker,
    "_graphql_request",
    return_value={
        "items": [
            {
                "id": "456",
                "name": "Fix bug",
                "column_values": [],
            }
        ]
    },
)
def test_get_issue_calls_graphql_with_correct_vars(mock_graphql):
    """get_issue should pass correct variables to _graphql_request."""
    tracker = MondayTracker(token="t", board_id="123")

    tracker.get_issue("456")

    mock_graphql.assert_called_once()
    assert mock_graphql.call_args[0][1] == {"board_id": 123, "item_id": 456}
