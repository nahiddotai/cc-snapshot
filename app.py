"""CC Snapshot - Streamlit Web App."""

from datetime import datetime
from pathlib import Path

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

# Output directory
OUTPUT_DIR = Path("ccsnapshot_out")


def load_config() -> dict:
    """Load configuration from ccsnapshot.yaml."""
    config_path = Path("ccsnapshot.yaml")
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def get_day_number() -> int:
    """Get day number from first commit."""
    first_commit = get_first_commit_date(".")
    if first_commit:
        start_date = first_commit.date()
        return (datetime.now().date() - start_date).days + 1
    return 1


def generate_snapshot(config: dict, project_name: str) -> tuple:
    """Generate snapshot and return (image, caption, metrics)."""
    # Get recent commits for streak and weekly chart
    recent_commits = get_commits_in_window(".", days=config.get("window_days", 7))

    # Get ALL commits for total build time (entire project)
    all_commits = get_all_commits(".")
    gap_minutes = config.get("session_gap_minutes", 45)

    metrics = SnapshotMetrics(
        streak=get_streak(recent_commits),
        total_minutes=get_project_duration(all_commits),
        files_changed=get_files_changed(recent_commits),
        daily_minutes=get_daily_minutes(recent_commits, gap_minutes, 7),
        day_number=get_day_number(),
        title=config.get("title", "CC Snapshot"),
        project_name=project_name,
    )

    img = render_snapshot(metrics)
    caption = generate_caption(metrics)

    # Save files
    OUTPUT_DIR.mkdir(exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    img.save(OUTPUT_DIR / f"{today_str}.png", "PNG")
    save_caption(caption, str(OUTPUT_DIR / f"{today_str}.txt"))

    return img, caption, metrics


def main():
    """Main app entry point."""
    config = load_config()
    project_info = get_project_info(".")

    # Check if we have a generated snapshot
    if "snapshot_bytes" in st.session_state:
        # === RESULT VIEW ===
        st.markdown(
            f"<h1 style='text-align: center; margin-bottom: 0;'>Your Snapshot</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='text-align: center; color: #888; margin-top: 0;'>{project_info['project_name']}</p>",
            unsafe_allow_html=True,
        )

        # Preview image
        st.image(st.session_state["snapshot_bytes"], use_container_width=True)

        # Action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button(
                label="Download",
                data=st.session_state["snapshot_bytes"],
                file_name=f"cc-snapshot-{datetime.now().strftime('%Y-%m-%d')}.png",
                mime="image/png",
                use_container_width=True,
            )

        with col2:
            if st.button("Copy Caption", use_container_width=True):
                if copy_to_clipboard(st.session_state["caption"]):
                    st.toast("Copied!")
                else:
                    st.toast("Copy from below")

        with col3:
            threads_url = get_threads_url(st.session_state["caption"])
            st.link_button("Share on Threads", url=threads_url, use_container_width=True)

        # Caption (collapsible)
        with st.expander("Caption"):
            st.code(st.session_state["caption"], language=None)

        # Reset button
        st.markdown("---")
        if st.button("Generate New Snapshot", use_container_width=True):
            del st.session_state["snapshot_bytes"]
            del st.session_state["caption"]
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

        # Trust signals - show connected project
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Project", project_info["project_name"])
        with col2:
            st.metric("Builder", project_info["author_name"])

        # Day counter preview
        day_number = get_day_number()
        st.markdown(
            f"<p style='text-align: center; font-size: 1.5em; margin: 1.5em 0;'>Day <strong>{day_number}</strong> of building</p>",
            unsafe_allow_html=True,
        )

        # Primary CTA
        st.markdown("---")
        if st.button("Generate Snapshot", type="primary", use_container_width=True):
            with st.spinner("Analyzing your commits..."):
                try:
                    img, caption, metrics = generate_snapshot(config, project_info["project_name"])
                    st.session_state["snapshot_bytes"] = get_image_bytes(img)
                    st.session_state["caption"] = caption
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
