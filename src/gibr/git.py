"""Git-related operations."""

import logging

import click
from git import GitCommandError, Repo


def create_and_push_branch(branch_name: str):
    """Create a new branch and push it to origin."""
    try:
        repo = Repo(".")
        if repo.is_dirty():
            logging.warning("⚠️ Working tree is dirty — uncommitted changes present.")

        # Handle repo with no commits yet (no HEAD)
        if not repo.head.is_valid():
            logging.error("❌ Please make an initial commit before using gibr.")
            return

        # Handle detached HEAD (e.g. checkout of specific commit)
        if repo.head.is_detached:
            logging.warning("⚠️ HEAD is detached (not on a branch).")

        # Determine current branch
        current_branch = repo.active_branch.name
        logging.debug(f"Current branch: {current_branch}")

        # Check if branch already exists locally
        if branch_name in repo.heads:
            if current_branch == branch_name:
                logging.info(
                    f"⚠️ Branch '{branch_name}' already exists and is checked out"
                )
                return
            else:
                logging.info(f"⚠️ Branch '{branch_name}' already exists locally.")
                # Ask user what to do
                if click.confirm(
                    "Would you like to create a new branch with a suffix?", default=True
                ):
                    suffix = click.prompt(
                        "Enter suffix", default="take2", show_default=True
                    )
                    new_name = f"{branch_name}-{suffix}"
                    logging.info(f"Creating new branch '{new_name}' instead.")
                    return create_and_push_branch(new_name)
                else:
                    logging.info("Operation canceled by user.")
                    return
        else:
            # Create new branch from current HEAD
            new_branch = repo.create_head(branch_name)
            logging.info(f"✅ Created branch '{branch_name}' from {current_branch}.")

        # Checkout new branch
        new_branch.checkout()
        logging.info(f"✅ Checked out branch: {branch_name}")

        # Push to origin
        origin = repo.remote(name="origin")
        origin.push(refspec=f"{branch_name}:{branch_name}", set_upstream=True)
        logging.info(f"✅ Pushed branch '{branch_name}' to origin.")

    except GitCommandError as e:
        logging.error(f"Git command failed: {e}")
        raise
