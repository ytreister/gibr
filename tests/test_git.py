"""Tests for git operations."""

from unittest.mock import MagicMock, patch

import click
import pytest
from git import GitCommandError, InvalidGitRepositoryError

# Expected counts for dry-run log messages
EXPECTED_DRY_RUN_LOG_COUNT_WITH_PUSH = 3
EXPECTED_DRY_RUN_LOG_COUNT_NO_PUSH = 2

# Expected counts for success messages in tests
EXPECTED_SUCCESS_COUNT_CREATE_AND_CHECKOUT = 2  # create + checkout
EXPECTED_SUCCESS_COUNT_CREATE_CHECKOUT_PUSH = 3  # create + checkout + push


@patch("gibr.git.Repo")
@patch("gibr.git.info")
@patch("gibr.git.success")
def test_create_and_push_branch_dry_run_logs_intended_actions(
    mock_success, mock_info, mock_repo_class
):
    """Should log intended actions without creating branch in dry-run mode."""
    from gibr.git import create_and_push_branch

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = False
    mock_repo.head.is_valid.return_value = True
    mock_repo.head.is_detached = False
    mock_repo.active_branch.name = "main"
    mock_repo.heads = []  # No existing branches
    mock_repo_class.return_value = mock_repo

    create_and_push_branch("feature/123-test", is_push=True, dry_run=True)

    # Verify dry-run messages were logged
    assert mock_info.call_count == EXPECTED_DRY_RUN_LOG_COUNT_WITH_PUSH
    mock_info.assert_any_call(
        "[DRY RUN] Would create branch 'feature/123-test' from main."
    )
    mock_info.assert_any_call("[DRY RUN] Would checkout branch: feature/123-test")
    mock_info.assert_any_call(
        "[DRY RUN] Would push branch 'feature/123-test' to origin."
    )

    # Verify no actual git operations were performed
    mock_repo.create_head.assert_not_called()
    mock_success.assert_not_called()


@patch("gibr.git.Repo")
@patch("gibr.git.info")
def test_create_and_push_branch_dry_run_no_push(mock_info, mock_repo_class):
    """Should not log push message when is_push=False in dry-run mode."""
    from gibr.git import create_and_push_branch

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = False
    mock_repo.head.is_valid.return_value = True
    mock_repo.head.is_detached = False
    mock_repo.active_branch.name = "main"
    mock_repo.heads = []
    mock_repo_class.return_value = mock_repo

    create_and_push_branch("feature/456-test", is_push=False, dry_run=True)

    # Verify only create and checkout messages, no push message
    assert mock_info.call_count == EXPECTED_DRY_RUN_LOG_COUNT_NO_PUSH
    mock_info.assert_any_call(
        "[DRY RUN] Would create branch 'feature/456-test' from main."
    )
    mock_info.assert_any_call("[DRY RUN] Would checkout branch: feature/456-test")


@patch("gibr.git.Repo")
@patch("gibr.git.info")
@patch("gibr.git.warning")
def test_create_and_push_branch_dry_run_existing_branch(
    mock_warning, mock_info, mock_repo_class
):
    """Should log that it would prompt for suffix when branch exists in dry-run mode."""
    from gibr.git import create_and_push_branch

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = False
    mock_repo.head.is_valid.return_value = True
    mock_repo.head.is_detached = False
    mock_repo.active_branch.name = "main"
    # Simulate existing branch
    mock_existing_branch = MagicMock()
    mock_existing_branch.name = "feature/existing"
    mock_repo.heads = ["feature/existing"]
    mock_repo_class.return_value = mock_repo

    create_and_push_branch("feature/existing", is_push=True, dry_run=True)

    # Verify warning about existing branch
    mock_warning.assert_called_once_with(
        "Branch 'feature/existing' already exists locally."
    )
    # Verify dry-run message about suffix prompt
    expected_msg = (
        "[DRY RUN] Would prompt to create branch with suffix "
        "since 'feature/existing' exists."
    )
    mock_info.assert_called_once_with(expected_msg)


@patch("gibr.git.Repo")
@patch("gibr.git.warning")
def test_create_and_push_branch_dry_run_validates_dirty_tree(
    mock_warning, mock_repo_class
):
    """Should still show warning for dirty working tree in dry-run mode."""
    from gibr.git import create_and_push_branch

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = True  # Dirty working tree
    mock_repo.head.is_valid.return_value = True
    mock_repo.head.is_detached = False
    mock_repo.active_branch.name = "main"
    mock_repo.heads = []
    mock_repo_class.return_value = mock_repo

    create_and_push_branch("feature/789-test", is_push=True, dry_run=True)

    # Verify validation warning was shown
    mock_warning.assert_called_once_with(
        "Working tree is dirty — uncommitted changes present."
    )


@patch("gibr.git.Repo")
@patch("gibr.git.error")
def test_create_and_push_branch_dry_run_validates_invalid_head(
    mock_error, mock_repo_class
):
    """Should still error for invalid HEAD in dry-run mode."""
    from gibr.git import create_and_push_branch

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = False
    mock_repo.head.is_valid.return_value = False  # Invalid HEAD
    mock_repo_class.return_value = mock_repo

    create_and_push_branch("feature/test", is_push=True, dry_run=True)

    # Verify error was called
    mock_error.assert_called_once_with(
        "Please make an initial commit before using gibr."
    )


