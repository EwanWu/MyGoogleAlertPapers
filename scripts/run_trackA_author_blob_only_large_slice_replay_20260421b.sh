#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

RUN_TAG=20260421b
STAGE_TIMEOUT_SECONDS=3600
LOG_DIR="$PROJECT_ROOT/data/logs"
mkdir -p "$LOG_DIR"

SEED_DB="data/mgap_pkgB_large_slice150_seed_20260416_slice150.db"
V2_DB="data/mgap_trackA_author_blob_only_large_slice150_replay_v2_${RUN_TAG}.db"
AB_DB="data/mgap_trackA_author_blob_only_large_slice150_replay_author_blob_only_${RUN_TAG}.db"
V2_REPORT="docs/validation/trackA-author-blob-only-large-slice150-v2-replay-${RUN_TAG}.json"
AB_REPORT="docs/validation/trackA-author-blob-only-large-slice150-replay-${RUN_TAG}.json"
SUMMARY_JSON="docs/validation/trackA-author-blob-only-large-slice150-summary-${RUN_TAG}.json"
SUMMARY_MD="docs/validation/trackA-author-blob-only-large-slice150-summary-${RUN_TAG}.md"
RUN_LOG="$LOG_DIR/trackA_author_blob_only_large_slice150_${RUN_TAG}.log"

rm -f "$V2_DB" "$AB_DB" "$V2_REPORT" "$AB_REPORT" "$SUMMARY_JSON" "$SUMMARY_MD"

echo "[$(date '+%F %T')] start Track A author-blob-only large-slice fixed-seed replay" | tee -a "$RUN_LOG"
echo "seed=$SEED_DB" | tee -a "$RUN_LOG"
echo "v2=$V2_DB" | tee -a "$RUN_LOG"
echo "author_blob_only=$AB_DB" | tee -a "$RUN_LOG"

python3 scripts/replay_validation.py \
  --source-db "$SEED_DB" \
  --output-db "$V2_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v2.yaml \
  --report-out "$V2_REPORT" \
  --stage-timeout-seconds "$STAGE_TIMEOUT_SECONDS" \
  --stages enrich merge dedup | tee -a "$RUN_LOG"

python3 scripts/replay_validation.py \
  --source-db "$SEED_DB" \
  --output-db "$AB_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v2_author_blob_only.yaml \
  --report-out "$AB_REPORT" \
  --stage-timeout-seconds "$STAGE_TIMEOUT_SECONDS" \
  --stages enrich merge dedup | tee -a "$RUN_LOG"

python3 - <<'PY' | tee -a "$RUN_LOG"
import json
from pathlib import Path

project = Path('.').resolve()
v2_report = project / 'docs/validation/trackA-author-blob-only-large-slice150-v2-replay-20260421b.json'
ab_report = project / 'docs/validation/trackA-author-blob-only-large-slice150-replay-20260421b.json'
summary_json = project / 'docs/validation/trackA-author-blob-only-large-slice150-summary-20260421b.json'
summary_md = project / 'docs/validation/trackA-author-blob-only-large-slice150-summary-20260421b.md'

v2 = json.loads(v2_report.read_text(encoding='utf-8'))
author_blob = json.loads(ab_report.read_text(encoding='utf-8'))
summary = {
    'v2': v2,
    'author_blob_only': author_blob,
    'delta_author_blob_only_minus_v2': {
        'matched_source_record_count': author_blob['matched_source_record_count'] - v2['matched_source_record_count'],
        'merged_metadata_proposal_count': author_blob['merged_metadata_proposal_count'] - v2['merged_metadata_proposal_count'],
        'normalized_only_fallback_proposal_count': author_blob['normalized_only_fallback_proposal_count'] - v2['normalized_only_fallback_proposal_count'],
        'merge_review_queue_count': author_blob['merge_review_queue_count'] - v2['merge_review_queue_count'],
        'canonical_paper_count': author_blob['canonical_paper_count'] - v2['canonical_paper_count'],
        'severe_doi_conflict_count': author_blob['severe_doi_conflict_count'] - v2['severe_doi_conflict_count'],
        'cost_event_count': author_blob['cost_event_count'] - v2['cost_event_count'],
        'total_batch_duration_ms': author_blob['total_batch_duration_ms'] - v2['total_batch_duration_ms'],
        'total_provider_latency_ms': author_blob['total_provider_latency_ms'] - v2['total_provider_latency_ms'],
    },
}
summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
summary_md.write_text(
    '\n'.join([
        '# Track A author-blob-only large-slice150 summary (2026-04-21)',
        '',
        '## v2 vs author_blob_only',
        f"- v2 matched_source_record_count: `{v2['matched_source_record_count']}`",
        f"- author_blob_only matched_source_record_count: `{author_blob['matched_source_record_count']}`",
        f"- v2 merged_metadata_proposal_count: `{v2['merged_metadata_proposal_count']}`",
        f"- author_blob_only merged_metadata_proposal_count: `{author_blob['merged_metadata_proposal_count']}`",
        f"- v2 normalized_only_fallback_proposal_count: `{v2['normalized_only_fallback_proposal_count']}`",
        f"- author_blob_only normalized_only_fallback_proposal_count: `{author_blob['normalized_only_fallback_proposal_count']}`",
        f"- v2 merge_review_queue_count: `{v2['merge_review_queue_count']}`",
        f"- author_blob_only merge_review_queue_count: `{author_blob['merge_review_queue_count']}`",
        f"- v2 canonical_paper_count: `{v2['canonical_paper_count']}`",
        f"- author_blob_only canonical_paper_count: `{author_blob['canonical_paper_count']}`",
        f"- delta canonical (author_blob_only-v2): `{summary['delta_author_blob_only_minus_v2']['canonical_paper_count']}`",
        f"- delta review (author_blob_only-v2): `{summary['delta_author_blob_only_minus_v2']['merge_review_queue_count']}`",
        f"- delta normalized_only_fallback (author_blob_only-v2): `{summary['delta_author_blob_only_minus_v2']['normalized_only_fallback_proposal_count']}`",
        f"- delta provider latency ms (author_blob_only-v2): `{summary['delta_author_blob_only_minus_v2']['total_provider_latency_ms']}`",
        '',
        '## accounting',
        f"- v2 paid_llm_note: `{v2['paid_llm_usage']['note']}`",
        f"- author_blob_only paid_llm_note: `{author_blob['paid_llm_usage']['note']}`",
    ]) + '\n',
    encoding='utf-8'
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
PY

echo "[$(date '+%F %T')] completed Track A author-blob-only large-slice fixed-seed replay" | tee -a "$RUN_LOG"
