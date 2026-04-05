#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

echo "Setup complete."
echo "Activate environment with: source .venv/bin/activate"
echo "Run website with: python app.py"
echo "Run tests with: python -m pytest -q"
