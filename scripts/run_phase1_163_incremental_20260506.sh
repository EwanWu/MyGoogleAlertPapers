#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers"
STATE="$ROOT/data/task_state/phase1_163_incremental_20260506.json"
LOG="$ROOT/data/logs/phase1_163_incremental_20260506.log"
INPUT_JSONL="$ROOT/data/raw_mail_exports/163_scholar_local/scholar_body_fetch_20260424_full_reconciled.jsonl"
DB_PATH="/home/ewan/NewCareer/MyPaperDatabase/mgap_163_incremental_20260506.db"

export SQLITE_PATH="$DB_PATH"
STEP="starting"

mkdir -p "$(dirname "$LOG")"
mkdir -p "$(dirname "$STATE")"
mkdir -p "$(dirname "$DB_PATH")"

update_state() {
  local status="$1"
  local current_step="$2"
  local next_step="$3"
  STATUS="$status" CURRENT_STEP="$current_step" NEXT_STEP="$next_step" STATE="$STATE" python3 - <<'PY'
import json, os, datetime
state_path = os.environ['STATE']
status = os.environ['STATUS']
current_step = os.environ['CURRENT_STEP']
next_step = os.environ['NEXT_STEP']
with open(state_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
data['status'] = status
data['current_step'] = current_step
data['next_step'] = next_step
data['last_check_time'] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
with open(state_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write('\n')
PY
}

on_error() {
  update_state "failed" "$STEP" "inspect $LOG and recover from the last finished Phase 1 sub-step" || true
  echo "[$(date --iso-8601=seconds)] ERROR during step: $STEP" | tee -a "$LOG"
}
trap on_error ERR

exec > >(tee -a "$LOG") 2>&1

echo "[$(date --iso-8601=seconds)] Phase 1 start"
echo "ROOT=$ROOT"
echo "SQLITE_PATH=$SQLITE_PATH"
echo "INPUT_JSONL=$INPUT_JSONL"

STEP="validate-local-bodies"
update_state "running" "$STEP" "init-db"
python3 -m mygooglealertpapers.cli validate-local-bodies --input "$INPUT_JSONL"

STEP="init-db"
update_state "running" "$STEP" "import-local-bodies"
python3 -m mygooglealertpapers.cli init-db

STEP="import-local-bodies"
update_state "running" "$STEP" "parse-mails"
python3 -m mygooglealertpapers.cli import-local-bodies --input "$INPUT_JSONL" --limit 20000

STEP="parse-mails"
update_state "running" "$STEP" "normalize-candidates"
python3 -m mygooglealertpapers.cli parse-mails --limit 10000

STEP="normalize-candidates"
update_state "running" "$STEP" "report-batch + report-normalization"
python3 -m mygooglealertpapers.cli normalize-candidates --limit 100000

STEP="report-phase1-results"
update_state "running" "$STEP" "phase1 complete"
python3 -m mygooglealertpapers.cli report-batch
python3 -m mygooglealertpapers.cli report-normalization

STEP="phase1-complete"
update_state "completed" "$STEP" "start chunked resolve/enrich/merge/dedup Phase 2"
echo "[$(date --iso-8601=seconds)] Phase 1 completed"
