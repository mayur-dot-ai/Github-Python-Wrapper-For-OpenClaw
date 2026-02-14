#!/usr/bin/env python3
"""
GitHub wrapper for OpenClaw agent
Connects to GitHub org via App credentials and provides CLI-style operations

Usage: python github-wrapper.py <action> [args]

Actions:
  repo-create <org> <name> [description] [private]  - Create a repository
  repo-list <org>                                    - List org repositories
  repo-delete <org> <repo>                           - Delete a repository
  
  file-create-or-update <org> <repo> <path> <content> <message>  - Create/update file
  file-get <org> <repo> <path> [ref]                              - Read file contents
  file-delete <org> <repo> <path> <message> [ref]                 - Delete a file
  
  issue-create <org> <repo> <title> [body]           - Create an issue
  issue-list <org> <repo> [state]                    - List issues (open/closed/all)
  issue-get <org> <repo> <issue_number>              - Get single issue details
  issue-update <org> <repo> <issue_number> [state]   - Update an issue
  issue-comment <org> <repo> <issue_number> <body>   - Add comment to issue
  
  pr-create <org> <repo> <title> <head> [base] [body]  - Create pull request
  pr-list <org> <repo> [state]                          - List pull requests
  pr-merge <org> <repo> <pr_number> [merge_method]     - Merge pull request
  pr-review <org> <repo> <pr_number> <event> [body]    - Create PR review
  pr-comment <org> <repo> <pr_number> <body>            - Add comment to PR
  
  branch-list <org> <repo>                           - List branches
  branch-create <org> <repo> <branch_name> [from_ref] - Create branch
  
  commit-list <org> <repo> [ref] [limit]             - List recent commits
  
  release-create <org> <repo> <tag> <name> [body] [draft] [prerelease]  - Create release
  
  label-list <org> <repo>                            - List labels
  label-create <org> <repo> <name> [color] [description]  - Create label
"""

import json
import sys
import os
import base64
from github import Github, Auth, GithubException

def get_github():
    """Connect to GitHub via App credentials"""
    # Option 1: GitHub App (preferred for org-level access)
    app_id = os.getenv('GITHUB_APP_ID')
    private_key = os.getenv('GITHUB_APP_PRIVATE_KEY')
    installation_id = os.getenv('GITHUB_INSTALLATION_ID')
    
    if app_id and private_key and installation_id:
        try:
            # Create AppAuth first, then get installation auth
            app_auth = Auth.AppAuth(int(app_id), private_key)
            auth = app_auth.get_installation_auth(int(installation_id))
            g = Github(auth=auth)
            return g
        except Exception as e:
            return None
    
    # Fallback: Personal Access Token
    token = os.getenv('GITHUB_TOKEN')
    if token:
        g = Github(auth=Auth.Token(token))
        return g
    
    return None

def get_repo(org, repo_name):
    """Helper: Get repository object"""
    g = get_github()
    org_obj = g.get_organization(org)
    return org_obj.get_repo(repo_name)

# ========== REPOSITORY OPERATIONS ==========

