"""Tests for the AzureDevOpsTracker class."""

from unittest.mock import MagicMock, patch

import click
import pytest
from azure.devops.exceptions import AzureDevOpsClientError

from gibr.issue import Issue
from gibr.trackers.azure import AzureTracker


@pytest.fixture
def mock_work_item():
    """Fixture returning a mock Azure work item."""
    mock_item = MagicMock()
    mock_item.id = 42
    mock_item.fields = {
        "System.Title": "Fix pipeline bug",
        "System.WorkItemType": "Bug",
        "System.AssignedTo": {"displayName": "John Doe"},
    }
    return mock_item


@pytest.fixture
def mock_wit_client(mock_work_item):
    """Fixture returning a mock Work Item Tracking client."""
    mock_client = MagicMock()
    mock_client.get_work_item.return_value = mock_work_item
    mock_wiql_result = MagicMock()
    mock_wiql_result.work_items = [MagicMock(id=42)]
    mock_client.query_by_wiql.return_value = mock_wiql_result

    return mock_client


@pytest.fixture
def mock_connection(mock_wit_client):
    """Fixture returning a mock Azure DevOps connection."""
    mock_conn = MagicMock()
    mock_conn.clients.get_work_item_tracking_client.return_value = mock_wit_client
    return mock_conn


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_from_config_creates_instance(
    mock_basic_auth, mock_connection, mock_wit_client
):
    """from_config should create AzureTracker with correct params."""
    # Setup the mock connection to return our mock WIT client
    mock_conn_instance = MagicMock()
    mock_conn_instance.clients.get_work_item_tracking_client.return_value = (
        mock_wit_client
    )
    mock_connection.return_value = mock_conn_instance

    # Setup BasicAuthentication mock
    mock_auth_instance = MagicMock()
    mock_basic_auth.return_value = mock_auth_instance

    config = {
        "url": "https://dev.azure.com/myorg",
        "token": "secrettoken",
        "project": "MyProject",
        "team": "MyTeam",
    }

    tracker = AzureTracker.from_config(config)

    # Verify BasicAuthentication was called correctly
    mock_basic_auth.assert_called_once_with("", "secrettoken")

    # Verify Connection was called correctly
    mock_connection.assert_called_once_with(
        base_url="https://dev.azure.com/myorg", creds=mock_auth_instance
    )

    # Verify the tracker was created correctly
    assert isinstance(tracker, AzureTracker)
    assert tracker.url == "https://dev.azure.com/myorg"
    assert tracker.project_name == "MyProject"
    assert tracker.team_name == "MyTeam"
    assert tracker.wit_client == mock_wit_client


@patch("msrest.authentication.BasicAuthentication")
@patch("azure.devops.connection.Connection")
def test_init_connection_failure(mock_connection, mock_basic_auth):
    """Test that ValueError is raised when Azure connection fails."""
    # Setup BasicAuthentication to succeed
    mock_auth_instance = MagicMock()
    mock_basic_auth.return_value = mock_auth_instance

    # Setup Connection to raise an exception
    mock_connection.side_effect = Exception("Connection timeout")

    with pytest.raises(ValueError) as excinfo:
        AzureTracker(
            url="https://dev.azure.com/myorg",
            token="secrettoken",
            project="MyProject",
            team="MyTeam",
            closed_states=["Done", "Removed", "Completed"],
        )

    assert "Failed to connect to Azure: Connection timeout" in str(excinfo.value)
    mock_basic_auth.assert_called_once_with("", "secrettoken")
    mock_connection.assert_called_once_with(
        base_url="https://dev.azure.com/myorg", creds=mock_auth_instance
    )


