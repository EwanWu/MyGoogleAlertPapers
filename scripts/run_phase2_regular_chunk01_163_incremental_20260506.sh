#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers"
STATE="$ROOT/data/task_state/phase2_regular_chunk01_163_incremental_20260506.json"
LOG="$ROOT/data/logs/phase2_regular_chunk01_163_incremental_20260506.log"
REVIEW_EXPORT="$ROOT/data/exports/review_queue_phase2_regular_chunk01_20260506.jsonl"
DB_PATH="/home/ewan/NewCareer/MyPaperDatabase/mgap_163_incremental_20260506.db"
CHUNK_LIMIT=5000

export SQLITE_PATH="$DB_PATH"
STEP="starting"

mkdir -p "$(dirname "$LOG")"
mkdir -p "$(dirname "$STATE")"
mkdir -p "$(dirname "$REVIEW_EXPORT")"
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

write_metrics() {
  local status="$1"
  STATUS="$status" STATE="$STATE" DB_PATH="$DB_PATH" REVIEW_EXPORT="$REVIEW_EXPORT" CHUNK_LIMIT="$CHUNK_LIMIT" python3 - <<'PY'
import json, os, sqlite3, datetime
state_path = os.environ['STATE']
db_path = os.environ['DB_PATH']
review_export = os.environ['REVIEW_EXPORT']
chunk_limit = int(os.environ['CHUNK_LIMIT'])
status = os.environ['STATUS']
with open(state_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
metrics = {
    'chunk_limit': chunk_limit,
    'review_export_path': review_export,
    'updated_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
}
with sqlite3.connect(db_path) as conn:
    metrics['paper_candidates'] = conn.execute('SELECT COUNT(*) FROM paper_candidate').fetchone()[0]
    metrics['normalized_candidates'] = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized').fetchone()[0]
    metrics['canonical_papers'] = conn.execute('SELECT COUNT(*) FROM canonical_paper').fetchone()[0]
    metrics['candidate_paper_links'] = conn.execute('SELECT COUNT(*) FROM candidate_paper_link').fetchone()[0]
    review_exists = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='merge_review_queue'").fetchone()[0] > 0
    metrics['review_blocked_total'] = conn.execute('SELECT COUNT(*) FROM merge_review_queue').fetchone()[0] if review_exists else 0
    notes_row = conn.execute("SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1").fetchone()
    if notes_row and notes_row[0]:
        try:
            notes = json.loads(notes_row[0])
        except Exception:
            notes = None
        metrics['latest_enrich_notes'] = notes
    else:
        metrics['latest_enrich_notes'] = None

data['latest_observed_metrics'] = metrics
data['status'] = status
data['last_check_time'] = metrics['updated_at']
with open(state_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write('\n')
PY
}

on_error() {
  write_metrics "failed" || true
  update_state "failed" "$STEP" "inspect $LOG and the state file before retrying regular chunk01" || true
  echo "[$(date --iso-8601=seconds)] ERROR during step: $STEP" | tee -a "$LOG"
}
trap on_error ERR

exec > >(tee -a "$LOG") 2>&1

echo "[$(date --iso-8601=seconds)] Phase 2 regular chunk01 start"
echo "ROOT=$ROOT"
echo "SQLITE_PATH=$SQLITE_PATH"
echo "CHUNK_LIMIT=$CHUNK_LIMIT"

STEP="resolve-candidates"
update_state "running" "$STEP" "enrich-candidates"
python3 -m mygooglealertpapers.cli resolve-candidates --limit "$CHUNK_LIMIT"

STEP="enrich-candidates"
update_state "running" "$STEP" "merge-metadata"
python3 -m mygooglealertpapers.cli enrich-candidates --limit "$CHUNK_LIMIT"

STEP="merge-metadata"
update_state "running" "$STEP" "dedup-candidates"
python3 -m mygooglealertpapers.cli merge-metadata --limit "$CHUNK_LIMIT"

STEP="dedup-candidates"
update_state "running" "$STEP" "reporting"
python3 -m mygooglealertpapers.cli dedup-candidates --limit "$CHUNK_LIMIT"

STEP="reporting"
update_state "running" "$STEP" "phase2 regular chunk01 complete"
python3 -m mygooglealertpapers.cli report-enrichment
python3 -m mygooglealertpapers.cli report-merge
python3 -m mygooglealertpapers.cli report-dedup
python3 -m mygooglealertpapers.cli report-review-queue
python3 -m mygooglealertpapers.cli report-cost
python3 -m mygooglealertpapers.cli export-review-queue --output "$REVIEW_EXPORT"

write_metrics "completed"
STEP="phase2-regular-chunk01-complete"
update_state "completed" "$STEP" "decide whether to continue regular chunk02 at the same size"
echo "[$(date --iso-8601=seconds)] Phase 2 regular chunk01 completed"
