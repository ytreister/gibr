"""Tests for the LinearTracker class."""

from http import HTTPStatus
from unittest.mock import MagicMock, patch

import click
import pytest

from gibr.issue import Issue
from gibr.trackers.linear import LinearTracker


@pytest.fixture
def mock_post():
    """Fixture to mock requests.post."""
    with patch("gibr.trackers.linear.requests.post") as mock_post:
        yield mock_post


def make_response(status=HTTPStatus.OK, json_data=None):
    """Create a mock response object."""
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.json.return_value = json_data or {}
    mock_resp.text = "mocked response"
    return mock_resp


def test_from_config_creates_instance():
    """from_config should create LinearTracker with correct params."""
    config = {"token": "secret", "team": "ENG"}
    tracker = LinearTracker.from_config(config)
    assert isinstance(tracker, LinearTracker)
    assert tracker.token == "secret"
    assert tracker.team == "ENG"


@pytest.mark.parametrize("missing_key", ["token"])
def test_from_config_raises_valueerror_for_missing_keys(missing_key):
    """from_config should raise ValueError for missing required keys."""
    bad_config = {"team": "ENG"} if missing_key == "token" else {}
    with pytest.raises(ValueError) as excinfo:
        LinearTracker.from_config(bad_config)
    assert f"Missing key in 'linear' config: {missing_key}" in str(excinfo.value)


@patch("gibr.trackers.linear.requests.post")
def test_get_issue_success(mock_post):
    """get_issue should return Issue object when Linear returns valid data."""
    tracker = LinearTracker(token="t", team="ENG")
    mock_post.return_value = make_response(
        json_data={
            "data": {
                "issues": {
                    "nodes": [
                        {
                            "id": "abc123",
                            "identifier": "ENG-123",
                            "title": "Fix bug",
                        }
                    ]
                }
            }
        }
    )

    issue = tracker.get_issue("ENG-123")

    assert isinstance(issue, Issue)
    assert issue.id == "ENG-123"
    assert issue.title == "Fix bug"
    assert issue.type == "issue"


@patch("gibr.trackers.linear.error", side_effect=click.Abort)
@patch("gibr.trackers.linear.requests.post")
def test_get_issue_not_found_triggers_error(mock_post, mock_error):
    """Should call error() if issue not found."""
    tracker = LinearTracker(token="t", team="ENG")
    mock_post.return_value = make_response(
        json_data={"data": {"issues": {"nodes": []}}}
    )

    with pytest.raises(click.Abort):
        tracker.get_issue("ENG-999")

    mock_error.assert_called_once()
    assert "not found" in mock_error.call_args[0][0]


@patch("gibr.trackers.linear.error", side_effect=click.Abort)
def test_init_invalid_team_key_triggers_error(mock_error):
    """Invalid team key should call error()."""
    with pytest.raises(click.Abort):
        LinearTracker(token="abc", team="invalid_team")
    mock_error.assert_called_once()


def test_describe_config_returns_expected_format():
    """describe_config should return a formatted summary string."""
    config = {"token": "${LINEAR_TOKEN}", "team": "ENG"}
    result = LinearTracker.describe_config(config)

    assert result.startswith("Linear:")
    assert "Team Key" in result
    assert "Token" in result
    assert "ENG" in result
    assert "${LINEAR_TOKEN}" in result


@patch.object(LinearTracker, "check_token")
@patch(
    "click.prompt",
    side_effect=["ENG", "LINEAR_TOKEN"],
)
def test_configure_interactively(mock_prompt, mock_check_token):
    """Should prompt for team and token and return correct config."""
    result = LinearTracker.configure_interactively()

    expected_call_count = 2
    assert mock_prompt.call_count == expected_call_count
    mock_check_token.assert_called_once_with("LINEAR_TOKEN")
    assert result == {"token": "${LINEAR_TOKEN}", "team": "ENG"}


@patch("gibr.trackers.linear.error")
@patch.object(LinearTracker, "check_token")
@patch("click.prompt", side_effect=["BAD_TEAM", "LINEAR_TOKEN"])
def test_configure_interactively_invalid_team(
    mock_prompt, mock_check_token, mock_error
):
    """Invalid team key should trigger error()."""
    mock_error.side_effect = click.Abort
    with pytest.raises(click.Abort):
        LinearTracker.configure_interactively()
    mock_error.assert_called_once()


