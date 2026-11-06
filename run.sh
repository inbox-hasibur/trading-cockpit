#!/usr/bin/env bash
cd "$(dirname "$0")"
if [ -f ".venv/Scripts/python.exe" ]; then
    .venv/Scripts/python.exe run.py "$@"
elif [ -f ".venv/bin/python" ]; then
    .venv/bin/python run.py "$@"
else
    python3 run.py "$@" 2>/dev/null || python run.py "$@"
fi
