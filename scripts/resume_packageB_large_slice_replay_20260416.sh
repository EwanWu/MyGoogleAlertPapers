#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

LOG=data/logs/packageB_large_slice150_resume_20260416.log
SEED=data/mgap_pkgB_large_slice150_seed_20260416_slice150.db
V2_DB=data/mgap_pkgB_large_slice150_replay_v2_20260416_slice150.db
V4_DB=data/mgap_pkgB_large_slice150_replay_v4_20260416_slice150.db
V2_REPORT=docs/validation/packageB-large-slice150-v2-replay-20260416_slice150.json
V4_REPORT=docs/validation/packageB-large-slice150-v4-replay-20260416_slice150.json
SUMMARY_JSON=docs/validation/packageB-large-slice150-summary-20260416_slice150.json
SUMMARY_MD=docs/validation/packageB-large-slice150-summary-20260416_slice150.md

rm -f "$V2_DB" "$V4_DB" "$V2_REPORT" "$V4_REPORT" "$SUMMARY_JSON" "$SUMMARY_MD"

echo "[$(date '+%F %T')] resume formal larger-slice replay from fixed seed" | tee -a "$LOG"

python3 scripts/replay_validation.py \
  --source-db "$SEED" \
  --output-db "$V2_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v2.yaml \
  --report-out "$V2_REPORT" \
  --stage-timeout-seconds 3600 \
  --stages enrich merge dedup | tee -a "$LOG"

python3 scripts/replay_validation.py \
  --source-db "$SEED" \
  --output-db "$V4_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v4_fallback_guardrail_salvage.yaml \
  --report-out "$V4_REPORT" \
  --stage-timeout-seconds 3600 \
  --stages enrich merge dedup | tee -a "$LOG"

python3 scripts/summarize_packageB_large_slice_replay_20260416.py | tee -a "$LOG"

echo "[$(date '+%F %T')] completed formal larger-slice replay" | tee -a "$LOG"
