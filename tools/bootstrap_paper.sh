#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export LUMEN_VENV="${LUMEN_VENV:-$root/.venv}"
bash "$root/tools/bootstrap.sh"
"$LUMEN_VENV/bin/python" -m pip install -r "$root/requirements-paper.txt"
"$LUMEN_VENV/bin/yowasp-yosys" --version
