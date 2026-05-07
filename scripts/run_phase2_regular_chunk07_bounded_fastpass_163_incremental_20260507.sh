#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/ewan/NewCareer/Openclaw/proj/MyGoogleAlertPapers"
STATE="$ROOT/data/task_state/phase2_regular_chunk07_bounded_163_incremental_20260507.json"
LOG="$ROOT/data/logs/phase2_regular_chunk07_bounded_fastpass_163_incremental_20260507.log"
REVIEW_EXPORT="$ROOT/data/exports/review_queue_phase2_regular_chunk07_bounded_20260507.jsonl"
DB_PATH="/home/ewan/NewCareer/MyPaperDatabase/mgap_163_incremental_20260506.db"
POLICY_PROFILE="$ROOT/config/policy_profiles/openalex_batching_identifier_fastpath.yaml"
CHUNK_LIMIT=50

export SQLITE_PATH="$DB_PATH"
export MGAP_POLICY_PROFILE="$POLICY_PROFILE"
STEP="starting"

mkdir -p "$(dirname "$LOG")" "$(dirname "$STATE")" "$(dirname "$REVIEW_EXPORT")"

ensure_state() {
  STATE="$STATE" DB_PATH="$DB_PATH" POLICY_PROFILE="$POLICY_PROFILE" REVIEW_EXPORT="$REVIEW_EXPORT" CHUNK_LIMIT="$CHUNK_LIMIT" python3 - <<'PY'
import datetime, json, os, sqlite3
state_path = os.environ['STATE']
db_path = os.environ['DB_PATH']
policy_profile = os.environ['POLICY_PROFILE']
review_export = os.environ['REVIEW_EXPORT']
chunk_limit = int(os.environ['CHUNK_LIMIT'])
if os.path.exists(state_path):
    raise SystemExit(0)
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
metrics = {}
with sqlite3.connect(db_path) as conn:
    metrics['paper_candidates'] = conn.execute('SELECT COUNT(*) FROM paper_candidate').fetchone()[0]
    metrics['normalized_candidates'] = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized').fetchone()[0]
    metrics['canonical_papers'] = conn.execute('SELECT COUNT(*) FROM canonical_paper').fetchone()[0]
    metrics['candidate_paper_links'] = conn.execute('SELECT COUNT(*) FROM candidate_paper_link').fetchone()[0]
    metrics['review_blocked_total'] = conn.execute('SELECT COUNT(*) FROM merge_review_queue').fetchone()[0]
    metrics['need_merge_remaining'] = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized pcn LEFT JOIN merged_metadata_proposal mmp ON mmp.candidate_id = pcn.candidate_id LEFT JOIN candidate_paper_link cpl ON cpl.candidate_id = pcn.candidate_id WHERE mmp.id IS NULL AND cpl.id IS NULL').fetchone()[0]
    metrics['need_dedup_remaining'] = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized pcn JOIN merged_metadata_proposal mmp ON mmp.candidate_id = pcn.candidate_id LEFT JOIN candidate_paper_link cpl ON cpl.candidate_id = pcn.candidate_id LEFT JOIN merge_review_queue mrq ON mrq.candidate_id = pcn.candidate_id WHERE cpl.id IS NULL AND mrq.id IS NULL').fetchone()[0]
state = {
    'flow_id': 'phase2_regular_chunk07_bounded_163_incremental_20260507',
    'owner_session_key': 'agent:deepblue:main',
    'status': 'created',
    'goal': 'Run a bounded chunk07 regular fast-pass on the remaining 163 incremental regular tail after manual residual cleanup reduced need_merge to a small leftover set.',
    'current_step': 'created',
    'next_step': 'resolve-candidates',
    'expected_artifacts': [db_path, os.environ['STATE'], os.environ['REVIEW_EXPORT'], os.environ['STATE'].replace('/data/task_state/', '/data/logs/').replace('.json', '.log')],
    'already_made_decisions': [
        'User explicitly requested continuing chunk07 despite prior low-yield recommendation',
        'Chunk07 is bounded rather than a full 5000-candidate block because residual need_merge is already small',
        'Policy stays on validated regular identifier_fastpath profile for reproducible comparison with chunk03-06',
        'Foreground monitored run is acceptable here because the bounded chunk is expected to finish within the current session'
    ],
    'commands_started': [],
    'process_ids': [],
    'last_check_time': now,
    'handoff_sent': False,
    'db_path': db_path,
    'chunk_limit': chunk_limit,
    'notes': 'Bounded chunk07 created after manual residual triage lowered need_merge. Intended as a user-directed closure probe rather than a high-expectation standard chunk.',
    'cron_followup': {
        'current_job': None,
        'reason': 'foreground_bounded_run_no_detach'
    },
    'latest_observed_metrics': metrics,
    'active_policy_profile': policy_profile,
}
with open(state_path, 'w', encoding='utf-8') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
    f.write('\n')
PY
}

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
    metrics['unlinked_total'] = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized pcn LEFT JOIN candidate_paper_link cpl ON cpl.candidate_id=pcn.candidate_id WHERE cpl.id IS NULL').fetchone()[0]
    for stage in ('resolve_candidates','enrich_candidates','merge_metadata','dedup_candidates'):
        row = conn.execute("SELECT run_id, status, processed_count, notes FROM batch_run WHERE stage=? ORDER BY id DESC LIMIT 1", (stage,)).fetchone()
        if row:
            metrics[f'latest_{stage}'] = {
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
  update_state "failed" "$STEP" "inspect $LOG and decide whether bounded chunk07 should be abandoned" || true
  echo "[$(date --iso-8601=seconds)] ERROR during step: $STEP" | tee -a "$LOG"
}
trap on_error ERR

ensure_state

exec > >(tee -a "$LOG") 2>&1

echo "[$(date --iso-8601=seconds)] Phase 2 regular chunk07 bounded fast-pass start"
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
update_state "running" "$STEP" "phase2 regular chunk07 bounded fast-pass complete"
python3 -m mygooglealertpapers.cli report-enrichment
python3 -m mygooglealertpapers.cli report-merge
python3 -m mygooglealertpapers.cli report-dedup
python3 -m mygooglealertpapers.cli report-review-queue
python3 -m mygooglealertpapers.cli report-cost
python3 -m mygooglealertpapers.cli export-review-queue --output "$REVIEW_EXPORT"

write_metrics "completed"
STEP="phase2-regular-chunk07-bounded-fastpass-complete"
update_state "completed" "$STEP" "decide whether the remaining residual should be closed manually rather than by regular fast-pass"
echo "[$(date --iso-8601=seconds)] Phase 2 regular chunk07 bounded fast-pass completed"
