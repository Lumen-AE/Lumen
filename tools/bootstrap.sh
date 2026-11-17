#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
for command in python3 make g++ verilator; do
  command -v "$command" >/dev/null || { echo "Missing prerequisite: $command" >&2; exit 2; }
done
venv="${LUMEN_VENV:-$root/.venv}"
python3 -m venv "$venv"
"$venv/bin/python" -m pip install 'setuptools>=77' wheel -r "$root/requirements.txt"
"$venv/bin/python" -m pip install --no-build-isolation --no-deps -e "$root"
PYTHONPATH="$root/src" "$venv/bin/python" -B -m lumen preflight
