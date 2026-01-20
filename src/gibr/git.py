"""Git-related operations."""

import logging

import click
from git import GitCommandError, InvalidGitRepositoryError, Repo

from gibr.notify import error, info, success, warning


def _validate_repo_state(repo: Repo) -> bool:
    """Validate repository state and emit warnings/errors.

    Returns True if repo is valid to proceed, False otherwise.
    """
    if repo.is_dirty(untracked_files=False):
        warning("Working tree is dirty — uncommitted changes present.")

    if not repo.head.is_valid():
        error("Please make an initial commit before using gibr.")
        return False

    if repo.head.is_detached:
        warning("HEAD is detached (not on a branch).")

    return True


def _handle_existing_branch(repo: Repo, branch_name: str, dry_run: bool) -> str | None:
    """Handle case when branch already exists.

    Returns the branch name to use (possibly with suffix), or None to cancel.
    """
    current_branch = repo.active_branch.name

    if current_branch == branch_name:
        warning(f"Branch '{branch_name}' already exists and is checked out")
        return None

    warning(f"Branch '{branch_name}' already exists locally.")

    if dry_run:
        info(
            f"[DRY RUN] Would prompt to create branch with suffix "
            f"since '{branch_name}' exists."
        )
        return None

    if click.confirm(
        "Would you like to create a new branch with a suffix?", default=True
    ):
        suffix = click.prompt("Enter suffix", default="take2", show_default=True)
        new_name = f"{branch_name}-{suffix}"
        info(f"Creating new branch '{new_name}' instead.")
        return new_name

    info("Operation canceled by user.")
    return None


def create_and_push_branch(
    branch_name: str, is_push: bool = True, dry_run: bool = False
) -> None:
    """Create a new branch and push it to origin."""
    try:
        repo = Repo(".", search_parent_directories=True)

        if not _validate_repo_state(repo):
            repo.close()
            return

        current_branch = repo.active_branch.name
        logging.debug(f"Current branch: {current_branch}")

        # Check if branch already exists locally
        if branch_name in repo.heads:
            result = _handle_existing_branch(repo, branch_name, dry_run)
            if result is None:
                repo.close()
                return
            branch_name = result

        if dry_run:
            info(
                f"[DRY RUN] Would create branch '{branch_name}' from {current_branch}."
            )
            info(f"[DRY RUN] Would checkout branch: {branch_name}")
            if is_push:
                info(f"[DRY RUN] Would push branch '{branch_name}' to origin.")
            repo.close()
            return

        # Create new branch from current HEAD
        new_branch = repo.create_head(branch_name)
        success(f"Created branch '{branch_name}' from {current_branch}.")

        # Checkout new branch
        new_branch.checkout()
        success(f"Checked out branch: {branch_name}")

        if is_push:
            origin = repo.remote(name="origin")
            push_result = origin.push(
                refspec=f"{branch_name}:{branch_name}", set_upstream=True
            )
            push_result.raise_if_error()
            success(f"Pushed branch '{branch_name}' to origin.")
        repo.close()

    except InvalidGitRepositoryError:
        error("Not a git repository (or any of the parent directories).")
    except GitCommandError as e:
        error(f"Git command failed: {e}")
