#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers"
STATE="$ROOT/data/task_state/phase2_regular_chunk04_163_incremental_20260506.json"
LOG="$ROOT/data/logs/phase2_regular_chunk04_fastpass_163_incremental_20260506.log"
REVIEW_EXPORT="$ROOT/data/exports/review_queue_phase2_regular_chunk04_20260506.jsonl"
DB_PATH="/home/ewan/NewCareer/MyPaperDatabase/mgap_163_incremental_20260506.db"
POLICY_PROFILE="$ROOT/config/policy_profiles/openalex_batching_identifier_fastpath.yaml"
CHUNK_LIMIT=5000

export SQLITE_PATH="$DB_PATH"
export MGAP_POLICY_PROFILE="$POLICY_PROFILE"
STEP="starting"

mkdir -p "$(dirname "$LOG")"
mkdir -p "$(dirname "$STATE")"
mkdir -p "$(dirname "$REVIEW_EXPORT")"

update_state() {
  local status="$1"
  local current_step="$2"
  local next_step="$3"
  STATUS="$status" CURRENT_STEP="$current_step" NEXT_STEP="$next_step" STATE="$STATE" POLICY_PROFILE="$POLICY_PROFILE" python3 - <<'PY'
import json, os, datetime
state_path = os.environ['STATE']
status = os.environ['STATUS']
current_step = os.environ['CURRENT_STEP']
next_step = os.environ['NEXT_STEP']
policy_profile = os.environ['POLICY_PROFILE']
with open(state_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
data['status'] = status
data['current_step'] = current_step
data['next_step'] = next_step
data['last_check_time'] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
data['active_policy_profile'] = policy_profile
with open(state_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write('\n')
PY
}

write_metrics() {
  local status="$1"
  STATUS="$status" STATE="$STATE" DB_PATH="$DB_PATH" REVIEW_EXPORT="$REVIEW_EXPORT" CHUNK_LIMIT="$CHUNK_LIMIT" POLICY_PROFILE="$POLICY_PROFILE" python3 - <<'PY'
import json, os, sqlite3, datetime
state_path = os.environ['STATE']
db_path = os.environ['DB_PATH']
review_export = os.environ['REVIEW_EXPORT']
chunk_limit = int(os.environ['CHUNK_LIMIT'])
status = os.environ['STATUS']
policy_profile = os.environ['POLICY_PROFILE']
with open(state_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
metrics = {
    'chunk_limit': chunk_limit,
    'review_export_path': review_export,
    'policy_profile': policy_profile,
    'updated_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
}
with sqlite3.connect(db_path) as conn:
    metrics['paper_candidates'] = conn.execute('SELECT COUNT(*) FROM paper_candidate').fetchone()[0]
    metrics['normalized_candidates'] = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized').fetchone()[0]
    metrics['canonical_papers'] = conn.execute('SELECT COUNT(*) FROM canonical_paper').fetchone()[0]
    metrics['candidate_paper_links'] = conn.execute('SELECT COUNT(*) FROM candidate_paper_link').fetchone()[0]
    metrics['review_blocked_total'] = conn.execute('SELECT COUNT(*) FROM merge_review_queue').fetchone()[0]
    metrics['need_merge_remaining'] = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized pcn LEFT JOIN merged_metadata_proposal mmp ON mmp.candidate_id = pcn.candidate_id LEFT JOIN candidate_paper_link cpl ON cpl.candidate_id = pcn.candidate_id WHERE mmp.id IS NULL AND cpl.id IS NULL').fetchone()[0]
    metrics['need_dedup_remaining'] = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized pcn JOIN merged_metadata_proposal mmp ON mmp.candidate_id = pcn.candidate_id LEFT JOIN candidate_paper_link cpl ON cpl.candidate_id = pcn.candidate_id LEFT JOIN merge_review_queue mrq ON mrq.candidate_id = pcn.candidate_id WHERE cpl.id IS NULL AND mrq.id IS NULL').fetchone()[0]
    for stage in ('resolve_candidates','enrich_candidates','merge_metadata','dedup_candidates'):
        row = conn.execute("SELECT run_id, status, processed_count, notes FROM batch_run WHERE stage=? ORDER BY id DESC LIMIT 1", (stage,)).fetchone()
        if row:
            key = f'latest_{stage}'
            metrics[key] = {
                'run_id': row[0],
                'status': row[1],
                'processed_count': row[2],
                'notes': json.loads(row[3]) if row[3] else None,
            }

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
  update_state "failed" "$STEP" "inspect $LOG and the state file before retrying chunk04 regular fast-pass" || true
  echo "[$(date --iso-8601=seconds)] ERROR during step: $STEP" | tee -a "$LOG"
}
trap on_error ERR

exec > >(tee -a "$LOG") 2>&1

echo "[$(date --iso-8601=seconds)] Phase 2 regular chunk04 fast-pass start"
echo "ROOT=$ROOT"
echo "SQLITE_PATH=$SQLITE_PATH"
echo "MGAP_POLICY_PROFILE=$MGAP_POLICY_PROFILE"
echo "CHUNK_LIMIT=$CHUNK_LIMIT"

STEP="resolve-candidates"
update_state "running" "$STEP" "enrich-candidates-fastpass"
python3 -m mygooglealertpapers.cli resolve-candidates --limit "$CHUNK_LIMIT"

STEP="enrich-candidates-fastpass"
update_state "running" "$STEP" "merge-metadata"
python3 -m mygooglealertpapers.cli enrich-candidates --limit "$CHUNK_LIMIT"

STEP="merge-metadata"
update_state "running" "$STEP" "dedup-candidates"
python3 -m mygooglealertpapers.cli merge-metadata --limit "$CHUNK_LIMIT"

STEP="dedup-candidates"
update_state "running" "$STEP" "reporting"
python3 -m mygooglealertpapers.cli dedup-candidates --limit "$CHUNK_LIMIT"

STEP="reporting"
update_state "running" "$STEP" "phase2 regular chunk04 fast-pass complete"
python3 -m mygooglealertpapers.cli report-enrichment
python3 -m mygooglealertpapers.cli report-merge
python3 -m mygooglealertpapers.cli report-dedup
python3 -m mygooglealertpapers.cli report-review-queue
python3 -m mygooglealertpapers.cli report-cost
python3 -m mygooglealertpapers.cli export-review-queue --output "$REVIEW_EXPORT"

write_metrics "completed"
STEP="phase2-regular-chunk04-fastpass-complete"
update_state "completed" "$STEP" "decide whether to continue chunk05 regular fast-pass or start a dedicated slow title-lane residual sweep"
echo "[$(date --iso-8601=seconds)] Phase 2 regular chunk04 fast-pass completed"
