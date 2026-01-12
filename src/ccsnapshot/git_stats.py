"""Git statistics collection for CC Snapshot."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from git import Repo
from git.exc import InvalidGitRepositoryError


@dataclass
class CommitInfo:
    """Information about a single commit."""
    timestamp: datetime
    files_changed: list[str]
    message: str


def get_repo(repo_path: Optional[str] = None) -> Repo:
    """Get the git repository at the given path or current directory."""
    path = Path(repo_path) if repo_path else Path.cwd()
    try:
        return Repo(path, search_parent_directories=True)
    except InvalidGitRepositoryError:
        raise ValueError(f"No git repository found at {path}")


def get_commits_in_window(repo_path: Optional[str] = None, days: int = 7) -> list[CommitInfo]:
    """Fetch all commits from the last N days."""
    repo = get_repo(repo_path)
    cutoff = datetime.now() - timedelta(days=days)
    commits = []

    for commit in repo.iter_commits():
        commit_time = datetime.fromtimestamp(commit.committed_date)
        if commit_time < cutoff:
            break

        # Get files changed in this commit
        files = []
        if commit.parents:
            diff = commit.parents[0].diff(commit)
            files = [d.a_path or d.b_path for d in diff if d.a_path or d.b_path]
        else:
            # Initial commit - get all files
            files = [item.path for item in commit.tree.traverse() if item.type == 'blob']

        commits.append(CommitInfo(
            timestamp=commit_time,
            files_changed=files,
            message=commit.message.strip()
        ))

    return commits


def get_all_commits(repo_path: Optional[str] = None) -> list[CommitInfo]:
    """Fetch all commits in the repository."""
    repo = get_repo(repo_path)
    commits = []

    for commit in repo.iter_commits():
        commit_time = datetime.fromtimestamp(commit.committed_date)

        # Get files changed in this commit
        files = []
        if commit.parents:
            diff = commit.parents[0].diff(commit)
            files = [d.a_path or d.b_path for d in diff if d.a_path or d.b_path]
        else:
            files = [item.path for item in commit.tree.traverse() if item.type == 'blob']

        commits.append(CommitInfo(
            timestamp=commit_time,
            files_changed=files,
            message=commit.message.strip()
        ))

    return commits


def get_streak(commits: list[CommitInfo]) -> int:
    """
    Count consecutive days with at least one commit.

    Streak stays active if you committed today OR yesterday,
    so users don't lose their streak overnight.
    """
    if not commits:
        return 0

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    commit_dates = set(c.timestamp.date() for c in commits)

    # Start counting from today if committed today, else from yesterday
    if today in commit_dates:
        current_date = today
    elif yesterday in commit_dates:
        current_date = yesterday
    else:
        return 0

    streak = 0
    while current_date in commit_dates:
        streak += 1
        current_date -= timedelta(days=1)

    return streak


def get_files_changed(commits: list[CommitInfo]) -> int:
    """Count unique files changed across all commits."""
    all_files = set()
    for commit in commits:
        all_files.update(commit.files_changed)
    return len(all_files)


def get_commits_by_day(commits: list[CommitInfo], days: int = 7) -> dict[str, list[CommitInfo]]:
    """Group commits by date for the last N days."""
    today = datetime.now().date()
    result = {}

    for i in range(days):
        day = today - timedelta(days=i)
        day_str = day.isoformat()
        result[day_str] = []

    for commit in commits:
        day_str = commit.timestamp.date().isoformat()
        if day_str in result:
            result[day_str].append(commit)

    return result


def get_first_commit_date(repo_path: Optional[str] = None) -> Optional[datetime]:
    """Get the date of the first commit in the repository."""
    repo = get_repo(repo_path)

    try:
        # Get all commits and find the oldest one
        first_commit = None
        for commit in repo.iter_commits():
            first_commit = commit

        if first_commit:
            return datetime.fromtimestamp(first_commit.committed_date)
    except Exception:
        pass

    return None


def get_project_info(repo_path: Optional[str] = None) -> dict:
    """Get project name and author info."""
    repo = get_repo(repo_path)

    # Project name from repo directory
    project_name = Path(repo.working_dir).name

    # Author from most recent commit
    author_name = "Unknown"
    try:
        for commit in repo.iter_commits(max_count=1):
            author_name = commit.author.name
            break
    except Exception:
        pass

    return {
        "project_name": project_name,
        "author_name": author_name,
    }
