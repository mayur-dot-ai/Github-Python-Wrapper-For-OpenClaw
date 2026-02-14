# GitHub Wrapper for OpenClaw

A CLI wrapper around [PyGithub](https://github.com/PyGithub/PyGithub) designed for AI agents running in [OpenClaw](https://openclaw.ai).

## Why This Wrapper?

**Problem:** AI agents need to interact with GitHub, but:
1. **GitHub App authentication is complex** — requires JWT generation, installation tokens, and token refresh
2. **PyGithub is a Python library** — agents calling via shell (`exec`) need a CLI interface  
3. **Consistent output** — agents need predictable JSON responses for parsing

**Solution:** This wrapper:
- Handles GitHub App authentication automatically (preferred for org-level access)
- Falls back to Personal Access Tokens when needed
- Provides a simple CLI interface with JSON output
- Wraps 22 common GitHub operations

## Why Not Use PyGithub Directly?

You can! But for AI agent workflows:

| Direct PyGithub | This Wrapper |
|-----------------|--------------|
| Requires writing Python each time | One-liner CLI calls |
| Manual auth token management | Auto-handles GitHub App auth |
| Raw exceptions | Consistent `{success: true/false}` JSON |
| Full 283 methods (overkill) | 22 curated operations |

If your agent can write Python, use PyGithub directly. If your agent uses shell commands (`exec`), this wrapper is simpler.

## Installation

```bash
# Clone
git clone https://github.com/mayur-dot-ai/github-wrapper-openclaw.git
cd github-wrapper-openclaw

# Install dependency
pip install PyGithub
```

## Authentication

### Option 1: GitHub App (Recommended for Orgs)

```bash
export GITHUB_APP_ID="your-app-id"
export GITHUB_INSTALLATION_ID="your-installation-id"
export GITHUB_APP_PRIVATE_KEY="$(cat /path/to/private-key.pem)"
```

### Option 2: Personal Access Token

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

## Usage

```bash
python github-wrapper.py <action> [args]
```

### Repository Operations
```bash
# List repos in org
python github-wrapper.py repo-list myorg

# Create repo
python github-wrapper.py repo-create myorg new-repo "Description" false

# Delete repo
python github-wrapper.py repo-delete myorg repo-name
```

### File Operations
```bash
# Read file
python github-wrapper.py file-get myorg myrepo README.md

# Create/update file
python github-wrapper.py file-create-or-update myorg myrepo path/to/file.txt "content" "commit message"

# Delete file
python github-wrapper.py file-delete myorg myrepo path/to/file.txt "delete file"
```

### Issue Operations
```bash
# List issues
python github-wrapper.py issue-list myorg myrepo open

# Create issue
python github-wrapper.py issue-create myorg myrepo "Bug: something broke" "Description here"

# Get issue details
python github-wrapper.py issue-get myorg myrepo 42

# Add comment
python github-wrapper.py issue-comment myorg myrepo 42 "This is a comment"

# Update issue state
python github-wrapper.py issue-update myorg myrepo 42 closed
```

### Pull Request Operations
```bash
# List PRs
python github-wrapper.py pr-list myorg myrepo open

# Create PR
python github-wrapper.py pr-create myorg myrepo "Feature: new thing" feature-branch main "PR description"

# Merge PR
python github-wrapper.py pr-merge myorg myrepo 5 squash

# Review PR (APPROVE, REQUEST_CHANGES, COMMENT)
python github-wrapper.py pr-review myorg myrepo 5 APPROVE "LGTM!"

# Comment on PR
python github-wrapper.py pr-comment myorg myrepo 5 "Nice work!"
```

### Branch Operations
```bash
# List branches
python github-wrapper.py branch-list myorg myrepo

# Create branch
python github-wrapper.py branch-create myorg myrepo new-feature main
```

### Other Operations
```bash
# List commits
python github-wrapper.py commit-list myorg myrepo main 10

# Create release
python github-wrapper.py release-create myorg myrepo v1.0.0 "Version 1.0" "Release notes"

# List labels
python github-wrapper.py label-list myorg myrepo

# Create label
python github-wrapper.py label-create myorg myrepo "priority:high" ff0000 "High priority items"
```

## All Available Actions (22)

| Category | Actions |
|----------|---------|
| **Repos** | `repo-create`, `repo-list`, `repo-delete` |
| **Files** | `file-create-or-update`, `file-get`, `file-delete` |
| **Issues** | `issue-create`, `issue-list`, `issue-get`, `issue-update`, `issue-comment` |
| **PRs** | `pr-create`, `pr-list`, `pr-merge`, `pr-review`, `pr-comment` |
| **Branches** | `branch-list`, `branch-create` |
| **Commits** | `commit-list` |
| **Releases** | `release-create` |
| **Labels** | `label-list`, `label-create` |

## Output Format

All commands return JSON:

```json
// Success
{"success": true, "repo": "new-repo", "url": "https://github.com/..."}

// Error
{"success": false, "error": "Not Found"}
```

## Use with OpenClaw

In your OpenClaw agent, call via `exec`:

```
exec python3 /path/to/github-wrapper.py issue-create myorg myrepo "New feature request" "Details..."
```

The wrapper handles authentication from environment variables automatically.

## License

MIT

## Contributing

PRs welcome! This wrapper exposes 22 of PyGithub's 283 methods. If you need more, add them following the existing pattern.