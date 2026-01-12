"""Threads sharing utilities for CC Snapshot."""

import subprocess
import sys
from urllib.parse import quote

from .render import SnapshotMetrics
from .time_stats import format_duration


def generate_caption(metrics: SnapshotMetrics) -> str:
    """Generate a Threads-ready caption for the snapshot."""
    if metrics.project_name:
        header = f"Day {metrics.day_number} of building {metrics.project_name}"
    else:
        header = f"Day {metrics.day_number} of building with Claude Code"

    lines = [
        header,
        "",
        f"Streak: {metrics.streak}",
        f"Total build time: {format_duration(metrics.total_minutes)}",
        f"Files changed: {metrics.files_changed}",
        "",
        "#BuildInPublic #ClaudeCode",
    ]
    return "\n".join(lines)


def get_threads_url(caption: str) -> str:
    """Generate Threads intent URL with prefilled caption."""
    encoded_text = quote(caption)
    return f"https://www.threads.net/intent/post?text={encoded_text}"


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to clipboard.

    Returns True if successful, False otherwise.
    """
    if sys.platform == "darwin":
        # macOS
        try:
            process = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=text)
            return process.returncode == 0
        except Exception:
            return False
    elif sys.platform == "win32":
        # Windows
        try:
            process = subprocess.Popen(
                ["clip"],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=text)
            return process.returncode == 0
        except Exception:
            return False
    else:
        # Linux - try xclip
        try:
            process = subprocess.Popen(
                ["xclip", "-selection", "clipboard"],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=text)
            return process.returncode == 0
        except Exception:
            return False


def save_caption(caption: str, output_path: str) -> None:
    """Save caption to a text file."""
    with open(output_path, "w") as f:
        f.write(caption)