@pytest.mark.parametrize(
    "issue,expected",
    [
        ("ENG-123", True),
        ("A1-1", True),
        (" ENG-123 ", True),
        ("ENG123", False),
        ("eng-123", False),
        ("-123", False),
        ("", False),
    ],
)
def test_is_linear_issue(issue, expected):
    """is_linear_issue should correctly validate Linear issue keys."""
    assert LinearTracker.is_linear_issue(issue) is expected


@pytest.mark.parametrize(
    "key,expected",
    [
        ("ENG", True),
        ("A1", True),
        ("ABCDE", True),
        ("A", True),
        ("ENGG1", True),
        ("ENGGGG", False),  # too long (>5)
        ("eng", False),  # lowercase invalid
        ("1ENG", False),  # must start with letter
        ("", False),
    ],
)
def test_is_linear_team_key(key, expected):
    """is_linear_team_key should correctly validate team keys."""
    assert LinearTracker.is_linear_team_key(key) is expected


@patch("gibr.trackers.linear.error", side_effect=click.Abort)
def test_get_issue_without_team_and_numeric_id_triggers_error(mock_error):
    """If numeric id given without team, error should be raised."""
    tracker = LinearTracker(token="t", team=None)
    with pytest.raises(click.Abort):
        tracker.get_issue("123")
    assert "Invalid issue id provided" in mock_error.call_args[0][0]


@patch("gibr.trackers.linear.requests.post")
def test_list_issues_returns_list(mock_post):
    """list_issues should return list of Issue objects."""
    tracker = LinearTracker(token="t", team="ENG")
    mock_post.return_value = make_response(
        json_data={
            "data": {
                "issues": {
                    "nodes": [
                        {
                            "identifier": "ENG-1",
                            "title": "Do something",
                        }
                    ]
                }
            }
        }
    )

    result = tracker.list_issues()

    assert isinstance(result, list)
    assert len(result) == 1
    issue = result[0]
    assert isinstance(issue, Issue)
    assert issue.id == "ENG-1"
    assert issue.title == "Do something"
    assert issue.type == "issue"
    mock_post.assert_called_once()


@patch("gibr.trackers.linear.error", side_effect=click.Abort)
@patch("gibr.trackers.linear.requests.post")
def test_graphql_request_non_200_triggers_error(mock_post, mock_error):
    """_graphql_request should call error() if status != 200."""
    tracker = LinearTracker(token="t")
    mock_post.return_value = make_response(status=HTTPStatus.BAD_REQUEST)

    with pytest.raises(click.Abort):
        tracker._graphql_request("query")

    mock_error.assert_called_once()
    assert "Linear API request failed" in mock_error.call_args[0][0]


@patch("gibr.trackers.linear.error", side_effect=click.Abort)
@patch("gibr.trackers.linear.requests.post")
def test_graphql_request_handles_graphql_errors(mock_post, mock_error):
    """_graphql_request should call error() if response contains GraphQL 'errors'."""
    tracker = LinearTracker(token="t", team="ENG")

    mock_post.return_value = MagicMock(
        status_code=HTTPStatus.OK,
        json=lambda: {"errors": [{"message": "Some GraphQL failure"}]},
        text="mocked text",
    )

    with pytest.raises(click.Abort):
        tracker._graphql_request("query { something }")

    mock_error.assert_called_once()
    assert "Some GraphQL failure" in str(mock_error.call_args[0][0])


@patch.object(
    LinearTracker,
    "_graphql_request",
    return_value={
        "issues": {
            "nodes": [
                {
                    "id": "abc123",
                    "identifier": "ENG-45",
                    "title": "Add telemetry",
                }
            ]
        }
    },
)
def test_get_issue_with_numeric_id_and_team_calls_graphql_with_correct_vars(
    mock_graphql,
):
    """get_issue should derive team_key and number correctly for numeric ID."""
    tracker = LinearTracker(token="t", team="ENG")

    tracker.get_issue("45")

    # Assert correct call to _graphql_request
    mock_graphql.assert_called_once()
    assert mock_graphql.call_args[0][1] == {"teamKey": "ENG", "number": 45}
