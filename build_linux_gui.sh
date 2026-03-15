#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-build.txt
python3 -m PyInstaller --noconfirm --clean word_cloud_gui.spec

printf '\nBuild finished. Output:\n%s\n' "$(pwd)/dist/word-cloud-gui"
