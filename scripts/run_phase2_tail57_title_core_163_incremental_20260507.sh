#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers"
STATE="$ROOT/data/task_state/phase2_tail57_title_core_163_incremental_20260507.json"
LOG="$ROOT/data/logs/phase2_tail57_title_core_163_incremental_20260507.log"
REVIEW_EXPORT="$ROOT/data/exports/review_queue_phase2_tail57_title_core_20260507.jsonl"
DB_PATH="/home/ewan/NewCareer/MyPaperDatabase/mgap_163_incremental_20260506.db"
CHUNK_LIMIT=57
PROFILE_NOTE="builtin default: identifier_fastpath + title_core + same_batch_cluster + url_identity_doi_recovery"

export SQLITE_PATH="$DB_PATH"
unset MGAP_POLICY_PROFILE || true
STEP="starting"

mkdir -p "$(dirname "$LOG")" "$(dirname "$STATE")" "$(dirname "$REVIEW_EXPORT")"

write_state() {
  local status="$1"
  local current_step="$2"
  local next_step="$3"
  STATUS="$status" CURRENT_STEP="$current_step" NEXT_STEP="$next_step" STATE="$STATE" DB_PATH="$DB_PATH" CHUNK_LIMIT="$CHUNK_LIMIT" PROFILE_NOTE="$PROFILE_NOTE" python3 - <<'PY'
import datetime, json, os, sqlite3
state_path = os.environ['STATE']
status = os.environ['STATUS']
current_step = os.environ['CURRENT_STEP']
next_step = os.environ['NEXT_STEP']
db_path = os.environ['DB_PATH']
chunk_limit = int(os.environ['CHUNK_LIMIT'])
profile_note = os.environ['PROFILE_NOTE']
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
metrics = {}
with sqlite3.connect(db_path) as conn:
    metrics['unlinked_total'] = conn.execute("SELECT COUNT(*) FROM paper_candidate_normalized pcn LEFT JOIN candidate_paper_link cpl ON cpl.candidate_id=pcn.candidate_id WHERE cpl.id IS NULL").fetchone()[0]
    metrics['need_merge_remaining'] = conn.execute("SELECT COUNT(*) FROM paper_candidate_normalized pcn LEFT JOIN merged_metadata_proposal mmp ON mmp.candidate_id = pcn.candidate_id LEFT JOIN candidate_paper_link cpl ON cpl.candidate_id = pcn.candidate_id WHERE mmp.id IS NULL AND cpl.id IS NULL").fetchone()[0]
    metrics['need_dedup_remaining'] = conn.execute("SELECT COUNT(*) FROM paper_candidate_normalized pcn JOIN merged_metadata_proposal mmp ON mmp.candidate_id = pcn.candidate_id LEFT JOIN candidate_paper_link cpl ON cpl.candidate_id = pcn.candidate_id LEFT JOIN merge_review_queue mrq ON mrq.candidate_id = pcn.candidate_id WHERE cpl.id IS NULL AND mrq.id IS NULL").fetchone()[0]
    metrics['review_queue_total'] = conn.execute("SELECT COUNT(*) FROM merge_review_queue").fetchone()[0]
    metrics['canonical_papers'] = conn.execute("SELECT COUNT(*) FROM canonical_paper").fetchone()[0]
    metrics['candidate_paper_links'] = conn.execute("SELECT COUNT(*) FROM candidate_paper_link").fetchone()[0]
    for stage in ('enrich_candidates', 'merge_metadata', 'dedup_candidates'):
        row = conn.execute("SELECT run_id, status, processed_count, notes FROM batch_run WHERE stage=? ORDER BY id DESC LIMIT 1", (stage,)).fetchone()
        if row:
            metrics[f'latest_{stage}'] = {
                'run_id': row[0], 'status': row[1], 'processed_count': row[2],
                'notes': json.loads(row[3]) if row[3] else None,
            }
state = {
    'flow_id': 'phase2_tail57_title_core_163_incremental_20260507',
    'owner_session_key': 'agent:deepblue:main',
    'status': status,
    'goal': 'Run a bounded tail sweep on the remaining unlinked chunk06 residuals using the builtin title_core-enabled default runtime, then clear the residual merge tail if possible.',
    'current_step': current_step,
    'next_step': next_step,
    'db_path': db_path,
    'chunk_limit': chunk_limit,
    'profile_note': profile_note,
    'expected_artifacts': [state_path, os.environ['DB_PATH'], os.environ['STATE'].replace('/data/task_state/', '/data/logs/').replace('.json', '.log'), os.environ['STATE'].replace('/data/task_state/', '/data/exports/').replace('.json', '.jsonl')],
    'last_check_time': now,
    'latest_observed_metrics': metrics,
}
with open(state_path, 'w', encoding='utf-8') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
    f.write('\n')
PY
}

on_error() {
  write_state "failed" "$STEP" "inspect tail57 log/state before retrying" || true
  echo "[$(date --iso-8601=seconds)] ERROR during step: $STEP" | tee -a "$LOG"
}
trap on_error ERR

exec > >(tee -a "$LOG") 2>&1

echo "[$(date --iso-8601=seconds)] Phase 2 tail57 title-core sweep start"
echo "ROOT=$ROOT"
echo "SQLITE_PATH=$SQLITE_PATH"
echo "PROFILE_NOTE=$PROFILE_NOTE"
echo "CHUNK_LIMIT=$CHUNK_LIMIT"

STEP="enrich-candidates-tail57"
write_state "running" "$STEP" "merge-metadata-tail57"
python3 -m mygooglealertpapers.cli enrich-candidates --limit "$CHUNK_LIMIT"

STEP="merge-metadata-tail57"
write_state "running" "$STEP" "dedup-candidates-tail57"
python3 -m mygooglealertpapers.cli merge-metadata --limit "$CHUNK_LIMIT"

STEP="dedup-candidates-tail57"
write_state "running" "$STEP" "reporting"
python3 -m mygooglealertpapers.cli dedup-candidates --limit "$CHUNK_LIMIT"

STEP="reporting"
write_state "running" "$STEP" "tail57 complete"
python3 -m mygooglealertpapers.cli report-enrichment
python3 -m mygooglealertpapers.cli report-merge
python3 -m mygooglealertpapers.cli report-dedup
python3 -m mygooglealertpapers.cli report-review-queue
python3 -m mygooglealertpapers.cli report-cost
python3 -m mygooglealertpapers.cli export-review-queue --output "$REVIEW_EXPORT"

STEP="tail57-complete"
write_state "completed" "$STEP" "decide whether any residual tail remains or whether the regular path is closed"
echo "[$(date --iso-8601=seconds)] Phase 2 tail57 title-core sweep completed"
