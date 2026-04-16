#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

export IMAP_ACCOUNT=issac
SLICE_LIMIT=150
PARSE_LIMIT=500
NORMALIZE_LIMIT=800
RUN_TAG=20260416_slice150
STAGE_TIMEOUT_SECONDS=3600
LOG_DIR="$PROJECT_ROOT/data/logs"
mkdir -p "$LOG_DIR"

SEED_DB="data/mgap_pkgB_large_slice150_seed_${RUN_TAG}.db"
V2_DB="data/mgap_pkgB_large_slice150_replay_v2_${RUN_TAG}.db"
V4_DB="data/mgap_pkgB_large_slice150_replay_v4_${RUN_TAG}.db"
V2_REPORT="docs/validation/packageB-large-slice150-v2-replay-${RUN_TAG}.json"
V4_REPORT="docs/validation/packageB-large-slice150-v4-replay-${RUN_TAG}.json"
SUMMARY_JSON="docs/validation/packageB-large-slice150-summary-${RUN_TAG}.json"
SUMMARY_MD="docs/validation/packageB-large-slice150-summary-${RUN_TAG}.md"
RUN_LOG="$LOG_DIR/packageB_large_slice150_${RUN_TAG}.log"

rm -f "$SEED_DB" "$V2_DB" "$V4_DB" "$V2_REPORT" "$V4_REPORT" "$SUMMARY_JSON" "$SUMMARY_MD"

echo "[$(date '+%F %T')] start packageB large-slice validation" | tee -a "$RUN_LOG"
echo "seed=$SEED_DB" | tee -a "$RUN_LOG"
echo "v2=$V2_DB" | tee -a "$RUN_LOG"
echo "v4=$V4_DB" | tee -a "$RUN_LOG"

export SQLITE_PATH="$SEED_DB"
python3 -m mygooglealertpapers.cli init-db | tee -a "$RUN_LOG"
python3 -m mygooglealertpapers.cli scan-mailbox --limit "$SLICE_LIMIT" | tee -a "$RUN_LOG"
python3 -m mygooglealertpapers.cli parse-mails --limit "$PARSE_LIMIT" | tee -a "$RUN_LOG"
python3 -m mygooglealertpapers.cli normalize-candidates --limit "$NORMALIZE_LIMIT" | tee -a "$RUN_LOG"
python3 -m mygooglealertpapers.cli report-batch | tee -a "$RUN_LOG"
python3 -m mygooglealertpapers.cli report-normalization | tee -a "$RUN_LOG"

python3 scripts/replay_validation.py \
  --source-db "$SEED_DB" \
  --output-db "$V2_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v2.yaml \
  --report-out "$V2_REPORT" \
  --stage-timeout-seconds "$STAGE_TIMEOUT_SECONDS" \
  --stages enrich merge dedup | tee -a "$RUN_LOG"

python3 scripts/replay_validation.py \
  --source-db "$SEED_DB" \
  --output-db "$V4_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v4_fallback_guardrail_salvage.yaml \
  --report-out "$V4_REPORT" \
  --stage-timeout-seconds "$STAGE_TIMEOUT_SECONDS" \
  --stages enrich merge dedup | tee -a "$RUN_LOG"

python3 - <<'PY' | tee -a "$RUN_LOG"
import json, sqlite3
from pathlib import Path

project = Path('.').resolve()
seed_db = project / 'data/mgap_pkgB_large_slice150_seed_20260416_slice150.db'
v2_report = project / 'docs/validation/packageB-large-slice150-v2-replay-20260416_slice150.json'
v4_report = project / 'docs/validation/packageB-large-slice150-v4-replay-20260416_slice150.json'
summary_json = project / 'docs/validation/packageB-large-slice150-summary-20260416_slice150.json'
summary_md = project / 'docs/validation/packageB-large-slice150-summary-20260416_slice150.md'

with sqlite3.connect(seed_db) as conn:
    seed = {
        'paper_candidate_count': conn.execute('select count(*) from paper_candidate').fetchone()[0],
        'normalized_candidate_count': conn.execute('select count(*) from paper_candidate_normalized').fetchone()[0],
    }

v2 = json.loads(v2_report.read_text(encoding='utf-8'))
v4 = json.loads(v4_report.read_text(encoding='utf-8'))
summary = {
    'seed': seed,
    'v2': v2,
    'v4': v4,
    'delta_v4_minus_v2': {
        'matched_source_record_count': v4['matched_source_record_count'] - v2['matched_source_record_count'],
        'merged_metadata_proposal_count': v4['merged_metadata_proposal_count'] - v2['merged_metadata_proposal_count'],
        'merge_review_queue_count': v4['merge_review_queue_count'] - v2['merge_review_queue_count'],
        'canonical_paper_count': v4['canonical_paper_count'] - v2['canonical_paper_count'],
        'cost_event_count': v4['cost_event_count'] - v2['cost_event_count'],
        'total_batch_duration_ms': v4['total_batch_duration_ms'] - v2['total_batch_duration_ms'],
        'total_provider_latency_ms': v4['total_provider_latency_ms'] - v2['total_provider_latency_ms'],
    },
}
summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
summary_md.write_text(
    '\n'.join([
        '# Package B large-slice150 summary (2026-04-16)',
        '',
        f"- seed paper_candidate_count: `{seed['paper_candidate_count']}`",
        f"- seed normalized_candidate_count: `{seed['normalized_candidate_count']}`",
        '',
        '## v2 vs v4',
        f"- v2 matched_source_record_count: `{v2['matched_source_record_count']}`",
        f"- v4 matched_source_record_count: `{v4['matched_source_record_count']}`",
        f"- v2 merged_metadata_proposal_count: `{v2['merged_metadata_proposal_count']}`",
        f"- v4 merged_metadata_proposal_count: `{v4['merged_metadata_proposal_count']}`",
        f"- v2 merge_review_queue_count: `{v2['merge_review_queue_count']}`",
        f"- v4 merge_review_queue_count: `{v4['merge_review_queue_count']}`",
        f"- v2 canonical_paper_count: `{v2['canonical_paper_count']}`",
        f"- v4 canonical_paper_count: `{v4['canonical_paper_count']}`",
        f"- delta canonical (v4-v2): `{summary['delta_v4_minus_v2']['canonical_paper_count']}`",
        f"- delta review (v4-v2): `{summary['delta_v4_minus_v2']['merge_review_queue_count']}`",
        f"- delta provider latency ms (v4-v2): `{summary['delta_v4_minus_v2']['total_provider_latency_ms']}`",
        '',
        '## accounting',
        f"- v2 paid_llm_note: `{v2['paid_llm_usage']['note']}`",
        f"- v4 paid_llm_note: `{v4['paid_llm_usage']['note']}`",
    ]) + '\n',
    encoding='utf-8'
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
PY

echo "[$(date '+%F %T')] completed packageB large-slice validation" | tee -a "$RUN_LOG"
