"""Time and session statistics for CC Snapshot."""

from datetime import datetime, timedelta

from .git_stats import CommitInfo


# Default time assumed for a single-commit session (minutes)
SINGLE_COMMIT_MINUTES = 15

# Padding added before first commit and after last commit in a session (minutes)
SESSION_PADDING_MINUTES = 10


def group_into_sessions(
    commits: list[CommitInfo],
    gap_minutes: int = 45
) -> list[list[CommitInfo]]:
    """
    Group commits into coding sessions based on time gaps.

    A new session starts when there's more than gap_minutes between commits.
    Commits should be sorted newest-first (as returned by git).
    """
    if not commits:
        return []

    # Sort by timestamp (oldest first for grouping)
    sorted_commits = sorted(commits, key=lambda c: c.timestamp)

    sessions = []
    current_session = [sorted_commits[0]]

    for commit in sorted_commits[1:]:
        prev_commit = current_session[-1]
        gap = (commit.timestamp - prev_commit.timestamp).total_seconds() / 60

        if gap > gap_minutes:
            sessions.append(current_session)
            current_session = [commit]
        else:
            current_session.append(commit)

    sessions.append(current_session)
    return sessions


def calculate_session_duration(session: list[CommitInfo]) -> int:
    """
    Calculate the duration of a session in minutes.

    - Single commit: assume SINGLE_COMMIT_MINUTES
    - Multiple commits: time span + padding on each end
    """
    if not session:
        return 0

    if len(session) == 1:
        return SINGLE_COMMIT_MINUTES

    # Sort by time
    sorted_session = sorted(session, key=lambda c: c.timestamp)
    first = sorted_session[0].timestamp
    last = sorted_session[-1].timestamp

    span_minutes = (last - first).total_seconds() / 60
    return int(span_minutes + (SESSION_PADDING_MINUTES * 2))


def get_total_build_time(
    commits: list[CommitInfo],
    gap_minutes: int = 45
) -> int:
    """Calculate total build time in minutes across all sessions."""
    sessions = group_into_sessions(commits, gap_minutes)
    return sum(calculate_session_duration(s) for s in sessions)


def get_daily_minutes(
    commits: list[CommitInfo],
    gap_minutes: int = 45,
    days: int = 7
) -> dict[str, int]:
    """
    Get build time per day for the last N days.

    Returns a dict mapping date strings (YYYY-MM-DD) to minutes.
    """
    today = datetime.now().date()

    # Initialize all days with 0
    result = {}
    for i in range(days):
        day = today - timedelta(days=i)
        result[day.isoformat()] = 0

    # Group commits by day
    commits_by_day: dict[str, list[CommitInfo]] = {}
    for commit in commits:
        day_str = commit.timestamp.date().isoformat()
        if day_str not in commits_by_day:
            commits_by_day[day_str] = []
        commits_by_day[day_str].append(commit)

    # Calculate session time for each day
    for day_str, day_commits in commits_by_day.items():
        if day_str in result:
            sessions = group_into_sessions(day_commits, gap_minutes)
            result[day_str] = sum(calculate_session_duration(s) for s in sessions)

    return result


def format_duration(minutes: int) -> str:
    """Format minutes as human-readable duration."""
    if minutes < 60:
        return f"{minutes}m"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return f"{hours}h"

    return f"{hours}h {remaining_minutes}m"


def get_project_duration(commits: list[CommitInfo]) -> int:
    """
    Calculate total project duration in minutes.

    Returns elapsed time between first and most recent commit.
    """
    if not commits or len(commits) < 2:
        return 0

    # Sort by timestamp
    sorted_commits = sorted(commits, key=lambda c: c.timestamp)
    first = sorted_commits[0].timestamp
    last = sorted_commits[-1].timestamp

    elapsed = (last - first).total_seconds() / 60
    return int(elapsed)