@patch("gibr.git.Repo")
@patch("gibr.git.warning")
def test_validate_repo_state_detached_head_warning(mock_warning, mock_repo_class):
    """Should show warning when HEAD is detached."""
    from gibr.git import create_and_push_branch

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = False
    mock_repo.head.is_valid.return_value = True
    mock_repo.head.is_detached = True  # Detached HEAD
    mock_repo.active_branch.name = "main"
    mock_repo.heads = []
    mock_repo_class.return_value = mock_repo

    create_and_push_branch("feature/test", is_push=False, dry_run=True)

    # Verify detached HEAD warning was shown
    mock_warning.assert_called_once_with("HEAD is detached (not on a branch).")


@patch("gibr.git.Repo")
@patch("gibr.git.warning")
def test_handle_existing_branch_already_checked_out(mock_warning, mock_repo_class):
    """Should warn and exit when branch already exists and is checked out."""
    from gibr.git import create_and_push_branch

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = False
    mock_repo.head.is_valid.return_value = True
    mock_repo.head.is_detached = False
    mock_repo.active_branch.name = "feature/already-checked-out"
    mock_repo.heads = ["feature/already-checked-out"]  # Branch exists
    mock_repo_class.return_value = mock_repo

    create_and_push_branch("feature/already-checked-out", is_push=True, dry_run=False)

    # Verify warning about branch being checked out
    mock_warning.assert_called_once_with(
        "Branch 'feature/already-checked-out' already exists and is checked out"
    )
    # Verify no branch creation attempted
    mock_repo.create_head.assert_not_called()


@patch("gibr.git.Repo")
@patch("gibr.git.click.prompt")
@patch("gibr.git.click.confirm")
@patch("gibr.git.warning")
@patch("gibr.git.info")
@patch("gibr.git.success")
def test_handle_existing_branch_user_accepts_suffix(  # noqa: PLR0913
    mock_success, mock_info, mock_warning, mock_confirm, mock_prompt, mock_repo_class
):
    """Should create branch with suffix when user accepts prompt."""
    from gibr.git import create_and_push_branch

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = False
    mock_repo.head.is_valid.return_value = True
    mock_repo.head.is_detached = False
    mock_repo.active_branch.name = "main"
    mock_repo.heads = ["feature/existing"]  # Branch exists
    mock_new_branch = MagicMock()
    mock_repo.create_head.return_value = mock_new_branch
    mock_repo_class.return_value = mock_repo

    # User accepts suffix prompt and enters "v2"
    mock_confirm.return_value = True
    mock_prompt.return_value = "v2"

    create_and_push_branch("feature/existing", is_push=False, dry_run=False)

    # Verify warning about existing branch
    mock_warning.assert_called_once_with(
        "Branch 'feature/existing' already exists locally."
    )
    # Verify info about creating new branch
    mock_info.assert_called_once_with(
        "Creating new branch 'feature/existing-v2' instead."
    )
    # Verify branch created with suffix
    mock_repo.create_head.assert_called_once_with("feature/existing-v2")
    mock_new_branch.checkout.assert_called_once()
    # Verify success messages
    assert mock_success.call_count == EXPECTED_SUCCESS_COUNT_CREATE_AND_CHECKOUT
    mock_success.assert_any_call("Created branch 'feature/existing-v2' from main.")
    mock_success.assert_any_call("Checked out branch: feature/existing-v2")


@patch("gibr.git.Repo")
@patch("gibr.git.click.confirm")
@patch("gibr.git.warning")
@patch("gibr.git.info")
def test_handle_existing_branch_user_declines_suffix(
    mock_info, mock_warning, mock_confirm, mock_repo_class
):
    """Should cancel operation when user declines suffix prompt."""
    from gibr.git import create_and_push_branch

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = False
    mock_repo.head.is_valid.return_value = True
    mock_repo.head.is_detached = False
    mock_repo.active_branch.name = "main"
    mock_repo.heads = ["feature/existing"]  # Branch exists
    mock_repo_class.return_value = mock_repo

    # User declines suffix prompt
    mock_confirm.return_value = False

    create_and_push_branch("feature/existing", is_push=True, dry_run=False)

    # Verify warning about existing branch
    mock_warning.assert_called_once_with(
        "Branch 'feature/existing' already exists locally."
    )
    # Verify cancellation message
    mock_info.assert_called_once_with("Operation canceled by user.")
    # Verify no branch creation
    mock_repo.create_head.assert_not_called()