def repo_create(org, repo_name, description="", private=False, auto_init=True):
    """Create a new repository"""
    try:
        g = get_github()
        org_obj = g.get_organization(org)
        
        repo = org_obj.create_repo(
            name=repo_name,
            description=description,
            private=private,
            auto_init=auto_init
        )
        
        return {
            'success': True,
            'repo': repo_name,
            'url': repo.html_url,
            'clone_url': repo.clone_url
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

def repo_list(org):
    """List repositories in org"""
    try:
        g = get_github()
        org_obj = g.get_organization(org)
        repos = list(org_obj.get_repos())
        
        return {
            'success': True,
            'repos': [
                {
                    'name': r.name,
                    'url': r.html_url,
                    'description': r.description,
                    'private': r.private,
                    'language': r.language
                }
                for r in repos
            ]
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

def repo_delete(org, repo_name):
    """Delete a repository"""
    try:
        repo = get_repo(org, repo_name)
        repo.delete()
        
        return {'success': True, 'message': f'Deleted {repo_name}'}
    except GithubException as e:
        return {'success': False, 'error': str(e)}

# ========== FILE OPERATIONS ==========

def file_create_or_update(org, repo_name, file_path, content, message):
    """Create or update a file in a repository"""
    try:
        repo = get_repo(org, repo_name)
        
        try:
            # Try to get existing file
            existing = repo.get_contents(file_path)
            repo.update_file(
                path=file_path,
                message=message,
                content=content,
                sha=existing.sha
            )
            action = 'updated'
        except:
            # File doesn't exist, create it
            repo.create_file(
                path=file_path,
                message=message,
                content=content
            )
            action = 'created'
        
        return {
            'success': True,
            'file': file_path,
            'action': action,
            'url': repo.html_url + f'/blob/main/{file_path}'
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

def file_get(org, repo_name, file_path, ref=None):
    """Read file contents from repository"""
    try:
        repo = get_repo(org, repo_name)
        
        if ref:
            contents = repo.get_contents(file_path, ref=ref)
        else:
            contents = repo.get_contents(file_path)
        
        # Handle directory case
        if isinstance(contents, list):
            return {
                'success': True,
                'type': 'directory',
                'path': file_path,
                'files': [
                    {
                        'name': c.name,
                        'path': c.path,
                        'type': c.type,
                        'size': c.size
                    }
                    for c in contents
                ]
            }
        
        # Decode file content
        if contents.encoding == 'base64':
            decoded_content = base64.b64decode(contents.content).decode('utf-8')
        else:
            decoded_content = contents.content
        
        return {
            'success': True,
            'type': 'file',
            'path': contents.path,
            'sha': contents.sha,
            'size': contents.size,
            'content': decoded_content,
            'url': contents.html_url
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

def file_delete(org, repo_name, file_path, message, ref=None):
    """Delete a file from repository"""
    try:
        repo = get_repo(org, repo_name)
        
        if ref:
            contents = repo.get_contents(file_path, ref=ref)
        else:
            contents = repo.get_contents(file_path)
        
        kwargs = {
            'path': file_path,
            'message': message,
            'sha': contents.sha
        }
        if ref:
            kwargs['branch'] = ref
            
        repo.delete_file(**kwargs)
        
        return {
            'success': True,
            'file': file_path,
            'action': 'deleted'
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

# ========== ISSUE OPERATIONS ==========

def issue_create(org, repo_name, title, body="", labels=None):
    """Create a GitHub issue"""
    try:
        repo = get_repo(org, repo_name)
        
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=labels or []
        )
        
        return {
            'success': True,
            'issue_number': issue.number,
            'url': issue.html_url,
            'state': issue.state
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

def issue_list(org, repo_name, state='open'):
    """List issues in a repository"""
    try:
        repo = get_repo(org, repo_name)
        issues = list(repo.get_issues(state=state))
        
        return {
            'success': True,
            'issues': [
                {
                    'number': i.number,
                    'title': i.title,
                    'state': i.state,
                    'url': i.html_url,
                    'labels': [l.name for l in i.labels],
                    'body': i.body[:200] if i.body else ''
                }
                for i in issues
            ]
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

def issue_get(org, repo_name, issue_number):
    """Get single issue details"""
    try:
        repo = get_repo(org, repo_name)
        issue = repo.get_issue(issue_number)
        
        return {
            'success': True,
            'number': issue.number,
            'title': issue.title,
            'state': issue.state,
            'url': issue.html_url,
            'body': issue.body,
            'labels': [l.name for l in issue.labels],
            'assignees': [a.login for a in issue.assignees],
            'created_at': issue.created_at.isoformat() if issue.created_at else None,
            'updated_at': issue.updated_at.isoformat() if issue.updated_at else None,
            'closed_at': issue.closed_at.isoformat() if issue.closed_at else None,
            'comments_count': issue.comments,
            'user': issue.user.login if issue.user else None
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

def issue_update(org, repo_name, issue_number, state=None, body=None, labels=None):
    """Update an issue"""
    try:
        repo = get_repo(org, repo_name)
        issue = repo.get_issue(issue_number)
        
        if state:
            issue.edit(state=state)
        if body is not None:
            issue.edit(body=body)
        if labels:
            issue.set_labels(*labels)
        
        return {
            'success': True,
            'issue_number': issue.number,
            'state': issue.state
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

def issue_comment(org, repo_name, issue_number, body):
    """Add comment to issue"""
    try:
        repo = get_repo(org, repo_name)
        issue = repo.get_issue(issue_number)
        
        comment = issue.create_comment(body)
        
        return {
            'success': True,
            'comment_id': comment.id,
            'issue_number': issue_number,
            'url': comment.html_url
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

# ========== PULL REQUEST OPERATIONS ==========

def pr_create(org, repo_name, title, head_branch, base_branch='main', body=""):
    """Create a pull request"""
    try:
        repo = get_repo(org, repo_name)
        
        pr = repo.create_pull(
            title=title,
            body=body,
            head=head_branch,
            base=base_branch
        )
        
        return {
            'success': True,
            'pr_number': pr.number,
            'url': pr.html_url,
            'state': pr.state
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

def pr_list(org, repo_name, state='open'):
    """List pull requests"""
    try:
        repo = get_repo(org, repo_name)
        prs = list(repo.get_pulls(state=state))
        
        return {
            'success': True,
            'prs': [
                {
                    'number': p.number,
                    'title': p.title,
                    'state': p.state,
                    'url': p.html_url,
                    'head': p.head.ref,
                    'base': p.base.ref
                }
                for p in prs
            ]
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

def pr_merge(org, repo_name, pr_number, merge_method='squash'):
    """Merge a pull request"""
    try:
        repo = get_repo(org, repo_name)
        pr = repo.get_pull(pr_number)
        
        pr.merge(merge_method=merge_method)
        
        return {
            'success': True,
            'pr_number': pr_number,
            'merged': True
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

def pr_review(org, repo_name, pr_number, event, body=""):
    """Create a PR review
    
    Args:
        event: APPROVE, REQUEST_CHANGES, or COMMENT
        body: Review comment (required for REQUEST_CHANGES and COMMENT)
    """
    try:
        repo = get_repo(org, repo_name)
        pr = repo.get_pull(pr_number)
        
        review = pr.create_review(body=body, event=event.upper())
        
        return {
            'success': True,
            'review_id': review.id,
            'pr_number': pr_number,
            'state': review.state,
            'url': review.html_url
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

def pr_comment(org, repo_name, pr_number, body):
    """Add comment to pull request (issue comment on PR)"""
    try:
        repo = get_repo(org, repo_name)
        # PRs are also issues in GitHub's API
        issue = repo.get_issue(pr_number)
        
        comment = issue.create_comment(body)
        
        return {
            'success': True,
            'comment_id': comment.id,
            'pr_number': pr_number,
            'url': comment.html_url
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

# ========== BRANCH OPERATIONS ==========

def branch_list(org, repo_name):
    """List branches in repository"""
    try:
        repo = get_repo(org, repo_name)
        branches = list(repo.get_branches())
        
        default_branch = repo.default_branch
        
        return {
            'success': True,
            'default_branch': default_branch,
            'branches': [
                {
                    'name': b.name,
                    'sha': b.commit.sha,
                    'protected': b.protected,
                    'is_default': b.name == default_branch
                }
                for b in branches
            ]
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

def branch_create(org, repo_name, branch_name, from_ref=None):
    """Create a new branch
    
    Args:
        from_ref: Source branch/ref to branch from (defaults to repo's default branch)
    """
    try:
        repo = get_repo(org, repo_name)
        
        # Get the SHA to branch from
        if from_ref:
            source = repo.get_branch(from_ref)
        else:
            source = repo.get_branch(repo.default_branch)
        
        sha = source.commit.sha
        
        # Create the reference (branch)
        ref = repo.create_git_ref(
            ref=f'refs/heads/{branch_name}',
            sha=sha
        )
        
        return {
            'success': True,
            'branch': branch_name,
            'sha': sha,
            'from_ref': from_ref or repo.default_branch,
            'ref': ref.ref
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

# ========== COMMIT OPERATIONS ==========

def commit_list(org, repo_name, ref=None, limit=10):
    """List recent commits"""
    try:
        repo = get_repo(org, repo_name)
        
        kwargs = {}
        if ref:
            kwargs['sha'] = ref
            
        commits = list(repo.get_commits(**kwargs))[:limit]
        
        return {
            'success': True,
            'ref': ref or repo.default_branch,
            'commits': [
                {
                    'sha': c.sha,
                    'short_sha': c.sha[:7],
                    'message': c.commit.message.split('\n')[0],  # First line only
                    'author': c.commit.author.name if c.commit.author else None,
                    'date': c.commit.author.date.isoformat() if c.commit.author and c.commit.author.date else None,
                    'url': c.html_url
                }
                for c in commits
            ]
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

# ========== RELEASE OPERATIONS ==========

def release_create(org, repo_name, tag, name, body="", draft=False, prerelease=False):
    """Create a release"""
    try:
        repo = get_repo(org, repo_name)
        
        release = repo.create_git_release(
            tag=tag,
            name=name,
            message=body,
            draft=draft,
            prerelease=prerelease
        )
        
        return {
            'success': True,
            'tag': tag,
            'name': name,
            'id': release.id,
            'url': release.html_url,
            'draft': release.draft,
            'prerelease': release.prerelease
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

# ========== LABEL OPERATIONS ==========

def label_list(org, repo_name):
    """List labels in repository"""
    try:
        repo = get_repo(org, repo_name)
        labels = list(repo.get_labels())
        
        return {
            'success': True,
            'labels': [
                {
                    'name': l.name,
                    'color': l.color,
                    'description': l.description
                }
                for l in labels
            ]
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

def label_create(org, repo_name, name, color="0366d6", description=""):
    """Create a label
    
    Args:
        color: Hex color without # (default: blue)
    """
    try:
        repo = get_repo(org, repo_name)
        
        # Remove # if provided
        color = color.lstrip('#')
        
        label = repo.create_label(
            name=name,
            color=color,
            description=description
        )
        
        return {
            'success': True,
            'name': label.name,
            'color': label.color,
            'description': label.description
        }
    except GithubException as e:
        return {'success': False, 'error': str(e)}

# ========== CLI MAIN ==========

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action in ['help', '-h', '--help']:
        print(__doc__)
        sys.exit(0)
    
    try:
        # Repository operations
        if action == 'repo-create':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            description = sys.argv[4] if len(sys.argv) > 4 else ""
            private = sys.argv[5].lower() == 'true' if len(sys.argv) > 5 else False
            result = repo_create(org, repo_name, description, private)
        
        elif action == 'repo-list':
            org = sys.argv[2]
            result = repo_list(org)
        
        elif action == 'repo-delete':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            result = repo_delete(org, repo_name)
        
        # File operations
        elif action == 'file-create-or-update':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            file_path = sys.argv[4]
            content = sys.argv[5]
            message = sys.argv[6]
            result = file_create_or_update(org, repo_name, file_path, content, message)
        
        elif action == 'file-get':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            file_path = sys.argv[4]
            ref = sys.argv[5] if len(sys.argv) > 5 else None
            result = file_get(org, repo_name, file_path, ref)
        
        elif action == 'file-delete':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            file_path = sys.argv[4]
            message = sys.argv[5]
            ref = sys.argv[6] if len(sys.argv) > 6 else None
            result = file_delete(org, repo_name, file_path, message, ref)
        
        # Issue operations
        elif action == 'issue-create':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            title = sys.argv[4]
            body = sys.argv[5] if len(sys.argv) > 5 else ""
            result = issue_create(org, repo_name, title, body)
        
        elif action == 'issue-list':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            state = sys.argv[4] if len(sys.argv) > 4 else 'open'
            result = issue_list(org, repo_name, state)
        
        elif action == 'issue-get':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            issue_number = int(sys.argv[4])
            result = issue_get(org, repo_name, issue_number)
        
        elif action == 'issue-update':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            issue_number = int(sys.argv[4])
            state = sys.argv[5] if len(sys.argv) > 5 else None
            result = issue_update(org, repo_name, issue_number, state)
        
        elif action == 'issue-comment':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            issue_number = int(sys.argv[4])
            body = sys.argv[5]
            result = issue_comment(org, repo_name, issue_number, body)
        
        # PR operations
        elif action == 'pr-create':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            title = sys.argv[4]
            head_branch = sys.argv[5]
            base_branch = sys.argv[6] if len(sys.argv) > 6 else 'main'
            body = sys.argv[7] if len(sys.argv) > 7 else ""
            result = pr_create(org, repo_name, title, head_branch, base_branch, body)
        
        elif action == 'pr-list':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            state = sys.argv[4] if len(sys.argv) > 4 else 'open'
            result = pr_list(org, repo_name, state)
        
        elif action == 'pr-merge':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            pr_number = int(sys.argv[4])
            merge_method = sys.argv[5] if len(sys.argv) > 5 else 'squash'
            result = pr_merge(org, repo_name, pr_number, merge_method)
        
        elif action == 'pr-review':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            pr_number = int(sys.argv[4])
            event = sys.argv[5]  # APPROVE, REQUEST_CHANGES, COMMENT
            body = sys.argv[6] if len(sys.argv) > 6 else ""
            result = pr_review(org, repo_name, pr_number, event, body)
        
        elif action == 'pr-comment':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            pr_number = int(sys.argv[4])
            body = sys.argv[5]
            result = pr_comment(org, repo_name, pr_number, body)
        
        # Branch operations
        elif action == 'branch-list':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            result = branch_list(org, repo_name)
        
        elif action == 'branch-create':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            branch_name = sys.argv[4]
            from_ref = sys.argv[5] if len(sys.argv) > 5 else None
            result = branch_create(org, repo_name, branch_name, from_ref)
        
        # Commit operations
        elif action == 'commit-list':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            ref = sys.argv[4] if len(sys.argv) > 4 else None
            limit = int(sys.argv[5]) if len(sys.argv) > 5 else 10
            result = commit_list(org, repo_name, ref, limit)
        
        # Release operations
        elif action == 'release-create':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            tag = sys.argv[4]
            name = sys.argv[5]
            body = sys.argv[6] if len(sys.argv) > 6 else ""
            draft = sys.argv[7].lower() == 'true' if len(sys.argv) > 7 else False
            prerelease = sys.argv[8].lower() == 'true' if len(sys.argv) > 8 else False
            result = release_create(org, repo_name, tag, name, body, draft, prerelease)
        
        # Label operations
        elif action == 'label-list':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            result = label_list(org, repo_name)
        
        elif action == 'label-create':
            org = sys.argv[2]
            repo_name = sys.argv[3]
            name = sys.argv[4]
            color = sys.argv[5] if len(sys.argv) > 5 else "0366d6"
            description = sys.argv[6] if len(sys.argv) > 6 else ""
            result = label_create(org, repo_name, name, color, description)
        
        else:
            result = {'error': f'Unknown action: {action}. Run with "help" for usage.'}
        
        print(json.dumps(result))
    
    except IndexError as e:
        print(json.dumps({'success': False, 'error': f'Missing arguments. Run with "help" for usage.'}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({'success': False, 'error': str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    main()