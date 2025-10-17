# gibr

A CLI that generates Git branch names from issue trackers (currently GitHub) and
creates + pushes the branch to `origin`.

## Quick start
### Installation
```bash
pip install gibr
```
### Usage
```bash
gibr 123
```

The command above will:
1. Load `.gibrconfig` from the current directory or a parent directory.
2. Use the configured issue tracker to fetch issue `#123`.
3. Generate a branch name using the `DEFAULT.branch_name_format` (see config example).
4. Create the branch locally and push it to `origin`.

## Verbose logging

Add `--verbose` to any command to enable debug-level logging:

```bash
gibr 123 --verbose
# or
gibr --verbose 123
```

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