@pytest.mark.parametrize("missing_key", ["url", "token", "project", "team"])
def test_from_config_raises_valueerror_for_missing_keys(missing_key):
    """from_config should raise ValueError for each missing required key."""
    base_config = {
        "url": "https://dev.azure.com/myorg",
        "token": "secrettoken",
        "project": "MyProject",
        "team": "MyTeam",
    }
    bad_config = base_config.copy()
    del bad_config[missing_key]
    with pytest.raises(ValueError) as excinfo:
        AzureTracker.from_config(bad_config)
    assert f"Missing key in 'azure' config: {missing_key}" in str(excinfo.value)


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_get_issue_success(mock_azure_cls, mock_connection, mock_wit_client):
    """Test successful get_issue returns Issue object with correct fields."""
    # Setup mocks
    mock_conn_instance = MagicMock()
    mock_conn_instance.clients.get_work_item_tracking_client.return_value = (
        mock_wit_client
    )
    mock_connection.return_value = mock_conn_instance

    config = {
        "url": "https://dev.azure.com/myorg",
        "token": "secrettoken",
        "project": "MyProject",
        "team": "MyTeam",
    }

    tracker = AzureTracker.from_config(config)
    issue = tracker.get_issue("42")

    # Verify the WIT client was called correctly
    mock_wit_client.get_work_item.assert_called_once_with(42)

    # Verify the issue was formatted correctly
    assert isinstance(issue, Issue)
    issue_id = 42
    assert issue.id == issue_id
    assert issue.title == "Fix pipeline bug"
    assert issue.type == "Bug"
    assert issue.assignee == "John Doe"


@patch("gibr.trackers.azure.error")
@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_get_issue_not_found(
    _, mock_connection_cls, mock_error, mock_connection, mock_wit_client
):
    """Test that click.Abort is raised when issue is not found."""
    mock_error.side_effect = click.Abort
    mock_connection_cls.return_value = mock_connection
    mock_wit_client.get_work_item.side_effect = AzureDevOpsClientError("Not Found")
    tracker = AzureTracker(
        url="https://dev.azure.com/myorg",
        token="secrettoken",
        project="MyProject",
        team="MyTeam",
        closed_states=["Done", "Removed", "Completed"],
    )

    with pytest.raises(click.Abort):
        tracker.get_issue("999")

    mock_error.assert_called_once_with("Issue #999 was not found")


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_list_issues_returns_list(
    mock_auth, mock_connection_cls, mock_connection, mock_wit_client, mock_work_item
):
    """Test list_issues returns list of Issue objects."""
    mock_connection_cls.return_value = mock_connection

    # Setup mock to return work items properly
    mock_wit_client.get_work_items.return_value = [mock_work_item]

    tracker = AzureTracker(
        url="https://dev.azure.com/myorg",
        token="secrettoken",
        project="proj",
        team="team",
        closed_states=["Done", "Removed", "Completed"],
    )

    issues = tracker.list_issues()

    mock_wit_client.query_by_wiql.assert_called_once()
    mock_wit_client.get_work_items.assert_called_once_with([42])

    assert isinstance(issues, list)
    assert len(issues) == 1
    assert isinstance(issues[0], Issue)
    assert issues[0].title == "Fix pipeline bug"
    assert issues[0].type == "Bug"


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_from_config_with_custom_closed_states(
    mock_basic_auth, mock_connection, mock_wit_client
):
    """from_config should handle custom closed_states configuration."""
    mock_conn_instance = MagicMock()
    mock_conn_instance.clients.get_work_item_tracking_client.return_value = (
        mock_wit_client
    )
    mock_connection.return_value = mock_conn_instance
    mock_auth_instance = MagicMock()
    mock_basic_auth.return_value = mock_auth_instance

    config = {
        "url": "https://dev.azure.com/myorg",
        "token": "secrettoken",
        "project": "MyProject",
        "team": "MyTeam",
        "closed_states": '["Completed", "Archived", "Resolved"]',
    }

    tracker = AzureTracker.from_config(config)

    assert tracker.closed_states == ["Completed", "Archived", "Resolved"]


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_from_config_with_default_closed_states(
    mock_basic_auth, mock_connection, mock_wit_client
):
    """from_config should use default closed_states when not provided."""
    mock_conn_instance = MagicMock()
    mock_conn_instance.clients.get_work_item_tracking_client.return_value = (
        mock_wit_client
    )
    mock_connection.return_value = mock_conn_instance
    mock_auth_instance = MagicMock()
    mock_basic_auth.return_value = mock_auth_instance

    config = {
        "url": "https://dev.azure.com/myorg",
        "token": "secrettoken",
        "project": "MyProject",
        "team": "MyTeam",
    }

    tracker = AzureTracker.from_config(config)

    assert tracker.closed_states == ["Done", "Removed", "Closed"]


