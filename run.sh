#!/usr/bin/env bash
set -e

# LiveLLM - Platform Launcher
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

echo "Starting LiveLLM continuous benchmarking platform..."
echo "Open your browser at: http://127.0.0.1:8000"
./venv/bin/uvicorn livellm.api.main:app --host 127.0.0.1 --port 8000 --reload
