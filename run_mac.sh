#!/bin/bash
# CC Snapshot - Quick Start Script for macOS

set -e

echo "CC Snapshot Setup"
echo "================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required. Install from python.org or via Homebrew."
    exit 1
fi

# Create venv if needed
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install deps
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Create default config if missing
if [ ! -f "ccsnapshot.yaml" ]; then
    echo "Creating default config..."
    cat > ccsnapshot.yaml << 'EOF'
# CC Snapshot Configuration

# Your display name (shown on snapshot)
builder_name: ""

# Minutes of inactivity before a new coding session
session_gap_minutes: 45

# How many days to include in weekly stats
window_days: 7

# Title shown on the snapshot card (leave empty to use "Building [project]")
title: ""
EOF
fi

# Run app
echo ""
echo "Starting CC Snapshot..."
echo "Opening http://localhost:8501"
echo ""
streamlit run app.py
