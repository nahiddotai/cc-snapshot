# CC Snapshot

Generate Threads-ready progress cards for Claude Code builders.

## Quick Start

```bash
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate it
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

# 3. Install dependencies
pip install -e .

# 4. Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Configuration

Edit `ccsnapshot.yaml` to customize:

```yaml
# When did you start this project?
project_start_date: "2025-01-01"

# Minutes of inactivity before a new coding session
session_gap_minutes: 45

# How many days to include in stats
window_days: 7

# Title shown on the card
title: "CC Snapshot"
```

## How It Works

1. Click **Generate Snapshot**
2. The app analyzes your git history from the last 7 days
3. It calculates:
   - **Streak**: Consecutive days with commits
   - **Build Time**: Estimated coding time (based on commit sessions)
   - **Files Changed**: Unique files modified
4. A 1080x1350 PNG is generated and saved to `ccsnapshot_out/`
5. Use the buttons to:
   - **Download PNG** - Save locally
   - **Copy Caption** - Copy pre-written caption
   - **Open Threads** - Opens Threads composer with caption

## Output Files

Generated files are saved to `ccsnapshot_out/`:
- `YYYY-MM-DD.png` - The snapshot image
- `YYYY-MM-DD.txt` - The caption text

## Troubleshooting

**No git repository found**
- Make sure you run the app from a directory with a `.git` folder

**Streak shows 0**
- You need at least one commit today for the streak to count

**Build time seems off**
- Build time is estimated from commit timestamps
- Sessions are separated by 45+ minutes of inactivity
- Single commits count as 15 minutes
