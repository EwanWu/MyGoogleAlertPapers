#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers"
STATE="$ROOT/data/task_state/phase2_regular_chunk01_163_incremental_20260506.json"
LOG="$ROOT/data/logs/phase2_regular_chunk01_163_incremental_20260506_resume.log"
REVIEW_EXPORT="$ROOT/data/exports/review_queue_phase2_regular_chunk01_20260506.jsonl"
DB_PATH="/home/ewan/NewCareer/MyPaperDatabase/mgap_163_incremental_20260506.db"
RESUME_LIMIT=4992

export SQLITE_PATH="$DB_PATH"
STEP="starting"

mkdir -p "$(dirname "$LOG")"
mkdir -p "$(dirname "$STATE")"
mkdir -p "$(dirname "$REVIEW_EXPORT")"

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
  STATUS="$status" STATE="$STATE" DB_PATH="$DB_PATH" REVIEW_EXPORT="$REVIEW_EXPORT" RESUME_LIMIT="$RESUME_LIMIT" python3 - <<'PY'
import json, os, sqlite3, datetime
state_path = os.environ['STATE']
db_path = os.environ['DB_PATH']
review_export = os.environ['REVIEW_EXPORT']
resume_limit = int(os.environ['RESUME_LIMIT'])
status = os.environ['STATUS']
with open(state_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
metrics = {
    'resume_limit': resume_limit,
    'review_export_path': review_export,
    'updated_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
}
with sqlite3.connect(db_path) as conn:
    metrics['merged_proposals_total'] = conn.execute('SELECT COUNT(*) FROM merged_metadata_proposal').fetchone()[0]
    metrics['canonical_papers'] = conn.execute('SELECT COUNT(*) FROM canonical_paper').fetchone()[0]
    metrics['candidate_paper_links'] = conn.execute('SELECT COUNT(*) FROM candidate_paper_link').fetchone()[0]
    review_exists = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='merge_review_queue'").fetchone()[0] > 0
    metrics['review_blocked_total'] = conn.execute('SELECT COUNT(*) FROM merge_review_queue').fetchone()[0] if review_exists else 0
    metrics['need_merge_remaining'] = conn.execute("SELECT COUNT(*) FROM paper_candidate_normalized pcn LEFT JOIN merged_metadata_proposal mmp ON mmp.candidate_id=pcn.candidate_id LEFT JOIN candidate_paper_link cpl ON cpl.candidate_id=pcn.candidate_id WHERE mmp.id IS NULL AND cpl.id IS NULL").fetchone()[0]
    metrics['need_dedup_remaining'] = conn.execute("SELECT COUNT(*) FROM paper_candidate_normalized pcn JOIN merged_metadata_proposal mmp ON mmp.candidate_id=pcn.candidate_id LEFT JOIN candidate_paper_link cpl ON cpl.candidate_id=pcn.candidate_id LEFT JOIN merge_review_queue mrq ON mrq.candidate_id=pcn.candidate_id WHERE cpl.id IS NULL AND mrq.id IS NULL").fetchone()[0]

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
  update_state "failed" "$STEP" "inspect resume log and DB state before retrying chunk01 recovery" || true
  echo "[$(date --iso-8601=seconds)] ERROR during step: $STEP" | tee -a "$LOG"
}
trap on_error ERR

exec > >(tee -a "$LOG") 2>&1

echo "[$(date --iso-8601=seconds)] Phase 2 regular chunk01 resume start"
echo "ROOT=$ROOT"
echo "SQLITE_PATH=$SQLITE_PATH"
echo "RESUME_LIMIT=$RESUME_LIMIT"

STEP="merge-metadata-resume"
update_state "running" "$STEP" "dedup-candidates-resume"
python3 -m mygooglealertpapers.cli merge-metadata --limit "$RESUME_LIMIT"

STEP="dedup-candidates-resume"
update_state "running" "$STEP" "reporting-resume"
python3 -m mygooglealertpapers.cli dedup-candidates --limit "$RESUME_LIMIT"

STEP="reporting-resume"
update_state "running" "$STEP" "phase2 regular chunk01 recovered"
python3 -m mygooglealertpapers.cli report-enrichment
python3 -m mygooglealertpapers.cli report-merge
python3 -m mygooglealertpapers.cli report-dedup
python3 -m mygooglealertpapers.cli report-review-queue
python3 -m mygooglealertpapers.cli report-cost
python3 -m mygooglealertpapers.cli export-review-queue --output "$REVIEW_EXPORT"

write_metrics "completed"
STEP="phase2-regular-chunk01-recovered"
update_state "completed" "$STEP" "decide whether to continue regular chunk02 with corrected chunk-boundary handling"
echo "[$(date --iso-8601=seconds)] Phase 2 regular chunk01 resume completed"
