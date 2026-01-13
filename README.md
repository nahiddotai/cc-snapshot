# CC Snapshot

Generate shareable progress cards for your coding projects. Built for builders who share on Threads.

## Run in 60 Seconds (macOS)

```bash
git clone <repo-url>
cd cc-snapshot
./run_mac.sh
```

That's it. The app opens at `http://localhost:8501`.

## Manual Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
streamlit run app.py
```

## How It Works

1. Run the app from your project directory (must be a git repo)
2. Click **Generate Snapshot**
3. Download the PNG and share on Threads

The app analyzes your git history to calculate:
- **Day count**: Days since first commit
- **Streak**: Consecutive days with commits
- **Build time**: Time between first and latest commit
- **Files changed**: Unique files modified this week

## Configuration

Settings are saved to `ccsnapshot.yaml`:

```yaml
builder_name: "Your Name"      # Shown in the UI
session_gap_minutes: 45        # Session detection threshold
window_days: 7                 # Days for weekly stats
title: ""                      # Custom title (optional)
```

You can also edit Builder Name directly in the app sidebar.

## Output

Generated files are saved to `ccsnapshot_out/`:
- `YYYY-MM-DD.png` - The snapshot image (1080x1350)
- `YYYY-MM-DD.txt` - Caption text for Threads

## Privacy

**CC Snapshot is 100% local.**

- Runs entirely on your machine
- Reads only your local git history
- No data is uploaded anywhere
- No accounts or API keys required
- Output stays in your `ccsnapshot_out/` folder

Your code and commit history never leave your computer.

## Requirements

- Python 3.9+
- macOS, Linux, or Windows
- A git repository with at least one commit

## Troubleshooting

**"No git repository found"**
- Run the app from inside a git repo directory

**Streak shows 0**
- Commit today or yesterday to start/continue your streak

**Build time shows 0**
- You need at least 2 commits to measure elapsed time
