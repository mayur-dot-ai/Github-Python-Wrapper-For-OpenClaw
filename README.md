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

## Quick Start for OpenClaw Users

### Step 1: Get GitHub Credentials

You have two options:

**Option A: GitHub App (Recommended for orgs)**
1. Go to your GitHub org → Settings → Developer Settings → GitHub Apps
2. Create a new GitHub App with these permissions:
   - Repository: Read & Write (contents, issues, pull requests)
   - Organization: Read (members) if needed
3. Install the app on your org
4. Note down: `App ID`, `Installation ID`, and download the private key `.pem` file

**Option B: Personal Access Token (Simpler, for personal repos)**
1. Go to GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens
2. Create a token with repo access
3. Copy the token (starts with `ghp_`)

### Step 2: Install the Wrapper

Copy this prompt to your OpenClaw agent:

```
Install the GitHub wrapper for me:

1. Create the directory and download:
   mkdir -p ~/github-mcp
   curl -o ~/github-mcp/github-wrapper.py https://raw.githubusercontent.com/mayur-dot-ai/Github-Python-Wrapper-For-OpenClaw/main/github-wrapper.py
   chmod +x ~/github-mcp/github-wrapper.py

2. Install PyGithub:
   pip install PyGithub

3. Set up credentials in ~/.bashrc (replace with your values):

   # For GitHub App:
   export GITHUB_APP_ID="your-app-id"
   export GITHUB_INSTALLATION_ID="your-installation-id"  
   export GITHUB_APP_PRIVATE_KEY="$(cat ~/.openclaw/github-app-key.pem)"

   # OR for Personal Access Token:
   export GITHUB_TOKEN="ghp_your_token_here"

4. Reload: source ~/.bashrc

5. Test it:
   python3 ~/github-mcp/github-wrapper.py repo-list your-org-or-username
```

### Step 3: Store Your Private Key (GitHub App only)

If using a GitHub App, save your `.pem` file:

```bash
# Copy your downloaded private key to OpenClaw
mkdir -p ~/.openclaw
# Paste the key contents:
cat > ~/.openclaw/github-app-key.pem << 'EOF'
-----BEGIN RSA PRIVATE KEY-----
(your key content here)
-----END RSA PRIVATE KEY-----
EOF
chmod 600 ~/.openclaw/github-app-key.pem
```

### Step 4: Add to Your Agent's Memory

Add this to your `TOOLS.md` or `MEMORY.md`:

```markdown
## GitHub Wrapper

**Location:** `~/github-mcp/github-wrapper.py`
**Auth:** GitHub App (App ID: XXXX, Installation ID: XXXX)
**Org:** your-org-name

### Usage
python3 ~/github-mcp/github-wrapper.py <action> [args]

### Common Actions
- `repo-list <org>` — List repos
- `repo-create <org> <name> "<desc>" private` — Create private repo
- `file-create-or-update <org> <repo> <path> "<content>" "<msg>"` — Push file
- `issue-create <org> <repo> "<title>" "<body>"` — Create issue
- `issue-comment <org> <repo> <num> "<body>"` — Comment on issue
```

---

## Why Not Use PyGithub Directly?

You can! But for AI agent workflows:

| Direct PyGithub | This Wrapper |
|-----------------|--------------|
| Requires writing Python each time | One-liner CLI calls |
| Manual auth token management | Auto-handles GitHub App auth |
| Raw exceptions | Consistent `{success: true/false}` JSON |
| Full 283 methods (overkill) | 22 curated operations |

If your agent can write Python, use PyGithub directly. If your agent uses shell commands (`exec`), this wrapper is simpler.

---

## Authentication Details

### Option 1: GitHub App (Recommended for Orgs)

```bash
export GITHUB_APP_ID="your-app-id"
export GITHUB_INSTALLATION_ID="your-installation-id"
export GITHUB_APP_PRIVATE_KEY="$(cat /path/to/private-key.pem)"
```

**Where to find these:**
- `GITHUB_APP_ID`: GitHub App settings page → App ID
- `GITHUB_INSTALLATION_ID`: Org settings → Installed GitHub Apps → Click app → URL contains installation ID
- Private key: Downloaded when you created the app (or generate a new one in app settings)

### Option 2: Personal Access Token

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

---

## Usage Reference

```bash
python github-wrapper.py <action> [args]
```

### Repository Operations
```bash
# List repos in org
python github-wrapper.py repo-list myorg

# Create repo (use 'private' or 'true' for private)
python github-wrapper.py repo-create myorg new-repo "Description" private

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

## License

MIT

## Contributing

PRs welcome! This wrapper exposes 22 of PyGithub's 283 methods. If you need more, add them following the existing pattern.
