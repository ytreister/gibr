[![Tests](https://github.com/ytreister/gibr/actions/workflows/test.yml/badge.svg)](https://github.com/ytreister/gibr/actions/workflows/test.yml)
[![Coverage](https://codecov.io/gh/ytreister/gibr/branch/main/graph/badge.svg)](https://codecov.io/gh/ytreister/gibr)
[![PyPI version](https://img.shields.io/pypi/v/gibr.svg)](https://pypi.org/project/gibr/)
[![Python versions](https://img.shields.io/pypi/pyversions/gibr.svg)](https://pypi.org/project/gibr/)
[![License](https://img.shields.io/github/license/ytreister/gibr.svg)](https://github.com/ytreister/gibr/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/ytreister/gibr.svg)](https://github.com/ytreister/gibr/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/ytreister/gibr.svg)](https://github.com/ytreister/gibr/pulls)

# gibr
> 🧩 **A smarter CLI for creating Git branches.**

`gibr` connects your Git workflow to your issue tracker — instantly creating consistent, descriptive branches.
Fully configurable, and ready for any tracker or team setup.

Currently supporting integration with GitHub, Jira and Gitlab.

## Usage
```bash
# List open issues
$ gibr issues
|   Issue | Type   | Title                                 |
|---------|--------|---------------------------------------|
|     123 | issue  | Add support for OAuth2 / login (beta) |
|      97 | issue  | Add support for gitlab                |
# Decide which issue to work
$ gibr 123
Generating branch name for issue #123: Add support for OAuth2 / login (beta)
Branch name: issue/123/add-support-for-oauth2-login-beta
✅  Created branch 'issue/123/add-support-for-oauth2-login-beta' from main.
✅  Checked out branch: issue/123/add-support-for-oauth2-login-beta
✅  Pushed branch 'issue/123/add-support-for-oauth2-login-beta' to origin.
```

## 🚀 Quick start
### Installation
```bash
uv pip install gibr
# or
pip install gibr
```
### Initial setup
Run `gibr init` to set up your configuration interactively. This will create a [`.gibrconfig`](#branch-naming-convention) file in your project root with the correct format for your chosen issue tracker.
### Setup git aliases commands (optional)
Run `gibr alias` to set up git alias commands for your conveinence. This essentially allows you to extend the `git` CLI with `gibr` commands. See [alias command](#alias) for more details

### Commands
- [init](#init)
- [alias](#alias)
- [issues](#issues)
- [create](#create)

#### init
`gibr` includes an `init` command to help you create your `.gibrconfig` file. See the following usage example:
```
$ gibr init
Welcome to gibr setup! Let’s get you started 🚀

Which issue tracker do you use?
1. GitHub
2. GitLab
3. Jira
4. Linear (coming soon)
5. Monday.com (coming soon)

Select a number (1, 2, 3, 4, 5) [1]: 1

GitHub selected.

GitHub repository (e.g. user/repo): ytreister/gibr
Environment variable for your GitHub token [GITHUB_TOKEN]:
🎉  Found GitHub token in environment (GITHUB_TOKEN)
.gibrconfig already exists. Overwrite? [y/N]: y
✅  Created .gibrconfig with GitHub settings
You're all set! Try: `gibr issues`
```

#### alias
`gibr` includes a built-in helper that writes git aliases into your global
`~/.gitconfig` for you. Run:

```bash
gibr alias
```

This adds aliases such as `git create` so that instead of using the gibr CLI directly, you can use an extended version of git:

```bash
git create 123
```

The above command is equivalent to using the CLI as follows: `gibr 123` or
`gibr create 123`.

##### Flag order

The flag order when using the `git` alias version is different:

```bash
# ✅ gibr CLI (flags before)
gibr --verbose create 123

# ✅ git alias (flags after)
git create 123 --verbose

# ❌ wrong: flags after gibr CLI
gibr create 123 --verbose 

# ❌ wrong: flags before the alias
git --verbose create 123
```

#### issues
Run `gibr issues` (or `git issues`) to view open issues in the issue tracker you have configured
#### create
Run `gibr 123` (or `gibr create 123` or `git create 123`) to create a branch for the cooresponding issue number.
##### Branch naming convention
`gibr` uses the `branch_name_format` from your `.gibrconfig` to determine the format for the branch.
You can use the following placeholders: `{issuetype}`, `{issue}`, `{title}`.
##### Special case: Jira
For Jira, you can specify a `project_key` in your configuration:
```ini
[jira]
project_key=FOO
```
If you do this, you can choose to either specify the entire issue id or just the numerical portion (i.e. `FOO-123` or `123`
```bash
# List issues
$ gibr issues
| Issue   | Type    | Title       |
|---------|---------|-------------|
| FOO-3   | Subtask | Subtask 2.1 |
| FOO-2   | Story   | Task 2      |
# Create branch for FOO-3
$ gibr 3
Generating branch name for issue FOO-3: Subtask 2.1
Branch name: FOO-3-subtask-2-1
✅  Created branch 'FOO-3-subtask-2-1' from main.
✅  Checked out branch: FOO-3-subtask-2-1
✅  Pushed branch 'FOO-3-subtask-2-1' to origin.
```
### Optional flags
- `--verbose` — enable debug-level logging for a command

## Roadmap
See the [Roadmap](ROADMAP.md) for upcoming features and plans.

## Opensource contributions
See the [Contributions](CONTRIBUTIONS.md) guidelines if you would like to contribute.

## 💬 Feedback welcome!
Found a bug or have a feature request? [Open an issue](https://github.com/ytreister/gibr/issues) or start a discussion.
