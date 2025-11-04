<!--
Summary: instructions to guide AI coding agents working on the 'gibr' repo.
Keep this short and focused on project-specific patterns, files, and examples.
-->

# copilot-instructions for gibr

This file gives concise, actionable guidance for code-generating AI agents working in this repository.

- Project purpose: `gibr` is a small CLI that generates Git branch names from issue trackers (currently GitHub, future Gitlab, Jira, etc.) and creates + pushes branches.

- Key entry points:
  - `pyproject.toml` defines the CLI script `gibr = 'gibr.cli:cli'` (the Click app).
  - `src/gibr/cli.py` is the CLI handler — follow its logging and error handling patterns when adding subcommands.

- Architecture and data flow (short):
  1. CLI (`gibr.cli:cli`) loads config via `GibrConfig.load()`.
  2. `trackers.factory.get_tracker(config)` returns a tracker (currently `GithubTracker`).
  3. Tracker returns an `Issue` object (`src/gibr/issue.py`) with `id`, `title`, and `type`.
  4. `BranchName.generate(format_string)` formats the branch using placeholders: `{{issuetype}}`, `{{issue}}`, `{{title}}` (the code uses Python `str.format`).
  5. `create_and_push_branch` in `git.py` performs repository checks and pushes to `origin`.

- Config conventions:
  - Repository-specific configuration lives in a `.gibrconfig` file searched from cwd upwards. Use `GibrConfig.CONFIG_FILENAME` to discover/modify behavior.
  - Default branch naming string is stored under the `DEFAULT` section as `branch_name_format`. The format expects placeholders matching the keys used in `BranchName.generate()` (issuetype, issue, title).
  - Tracker configuration example (see `GibrConfig._get_tracker_details_str`):
    - `[issue-tracker] name = github`
    - `[github] repo = owner/repo` and `token = $GITHUB_TOKEN` (environment variable expansion is supported)

- Coding patterns and conventions to follow:
  - Use `logging` for informational output and `gibr.logger.configure_logger` for CLI logging configuration.
  - Raise `gibr.error.IssueNotFoundError` when a tracker cannot find an issue; convert to Click exceptions only in `cli.py`.
  - Tracker implementations should subclass `IssueTracker` and return an `Issue` dataclass instance.
  - Do not change the public CLI signature (`gibr.cli:app`) unless updating `pyproject.toml` script entry.
  - Keep functions small and side-effect boundary explicit: network/tracker calls in tracker modules, git mutations in `git.py` only.

- Tests and linting:
  - Pytest config is defined in `pyproject.toml` under `[tool.pytest.ini_options]` and expects `src` on `PYTHONPATH`.
  - Ruff lint configuration exists in `pyproject.toml`.

- Examples to reference in edits:
  - When generating branch names, `BranchName.generate()` uses `format_string.format(**data)`. Add new placeholders only if you update `DEFAULT.branch_name_format` usage and document the mapping in `src/gibr/branch.py`.
  - When adding a new tracker, add it to `src/gibr/trackers/` and update `trackers.factory.get_tracker()` to recognize the new `name` from `.gibrconfig`.

- Safety and permissions:
  - `GithubTracker` uses a token (PyGitHub). Do not log tokens or commit them to the repo. Use env var expansion via `.gibrconfig`.

- When uncertain, follow these steps (prioritized):
  1. Run local unit tests (`pytest`) — `pyproject.toml` contains options.
  2. Run `gibr` manually by installing in editable mode (pip install -e .) or invoking `python -m gibr.cli` from project root.
  3. For changes touching git operations, exercise on a throwaway repo to avoid pushing unwanted branches.

If anything here looks incomplete or you want additional examples (e.g., `.gibrconfig` sample), ask and I will extend this file.
