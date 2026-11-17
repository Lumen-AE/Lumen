#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
venv="${LUMEN_VENV:-$root/.venv}"
if [[ ! -x "$venv/bin/python" ]]; then
  echo "Python environment missing. Run bash tools/bootstrap.sh or set LUMEN_VENV." >&2
  exit 2
fi
source "$venv/bin/activate"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$root/src"
exec python -B -m lumen "$@"