def test_from_config_with_invalid_closed_states_json():
    """from_config should raise ValueError for invalid closed_states JSON."""
    config = {
        "url": "https://dev.azure.com/myorg",
        "token": "secrettoken",
        "project": "MyProject",
        "team": "MyTeam",
        "closed_states": "not a valid json",
    }

    with pytest.raises(ValueError) as excinfo:
        AzureTracker.from_config(config)

    assert "Unrecognized list format for closed_states" in str(excinfo.value)


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_build_state_exclusion_with_single_state(
    mock_auth, mock_connection_cls, mock_connection
):
    """_build_state_exclusion should correctly format single closed state."""
    mock_connection_cls.return_value = mock_connection

    tracker = AzureTracker(
        url="https://dev.azure.com/myorg",
        token="secrettoken",
        project="MyProject",
        team="MyTeam",
        closed_states=["Done"],
    )

    result = tracker._build_state_exclusion()

    assert result == "[System.State] NOT IN ('Done')"


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_build_state_exclusion_with_multiple_states(
    mock_auth, mock_connection_cls, mock_connection
):
    """_build_state_exclusion should correctly format multiple closed states."""
    mock_connection_cls.return_value = mock_connection

    tracker = AzureTracker(
        url="https://dev.azure.com/myorg",
        token="secrettoken",
        project="MyProject",
        team="MyTeam",
        closed_states=["Done", "Removed", "Completed", "Archived"],
    )

    result = tracker._build_state_exclusion()

    assert (
        result == "[System.State] NOT IN ('Done', 'Removed', 'Completed', 'Archived')"
    )


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_list_issues_uses_closed_states_in_query(
    mock_auth, mock_connection_cls, mock_connection, mock_wit_client, mock_work_item
):
    """Test that list_issues uses closed_states in the WIQL query."""
    mock_connection_cls.return_value = mock_connection
    mock_wit_client.get_work_items.return_value = [mock_work_item]

    tracker = AzureTracker(
        url="https://dev.azure.com/myorg",
        token="secrettoken",
        project="proj",
        team="team",
        closed_states=["Completed", "Archived"],
    )

    tracker.list_issues()

    # Get the WIQL query that was passed
    call_args = mock_wit_client.query_by_wiql.call_args
    wiql_object = call_args[0][0]
    query = wiql_object.query

    # Verify the query contains the correct state exclusion
    assert "[System.State] NOT IN ('Completed', 'Archived')" in query


def test_describe_config_returns_expected_format():
    """describe_config() should return a formatted summary of the config."""
    config = {
        "url": "https://dev.azure.com/myorg ",
        "project": "MyProject",
        "team": "MyTeam",
        "token": "secrettoken",
        "closed_states": '["Completed", "Archived"]',
    }
    result = AzureTracker.describe_config(config)
    assert result.startswith("Azure DevOps:")
    assert "URL" in result
    assert "Project" in result
    assert "Team" in result
    assert "Token" in result
    assert "https://dev.azure.com/myorg" in result
    assert "MyProject" in result
    assert "MyTeam" in result
    assert "secrettoken" in result
    assert "Closed States" in result
    assert '["Completed", "Archived"]' in result


def test_describe_config_with_default_closed_states():
    """describe_config() should show default closed_states when not provided."""
    config = {
        "url": "https://dev.azure.com/myorg",
        "project": "MyProject",
        "team": "MyTeam",
        "token": "secrettoken",
    }

    result = AzureTracker.describe_config(config)

    assert "Closed States" in result
    # The describe_config shows the default value
    assert "Done" in result or '["Done", "Removed", "Closed"]' in str(result)


