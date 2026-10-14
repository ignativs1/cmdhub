#!/usr/bin/env bash
# CmdHub Linux/macOS Startup Script

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

export CMDHUB_PORT=8080
export CMDHUB_HOST=0.0.0.0

python3 app.py
