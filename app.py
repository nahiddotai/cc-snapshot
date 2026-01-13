"""CC Snapshot - Streamlit Web App."""

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st
import yaml

from src.ccsnapshot.git_stats import (
    get_all_commits,
    get_commits_in_window,
    get_files_changed,
    get_first_commit_date,
    get_project_info,
    get_streak,
)
from src.ccsnapshot.render import (
    SnapshotMetrics,
    get_image_bytes,
    render_snapshot,
)
from src.ccsnapshot.share_threads import (
    copy_to_clipboard,
    generate_caption,
    get_threads_url,
    save_caption,
)
from src.ccsnapshot.time_stats import get_daily_minutes, get_project_duration

# Page config
st.set_page_config(
    page_title="CC Snapshot",
    page_icon="📸",
    layout="centered",
)

# Paths
CONFIG_PATH = Path("ccsnapshot.yaml")
OUTPUT_DIR = Path("ccsnapshot_out")


def load_config() -> dict:
    """Load configuration from ccsnapshot.yaml."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def save_config(config: dict) -> None:
    """Save configuration to ccsnapshot.yaml."""
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_day_number() -> int:
    """Get day number from first commit."""
    first_commit = get_first_commit_date(".")
    if first_commit:
        start_date = first_commit.date()
        return (datetime.now().date() - start_date).days + 1
    return 1


def open_in_finder(path: Path) -> bool:
    """Open file in Finder (macOS only)."""
    if sys.platform == "darwin":
        try:
            subprocess.run(["open", "-R", str(path)], check=True)
            return True
        except Exception:
            pass
    return False


def generate_snapshot_data(config: dict, project_name: str, builder_name: str) -> tuple:
    """Generate snapshot and return (image, caption, metrics, png_path)."""
    recent_commits = get_commits_in_window(".", days=config.get("window_days", 7))
    all_commits = get_all_commits(".")
    gap_minutes = config.get("session_gap_minutes", 45)

    metrics = SnapshotMetrics(
        streak=get_streak(recent_commits),
        total_minutes=get_project_duration(all_commits),
        files_changed=get_files_changed(recent_commits),
        daily_minutes=get_daily_minutes(recent_commits, gap_minutes, 7),
        day_number=get_day_number(),
        title=config.get("title", ""),
        project_name=project_name,
    )

    img = render_snapshot(metrics)
    caption = generate_caption(metrics)

    # Save files
    OUTPUT_DIR.mkdir(exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    png_path = OUTPUT_DIR / f"{today_str}.png"
    txt_path = OUTPUT_DIR / f"{today_str}.txt"

    img.save(png_path, "PNG")
    save_caption(caption, str(txt_path))

    return img, caption, metrics, png_path


def main():
    """Main app entry point."""
    config = load_config()
    project_info = get_project_info(".")

    # Sidebar settings
    with st.sidebar:
        st.header("Settings")

        # Builder name (editable)
        default_builder = config.get("builder_name") or project_info.get("author_name", "")
        builder_name = st.text_input(
            "Builder Name",
            value=default_builder,
            help="Your name shown on the snapshot",
        )

        # Save if changed
        if builder_name != config.get("builder_name"):
            config["builder_name"] = builder_name
            save_config(config)

        st.caption(f"Project: **{project_info['project_name']}**")

        st.markdown("---")
        st.caption("Settings auto-save to ccsnapshot.yaml")

    # Main content
    if "snapshot_bytes" in st.session_state:
        # === RESULT VIEW ===
        st.markdown(
            "<h1 style='text-align: center; margin-bottom: 0;'>Your Snapshot</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='text-align: center; color: #888; margin-top: 0;'>{project_info['project_name']}</p>",
            unsafe_allow_html=True,
        )

        # Preview image
        st.image(st.session_state["snapshot_bytes"], use_container_width=True)

        # Action buttons row 1
        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                label="Download PNG",
                data=st.session_state["snapshot_bytes"],
                file_name=f"cc-snapshot-{datetime.now().strftime('%Y-%m-%d')}.png",
                mime="image/png",
                use_container_width=True,
            )

        with col2:
            threads_url = get_threads_url(st.session_state["caption"])
            st.link_button("Open Threads", url=threads_url, use_container_width=True)

        # Caption section
        st.markdown("**Caption**")
        st.code(st.session_state["caption"], language=None)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Copy Caption", use_container_width=True):
                if copy_to_clipboard(st.session_state["caption"]):
                    st.toast("Copied to clipboard!")
                else:
                    st.toast("Select and copy from above")

        with col2:
            if sys.platform == "darwin":
                if st.button("Open in Finder", use_container_width=True):
                    if "png_path" in st.session_state:
                        open_in_finder(Path(st.session_state["png_path"]))

        # Reset
        st.markdown("---")
        if st.button("Generate New Snapshot", use_container_width=True):
            del st.session_state["snapshot_bytes"]
            del st.session_state["caption"]
            if "png_path" in st.session_state:
                del st.session_state["png_path"]
            st.rerun()

    else:
        # === INITIAL VIEW ===
        st.markdown(
            "<h1 style='text-align: center;'>CC Snapshot</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align: center; color: #888; font-size: 1.1em;'>Share your build progress on Threads</p>",
            unsafe_allow_html=True,
        )

        # Trust signals
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Project", project_info["project_name"])
        with col2:
            display_name = builder_name or project_info.get("author_name", "Builder")
            st.metric("Builder", display_name)

        # Day counter
        day_number = get_day_number()
        st.markdown(
            f"<p style='text-align: center; font-size: 1.5em; margin: 1.5em 0;'>Day <strong>{day_number}</strong> of building</p>",
            unsafe_allow_html=True,
        )

        # Generate button
        st.markdown("---")
        if st.button("Generate Snapshot", type="primary", use_container_width=True):
            with st.spinner("Analyzing your commits..."):
                try:
                    img, caption, metrics, png_path = generate_snapshot_data(
                        config,
                        project_info["project_name"],
                        builder_name,
                    )
                    st.session_state["snapshot_bytes"] = get_image_bytes(img)
                    st.session_state["caption"] = caption
                    st.session_state["png_path"] = str(png_path)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
