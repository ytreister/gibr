[![Tests](https://github.com/ytreister/gibr/actions/workflows/test.yml/badge.svg)](https://github.com/ytreister/gibr/actions/workflows/test.yml)
[![Coverage](https://codecov.io/gh/ytreister/gibr/branch/main/graph/badge.svg)](https://codecov.io/gh/ytreister/gibr)
[![PyPI version](https://img.shields.io/pypi/v/gibr.svg)](https://pypi.org/project/gibr/)
[![Downloads](https://img.shields.io/pypi/dm/gibr.svg)](https://pypi.org/project/gibr/)
[![Python versions](https://img.shields.io/pypi/pyversions/gibr.svg)](https://pypi.org/project/gibr/)
[![License](https://img.shields.io/github/license/ytreister/gibr.svg)](https://github.com/ytreister/gibr/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/ytreister/gibr.svg)](https://github.com/ytreister/gibr/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/ytreister/gibr.svg)](https://github.com/ytreister/gibr/issues)


# gibr
> 🧩 **A smarter CLI for creating Git branches.**

`gibr` connects your Git workflow to your issue tracker — instantly creating consistent, descriptive branches.
Fully configurable, and ready for any tracker or team setup.

Currently supporting integration with:  

[![GitHub](https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=white)](https://github.com)
[![GitLab](https://img.shields.io/badge/GitLab-330F63?logo=gitlab&logoColor=white)](https://gitlab.com)
[![Jira](https://img.shields.io/badge/Jira-0052CC?logo=jira&logoColor=white)](https://www.atlassian.com/software/jira)
[![Azure](https://img.shields.io/badge/Azure-269AF2)](https://dev.azure.com)
[![Linear](https://img.shields.io/badge/Linear-5E6AD2?logo=linear&logoColor=white)](https://linear.app)
## Usage
```
# List open issues
$ gibr issues
|   Issue | Type   | Title                                 | Assignee   |
|---------|--------|---------------------------------------|------------|
|     123 | issue  | Add support for OAuth2 / login (beta) | ytreister  |
|      97 | issue  | Add support for gitlab                |            |
# Decide which issue to work
$ gibr 123
Generating branch name for issue #123: Add support for OAuth2 / login (beta)
Branch name: ytreister/issue/123/add-support-for-oauth2-login-beta
✅  Created branch 'ytreister/issue/123/add-support-for-oauth2-login-beta' from main.
✅  Checked out branch: ytreister/issue/123/add-support-for-oauth2-login-beta
✅  Pushed branch 'ytreister/issue/123/add-support-for-oauth2-login-beta' to origin.
```

## 🚀 Quick start
### Installation
Install the base package
```bash
pip install gibr
```
or if you use `uv`
```
uv pip install gibr
```
#### 🧩 Optional dependencies
`gibr` supports multiple issue trackers, but you only need to install the dependencies for the ones you actually use.

Each tracker’s client library is an optional extra.

| Tracker | Extra name | Install command (can prepend with `uv` if you use it) |
|---------|------------|------------------------------------------------------ |
| GitHub  | `github`   | `pip install gibr[github]`                            |
| GitLab  | `gitlab`   | `pip install gibr[gitlab]`                            |
| Jira    | `jira`     | `pip install gibr[jira]`                              |
| Azure   | `azure`    | `pip install gibr[azure]`                             |
| Linear  | built-in   | N/A                                                   |

*Note:* You can also install multiple trackers at once, for example: 
```bash
pip install gibr[github,jira]
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
1. AzureDevOps
2. GitHub
3. GitLab
4. Jira
5. Linear
6. Monday.com (coming soon)

Select a number (1, 2, 3, 4, 5, 6) [1]: 2

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
You can use the following placeholders:  
- `{issuetype}`
- `{issue}`
- `{title}`
- `{assignee}` (Note: If issue does not have an assignee and your branch name format contains assignee, you will not be able to create the branch)
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
| Issue   | Type    | Title       | Assignee   |
|---------|---------|-------------|------------|
| FOO-3   | Subtask | Subtask 2.1 | ytreister  |
| FOO-2   | Story   | Task 2      |            |
# Create branch for FOO-3
$ gibr 3
Generating branch name for issue FOO-3: Subtask 2.1
Branch name: FOO-3-subtask-2-1
✅  Created branch 'FOO-3-subtask-2-1' from main.
✅  Checked out branch: FOO-3-subtask-2-1
✅  Pushed branch 'FOO-3-subtask-2-1' to origin.
```
##### Special case: Azure
Azure DevOps allows teams to customize their work item states based on their workflow. By default, this integration assumes the following states represent closed/completed work items: 
  - Done
  - Removed
  - Closed
If your Azure DevOps project uses different state names or a custom workflow, you can configure the closed_states parameter to match your setup. 
[azure]
closed_states: ['Done', 'Removed', 'Closed']
Work items matching any of the configured closed_states will be excluded from the list of active issues.

### Optional flags
- `--verbose` — enable debug-level logging for a command

## Roadmap
See the [Roadmap](ROADMAP.md) for upcoming features and plans.

## Opensource contributions
See the [Contributing](CONTRIBUTING.md) guidelines if you would like to contribute.

## 💬 Feedback welcome!
Found a bug or have a feature request? [Open an issue](https://github.com/ytreister/gibr/issues) or start a discussion.  
If you find it useful, consider starring ⭐️ the repo — it really helps visibility!
