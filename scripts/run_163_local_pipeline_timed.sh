#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

INPUT_JSONL="${1:-data/raw_mail_exports/163_scholar_local/scholar_body_fetch_multisample19.jsonl}"
SQLITE_PATH_VALUE="${2:-/tmp/mgap_163_local_multisample.db}"
TIMING_JSON="${3:-data/raw_mail_exports/163_scholar_local/timing/local_pipeline_timing.json}"
INIT_DB="${INIT_DB:-1}"
IMPORT_LIMIT="${IMPORT_LIMIT:-50}"
PARSE_LIMIT="${PARSE_LIMIT:-200}"
NORMALIZE_LIMIT="${NORMALIZE_LIMIT:-500}"

mkdir -p "$(dirname "$TIMING_JSON")"
rm -f "$TIMING_JSON"

export PYTHONPATH="${PYTHONPATH:-src}"
export SQLITE_PATH="$SQLITE_PATH_VALUE"

json_escape() {
  python3 - <<'PY' "$1"
import json, sys
print(json.dumps(sys.argv[1], ensure_ascii=False))
PY
}

run_stage() {
  local label="$1"
  shift
  local started_at ended_at elapsed rc
  started_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  local start_epoch
  start_epoch="$(python3 - <<'PY'
import time
print(time.perf_counter())
PY
)"
  set +e
  "$@"
  rc=$?
  set -e
  local end_epoch
  end_epoch="$(python3 - <<'PY'
import time
print(time.perf_counter())
PY
)"
  ended_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  elapsed="$(python3 - <<'PY' "$start_epoch" "$end_epoch"
import sys
print(f"{float(sys.argv[2]) - float(sys.argv[1]):.3f}")
PY
)"
  STAGE_ROWS+=("{\"label\":$(json_escape "$label"),\"started_at\":$(json_escape "$started_at"),\"completed_at\":$(json_escape "$ended_at"),\"elapsed_seconds\":$elapsed,\"exit_code\":$rc}")
  if [[ $rc -ne 0 ]]; then
    echo "Stage failed: $label (exit=$rc)" >&2
    return $rc
  fi
}

STARTED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
RUN_START_EPOCH="$(python3 - <<'PY'
import time
print(time.perf_counter())
PY
)"
STAGE_ROWS=()

if [[ "$INIT_DB" == "1" ]]; then
  rm -f "$SQLITE_PATH"
  run_stage init-db python3 -m mygooglealertpapers.cli init-db
fi
run_stage import-local-bodies python3 -m mygooglealertpapers.cli import-local-bodies --input "$INPUT_JSONL" --limit "$IMPORT_LIMIT"
run_stage parse-mails python3 -m mygooglealertpapers.cli parse-mails --limit "$PARSE_LIMIT"
run_stage normalize-candidates python3 -m mygooglealertpapers.cli normalize-candidates --limit "$NORMALIZE_LIMIT"
run_stage report-batch python3 -m mygooglealertpapers.cli report-batch
run_stage report-normalization python3 -m mygooglealertpapers.cli report-normalization

RUN_END_EPOCH="$(python3 - <<'PY'
import time
print(time.perf_counter())
PY
)"
COMPLETED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
ELAPSED_SECONDS="$(python3 - <<'PY' "$RUN_START_EPOCH" "$RUN_END_EPOCH"
import sys
print(f"{float(sys.argv[2]) - float(sys.argv[1]):.3f}")
PY
)"

{
  printf '{\n'
  printf '  "started_at": %s,\n' "$(json_escape "$STARTED_AT")"
  printf '  "completed_at": %s,\n' "$(json_escape "$COMPLETED_AT")"
  printf '  "elapsed_seconds": %s,\n' "$ELAPSED_SECONDS"
  printf '  "input_jsonl": %s,\n' "$(json_escape "$INPUT_JSONL")"
  printf '  "sqlite_path": %s,\n' "$(json_escape "$SQLITE_PATH")"
  printf '  "init_db": %s,\n' "$(json_escape "$INIT_DB")"
  printf '  "import_limit": %s,\n' "$IMPORT_LIMIT"
  printf '  "parse_limit": %s,\n' "$PARSE_LIMIT"
  printf '  "normalize_limit": %s,\n' "$NORMALIZE_LIMIT"
  printf '  "stages": [\n'
  for i in "${!STAGE_ROWS[@]}"; do
    if [[ $i -gt 0 ]]; then
      printf ',\n'
    fi
    printf '    %s' "${STAGE_ROWS[$i]}"
  done
  printf '\n  ]\n'
  printf '}\n'
} > "$TIMING_JSON"

echo "Pipeline timing JSON: $TIMING_JSON"
echo "Pipeline elapsed_seconds: $ELAPSED_SECONDS"