@patch("gibr.git.Repo")
@patch("gibr.git.success")
def test_create_branch_success_no_push(mock_success, mock_repo_class):
    """Should create and checkout branch without pushing."""
    from gibr.git import create_and_push_branch

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = False
    mock_repo.head.is_valid.return_value = True
    mock_repo.head.is_detached = False
    mock_repo.active_branch.name = "main"
    mock_repo.heads = []
    mock_new_branch = MagicMock()
    mock_repo.create_head.return_value = mock_new_branch
    mock_repo_class.return_value = mock_repo

    create_and_push_branch("feature/new", is_push=False, dry_run=False)

    # Verify branch created and checked out
    mock_repo.create_head.assert_called_once_with("feature/new")
    mock_new_branch.checkout.assert_called_once()
    # Verify success messages
    assert mock_success.call_count == EXPECTED_SUCCESS_COUNT_CREATE_AND_CHECKOUT
    mock_success.assert_any_call("Created branch 'feature/new' from main.")
    mock_success.assert_any_call("Checked out branch: feature/new")
    # Verify no push
    mock_repo.remote.assert_not_called()


@patch("gibr.git.Repo")
@patch("gibr.git.success")
def test_create_branch_success_with_push(mock_success, mock_repo_class):
    """Should create, checkout, and push branch to origin."""
    from gibr.git import create_and_push_branch

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = False
    mock_repo.head.is_valid.return_value = True
    mock_repo.head.is_detached = False
    mock_repo.active_branch.name = "main"
    mock_repo.heads = []
    mock_new_branch = MagicMock()
    mock_repo.create_head.return_value = mock_new_branch
    mock_origin = MagicMock()
    mock_push_result = MagicMock()
    mock_origin.push.return_value = mock_push_result
    mock_repo.remote.return_value = mock_origin
    mock_repo_class.return_value = mock_repo

    create_and_push_branch("feature/with-push", is_push=True, dry_run=False)

    # Verify branch created and checked out
    mock_repo.create_head.assert_called_once_with("feature/with-push")
    mock_new_branch.checkout.assert_called_once()
    # Verify push
    mock_repo.remote.assert_called_once_with(name="origin")
    mock_origin.push.assert_called_once_with(
        refspec="feature/with-push:feature/with-push", set_upstream=True
    )
    mock_push_result.raise_if_error.assert_called_once()
    # Verify all success messages
    assert mock_success.call_count == EXPECTED_SUCCESS_COUNT_CREATE_CHECKOUT_PUSH
    mock_success.assert_any_call("Created branch 'feature/with-push' from main.")
    mock_success.assert_any_call("Checked out branch: feature/with-push")
    mock_success.assert_any_call("Pushed branch 'feature/with-push' to origin.")


@patch("gibr.git.Repo")
@patch("gibr.git.error")
def test_create_branch_invalid_git_repository_error(mock_error, mock_repo_class):
    """Should handle InvalidGitRepositoryError."""
    from gibr.git import create_and_push_branch

    mock_repo_class.side_effect = InvalidGitRepositoryError("Not a repo")
    mock_error.side_effect = click.Abort()

    with pytest.raises(click.Abort):
        create_and_push_branch("feature/test", is_push=True, dry_run=False)

    mock_error.assert_called_once_with(
        "Not a git repository (or any of the parent directories)."
    )


@patch("gibr.git.Repo")
@patch("gibr.git.error")
def test_create_branch_git_command_error(mock_error, mock_repo_class):
    """Should handle GitCommandError during branch creation."""
    from gibr.git import create_and_push_branch

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = False
    mock_repo.head.is_valid.return_value = True
    mock_repo.head.is_detached = False
    mock_repo.active_branch.name = "main"
    mock_repo.heads = []
    mock_repo.create_head.side_effect = GitCommandError("git branch", 128)
    mock_repo_class.return_value = mock_repo
    mock_error.side_effect = click.Abort()

    with pytest.raises(click.Abort):
        create_and_push_branch("feature/error", is_push=False, dry_run=False)

    mock_error.assert_called_once()
    assert "Git command failed:" in mock_error.call_args[0][0]


@patch("gibr.git.Repo")
@patch("gibr.git.error")
@patch("gibr.git.success")
def test_create_branch_git_command_error_during_push(
    mock_success, mock_error, mock_repo_class
):
    """Should handle GitCommandError during push."""
    from gibr.git import create_and_push_branch

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = False
    mock_repo.head.is_valid.return_value = True
    mock_repo.head.is_detached = False
    mock_repo.active_branch.name = "main"
    mock_repo.heads = []
    mock_new_branch = MagicMock()
    mock_repo.create_head.return_value = mock_new_branch
    mock_origin = MagicMock()
    mock_origin.push.side_effect = GitCommandError("git push", 128)
    mock_repo.remote.return_value = mock_origin
    mock_repo_class.return_value = mock_repo
    mock_error.side_effect = click.Abort()

    with pytest.raises(click.Abort):
        create_and_push_branch("feature/push-error", is_push=True, dry_run=False)

    # Branch was created and checked out before push error
    assert mock_success.call_count == EXPECTED_SUCCESS_COUNT_CREATE_AND_CHECKOUT
    mock_success.assert_any_call("Created branch 'feature/push-error' from main.")
    mock_success.assert_any_call("Checked out branch: feature/push-error")
    # Error occurred during push
    mock_error.assert_called_once()
    assert "Git command failed:" in mock_error.call_args[0][0]
