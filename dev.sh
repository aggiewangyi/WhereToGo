#!/usr/bin/env bash
# 一键启动：后端 FastAPI (8000) + 前端 Vite (3000，/api 代理到 8000)
# 依赖：Poetry、Node.js/npm；首次请在后端目录执行 poetry install，在前端目录执行 npm install
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="${ROOT}/backend"
FRONTEND="${ROOT}/frontend"

require_dir() {
  if [[ ! -d "$1" ]]; then
    echo "error: directory not found: $1" >&2
    exit 1
  fi
}

require_dir "$BACKEND"
require_dir "$FRONTEND"

if ! command -v poetry &>/dev/null; then
  echo "error: poetry not found (install: https://python-poetry.org/docs/#installation)" >&2
  exit 1
fi
if ! command -v npm &>/dev/null; then
  echo "error: npm not found" >&2
  exit 1
fi

cleanup() {
  local pids
  pids="$(jobs -p 2>/dev/null || true)"
  if [[ -n "${pids}" ]]; then
    # shellcheck disable=SC2086
    kill ${pids} 2>/dev/null || true
    wait 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "==> Starting backend: http://127.0.0.1:8000  (cwd: ${BACKEND})"
(
  cd "$BACKEND"
  poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &

echo "==> Starting frontend: http://127.0.0.1:3000  (cwd: ${FRONTEND})"
(
  cd "$FRONTEND"
  npm run dev -- --host 0.0.0.0 --port 3000
) &

echo "==> Press Ctrl+C to stop both."
# 等所有后台任务结束（任一崩溃时另一进程仍会跑，可 Ctrl+C 一并清理）
wait
