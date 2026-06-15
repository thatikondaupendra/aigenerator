#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

cd frontend
npm install

echo "Install complete. Start backend with scripts/start_backend.sh and frontend with scripts/start_frontend.sh"
