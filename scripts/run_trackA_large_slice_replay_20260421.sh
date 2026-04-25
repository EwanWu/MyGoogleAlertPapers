#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

RUN_TAG=20260421
STAGE_TIMEOUT_SECONDS=3600
LOG_DIR="$PROJECT_ROOT/data/logs"
mkdir -p "$LOG_DIR"

SEED_DB="data/mgap_pkgB_large_slice150_seed_20260416_slice150.db"
V2_DB="data/mgap_trackA_large_slice150_replay_v2_${RUN_TAG}.db"
NARROW_DB="data/mgap_trackA_large_slice150_replay_v2_narrow_antigarbage_${RUN_TAG}.db"
V2_REPORT="docs/validation/trackA-large-slice150-v2-replay-${RUN_TAG}.json"
NARROW_REPORT="docs/validation/trackA-large-slice150-v2-narrow-antigarbage-replay-${RUN_TAG}.json"
SUMMARY_JSON="docs/validation/trackA-large-slice150-summary-${RUN_TAG}.json"
SUMMARY_MD="docs/validation/trackA-large-slice150-summary-${RUN_TAG}.md"
RUN_LOG="$LOG_DIR/trackA_large_slice150_${RUN_TAG}.log"

rm -f "$V2_DB" "$NARROW_DB" "$V2_REPORT" "$NARROW_REPORT" "$SUMMARY_JSON" "$SUMMARY_MD"

echo "[$(date '+%F %T')] start Track A large-slice fixed-seed replay" | tee -a "$RUN_LOG"
echo "seed=$SEED_DB" | tee -a "$RUN_LOG"
echo "v2=$V2_DB" | tee -a "$RUN_LOG"
echo "narrow=$NARROW_DB" | tee -a "$RUN_LOG"

python3 scripts/replay_validation.py \
  --source-db "$SEED_DB" \
  --output-db "$V2_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v2.yaml \
  --report-out "$V2_REPORT" \
  --stage-timeout-seconds "$STAGE_TIMEOUT_SECONDS" \
  --stages enrich merge dedup | tee -a "$RUN_LOG"

python3 scripts/replay_validation.py \
  --source-db "$SEED_DB" \
  --output-db "$NARROW_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v2_narrow_antigarbage.yaml \
  --report-out "$NARROW_REPORT" \
  --stage-timeout-seconds "$STAGE_TIMEOUT_SECONDS" \
  --stages enrich merge dedup | tee -a "$RUN_LOG"

python3 - <<'PY' | tee -a "$RUN_LOG"
import json
from pathlib import Path

project = Path('.').resolve()
v2_report = project / 'docs/validation/trackA-large-slice150-v2-replay-20260421.json'
narrow_report = project / 'docs/validation/trackA-large-slice150-v2-narrow-antigarbage-replay-20260421.json'
summary_json = project / 'docs/validation/trackA-large-slice150-summary-20260421.json'
summary_md = project / 'docs/validation/trackA-large-slice150-summary-20260421.md'

v2 = json.loads(v2_report.read_text(encoding='utf-8'))
narrow = json.loads(narrow_report.read_text(encoding='utf-8'))
summary = {
    'v2': v2,
    'v2_narrow_antigarbage': narrow,
    'delta_narrow_minus_v2': {
        'matched_source_record_count': narrow['matched_source_record_count'] - v2['matched_source_record_count'],
        'merged_metadata_proposal_count': narrow['merged_metadata_proposal_count'] - v2['merged_metadata_proposal_count'],
        'normalized_only_fallback_proposal_count': narrow['normalized_only_fallback_proposal_count'] - v2['normalized_only_fallback_proposal_count'],
        'merge_review_queue_count': narrow['merge_review_queue_count'] - v2['merge_review_queue_count'],
        'canonical_paper_count': narrow['canonical_paper_count'] - v2['canonical_paper_count'],
        'severe_doi_conflict_count': narrow['severe_doi_conflict_count'] - v2['severe_doi_conflict_count'],
        'cost_event_count': narrow['cost_event_count'] - v2['cost_event_count'],
        'total_batch_duration_ms': narrow['total_batch_duration_ms'] - v2['total_batch_duration_ms'],
        'total_provider_latency_ms': narrow['total_provider_latency_ms'] - v2['total_provider_latency_ms'],
    },
}
summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
summary_md.write_text(
    '\n'.join([
        '# Track A large-slice150 summary (2026-04-21)',
        '',
        '## v2 vs v2_narrow_antigarbage',
        f"- v2 matched_source_record_count: `{v2['matched_source_record_count']}`",
        f"- narrow matched_source_record_count: `{narrow['matched_source_record_count']}`",
        f"- v2 merged_metadata_proposal_count: `{v2['merged_metadata_proposal_count']}`",
        f"- narrow merged_metadata_proposal_count: `{narrow['merged_metadata_proposal_count']}`",
        f"- v2 normalized_only_fallback_proposal_count: `{v2['normalized_only_fallback_proposal_count']}`",
        f"- narrow normalized_only_fallback_proposal_count: `{narrow['normalized_only_fallback_proposal_count']}`",
        f"- v2 merge_review_queue_count: `{v2['merge_review_queue_count']}`",
        f"- narrow merge_review_queue_count: `{narrow['merge_review_queue_count']}`",
        f"- v2 canonical_paper_count: `{v2['canonical_paper_count']}`",
        f"- narrow canonical_paper_count: `{narrow['canonical_paper_count']}`",
        f"- delta canonical (narrow-v2): `{summary['delta_narrow_minus_v2']['canonical_paper_count']}`",
        f"- delta review (narrow-v2): `{summary['delta_narrow_minus_v2']['merge_review_queue_count']}`",
        f"- delta normalized_only_fallback (narrow-v2): `{summary['delta_narrow_minus_v2']['normalized_only_fallback_proposal_count']}`",
        f"- delta provider latency ms (narrow-v2): `{summary['delta_narrow_minus_v2']['total_provider_latency_ms']}`",
        '',
        '## accounting',
        f"- v2 paid_llm_note: `{v2['paid_llm_usage']['note']}`",
        f"- narrow paid_llm_note: `{narrow['paid_llm_usage']['note']}`",
    ]) + '\n',
    encoding='utf-8'
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
PY

echo "[$(date '+%F %T')] completed Track A large-slice fixed-seed replay" | tee -a "$RUN_LOG"