@patch.object(AzureTracker, "check_token")
@patch(
    "click.prompt",
    side_effect=["https://dev.azure.com/myorg", "MyProject", "MyTeam", "AZURE_TOKEN"],
)
def test_azure_configure_interactively(mock_prompt, mock_check_token):
    """Should prompt user for Azure settings and return correct dict."""
    result = AzureTracker.configure_interactively()
    expected_call_count = 4
    assert mock_prompt.call_count == expected_call_count
    mock_check_token.assert_called_once_with("AZURE_TOKEN")
    assert result == {
        "url": "https://dev.azure.com/myorg",
        "project": "MyProject",
        "team": "MyTeam",
        "token": "${AZURE_TOKEN}",
    }


@patch("gibr.trackers.azure.error")
@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_list_issues_handles_empty_results(
    mock_auth, mock_connection_cls, mock_error, mock_connection, mock_wit_client
):
    """Test list_issues returns empty list when no work items found."""
    mock_connection_cls.return_value = mock_connection

    # Mock empty query result
    mock_wiql_result = MagicMock()
    mock_wiql_result.work_items = []
    mock_wit_client.query_by_wiql.return_value = mock_wiql_result

    tracker = AzureTracker(
        url="https://dev.azure.com/myorg",
        token="secrettoken",
        project="proj",
        team="team",
        closed_states=["Done", "Removed", "Completed"],
    )

    issues = tracker.list_issues()

    assert isinstance(issues, list)
    assert len(issues) == 0
    mock_wit_client.get_work_items.assert_not_called()


@patch("gibr.trackers.azure.error", side_effect=SystemExit)
@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_list_issues_handles_query_exception(
    _, mock_connection_cls, mock_error, mock_connection, mock_wit_client
):
    """Test list_issues handles exceptions during query execution."""
    mock_connection_cls.return_value = mock_connection
    mock_wit_client.query_by_wiql.side_effect = Exception("Query failed")

    tracker = AzureTracker(
        url="https://dev.azure.com/myorg",
        token="secrettoken",
        project="proj",
        team="team",
        closed_states=["Done", "Removed", "Completed"],
    )
    with pytest.raises(SystemExit):
        tracker.list_issues()

    mock_error.assert_called_once()
    assert (
        "Failed to get issues, run again with --verbose flag for more details"
        in str(mock_error.call_args)
    )


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_get_assignee_with_assignee(_, mock_connection_cls, mock_connection):
    """_get_assignee should return displayName when assignee exists."""
    mock_connection_cls.return_value = mock_connection
    tracker = AzureTracker(
        url="https://dev.azure.com/myorg",
        token="secrettoken",
        project="MyProject",
        team="MyTeam",
        closed_states=["Done", "Removed", "Completed"],
    )
    mock_issue = MagicMock()
    mock_issue.fields = {"System.AssignedTo": {"displayName": "Bob"}}

    result = tracker._get_assignee(mock_issue)
    assert result == "Bob"


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_get_assignee_no_assignee(mock_auth, mock_connection_cls, mock_connection):
    """_get_assignee should return None when no assignee info exists."""
    mock_connection_cls.return_value = mock_connection
    tracker = AzureTracker(
        url="https://dev.azure.com/myorg ",
        token="secrettoken",
        project="MyProject",
        team="MyTeam",
        closed_states=["Done", "Removed", "Completed"],
    )
    mock_issue = MagicMock()
    mock_issue.fields = {}

    result = tracker._get_assignee(mock_issue)
    assert result is None


@patch.object(AzureTracker, "import_error", side_effect=SystemExit)
def test_import_error_called_when_azure_missing(mock_import_error):
    """Should call import_error() when azure-devops is not installed."""
    with patch("builtins.__import__", side_effect=ImportError):
        with pytest.raises(SystemExit):
            AzureTracker(
                url="https://dev.azure.com/myorg",
                token="secrettoken",
                project="MyProject",
                team="MyTeam",
                closed_states=["Done", "Removed", "Completed"],
            )

    mock_import_error.assert_called_once_with("azure-devops", "azure")
