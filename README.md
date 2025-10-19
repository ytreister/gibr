[![Tests](https://github.com/ytreister/gibr/actions/workflows/test.yml/badge.svg)](https://github.com/ytreister/gibr/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/ytreister/gibr/branch/main/graph/badge.svg)](https://codecov.io/gh/ytreister/gibr)

# gibr

A CLI that generates Git branch names from issue trackers (currently GitHub) and
creates + pushes the branch to `origin`.

## Quick start
### Installation
```bash
pip install gibr
```
### Usage (primary use case)
Issue #123 "Add support for OAuth2 / login (beta)"
```bash
$ gibr 123
Generating branch name for issue #123: Add support for OAuth2 / login (beta)
Branch name: issue/123/add-support-for-oauth2-login-beta
✅  Created branch 'issue/123/add-support-for-oauth2-login-beta' from main.
✅  Checked out branch: issue/123/add-support-for-oauth2-login-beta
✅  Pushed branch 'issue/123/add-support-for-oauth2-login-beta' to origin.
```
 
## Listing issues with `gibr issues`

You can list open issues from your configured tracker with:

```bash
gibr issues
```

This prints a short list of matching/open issues (id, title, type) so you can
pick which issue to use when creating a branch.

## Adding convenient Git aliases with `gibr alias`

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


### Flag order

Short rule:

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

## Optional flags
- `--verbose` — enable debug-level logging for a command

## Configuration (`.gibrconfig`)

Example `.gibrconfig` (place in repo root or parent directory):

```ini
[DEFAULT]
branch_name_format = {issuetype}/{issue}-{title}

[issue-tracker]
name = github

[github]
repo = owner/repo
token = $GITHUB_TOKEN
```

Notes:
- Environment variables in config values are expanded.
- `branch_name_format` uses these placeholders: `{issuetype}`, `{issue}`, `{title}`.
