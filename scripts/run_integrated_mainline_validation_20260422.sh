#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

RUN_TAG="20260422_mainline"
LOG_DIR="$PROJECT_ROOT/data/logs"
mkdir -p "$LOG_DIR"

SEED_DB="data/mgap_pkgB_large_slice150_seed_20260416_slice150.db"
DONOR_DB="data/mgap_trackA_author_blob_fb_v2_20260421c.db"
CONTROL_DB="data/mgap_mainline_control_${RUN_TAG}.db"
TREAT_DB="data/mgap_mainline_treat_${RUN_TAG}.db"
CONTROL_REPORT="docs/validation/mainline-control-${RUN_TAG}.json"
TREAT_REPORT="docs/validation/mainline-treat-${RUN_TAG}.json"
SUMMARY_JSON="docs/validation/mainline-summary-${RUN_TAG}.json"
SUMMARY_MD="docs/validation/mainline-summary-${RUN_TAG}.md"
RUN_LOG="$LOG_DIR/mainline_validation_${RUN_TAG}.log"

rm -f "$CONTROL_DB" "$TREAT_DB" "$CONTROL_REPORT" "$TREAT_REPORT" "$SUMMARY_JSON" "$SUMMARY_MD"

if [[ -z "${UNPAYWALL_EMAIL:-}" ]]; then
  echo "UNPAYWALL_EMAIL is required for the post-dedup OA stage" >&2
  exit 1
fi

echo "[$(date '+%F %T')] start integrated mainline validation" | tee -a "$RUN_LOG"
echo "seed=$SEED_DB" | tee -a "$RUN_LOG"
echo "donor=$DONOR_DB" | tee -a "$RUN_LOG"
echo "control_db=$CONTROL_DB" | tee -a "$RUN_LOG"
echo "treat_db=$TREAT_DB" | tee -a "$RUN_LOG"

python3 scripts/replay_validation.py \
  --source-db "$SEED_DB" \
  --output-db "$CONTROL_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v2.yaml \
  --report-out "$CONTROL_REPORT" \
  --reuse-source-records-from "$DONOR_DB" \
  --stages merge dedup | tee -a "$RUN_LOG"

python3 scripts/replay_validation.py \
  --source-db "$SEED_DB" \
  --output-db "$TREAT_DB" \
  --policy-profile config/policy_profiles/conditional_sources_v2_author_blob_fallback_only.yaml \
  --report-out "$TREAT_REPORT" \
  --reuse-source-records-from "$DONOR_DB" \
  --stages merge dedup | tee -a "$RUN_LOG"

SQLITE_PATH="$TREAT_DB" python3 -m mygooglealertpapers.cli enrich-paper-oa --limit 1000000 | tee -a "$RUN_LOG"
SQLITE_PATH="$TREAT_DB" python3 -m mygooglealertpapers.cli report-paper-oa | tee -a "$RUN_LOG"

python3 - <<'PY' | tee -a "$RUN_LOG"
import json
import sqlite3
from pathlib import Path

project = Path('.').resolve()
run_tag = '20260422_mainline'
control_report = project / f'docs/validation/mainline-control-{run_tag}.json'
treat_report = project / f'docs/validation/mainline-treat-{run_tag}.json'
donor_db = project / 'data/mgap_trackA_author_blob_fb_v2_20260421c.db'
treat_db = project / f'data/mgap_mainline_treat_{run_tag}.db'
summary_json = project / f'docs/validation/mainline-summary-{run_tag}.json'
summary_md = project / f'docs/validation/mainline-summary-{run_tag}.md'

garbage_candidate = 'cand_400e144162689110'

control = json.loads(control_report.read_text(encoding='utf-8'))
treat = json.loads(treat_report.read_text(encoding='utf-8'))

with sqlite3.connect(donor_db) as conn:
    baseline_enrich_latency_ms = int(conn.execute("SELECT COALESCE(SUM(latency_ms),0) FROM cost_event WHERE stage='enrich_candidates' AND provider IS NOT NULL").fetchone()[0] or 0)
    baseline_provider_summary = [
        {
            'provider': row[0],
            'events': int(row[1]),
            'total_latency_ms': int(row[2] or 0),
        }
        for row in conn.execute(
            """
            SELECT COALESCE(provider, 'none'), COUNT(*), COALESCE(SUM(latency_ms),0)
            FROM cost_event
            WHERE stage='enrich_candidates'
            GROUP BY COALESCE(provider, 'none')
            ORDER BY COALESCE(provider, 'none')
            """
        ).fetchall()
    ]

with sqlite3.connect(treat_db) as conn:
    oa_summary = {
        'paper_open_access_count': int(conn.execute('SELECT COUNT(*) FROM paper_open_access').fetchone()[0] or 0),
        'canonical_doi_count': int(conn.execute('SELECT COUNT(*) FROM canonical_paper WHERE canonical_doi IS NOT NULL').fetchone()[0] or 0),
        'is_oa_true_count': int(conn.execute('SELECT COUNT(*) FROM paper_open_access WHERE is_oa = 1').fetchone()[0] or 0),
        'best_oa_url_count': int(conn.execute("SELECT COUNT(*) FROM paper_open_access WHERE best_oa_url IS NOT NULL AND TRIM(best_oa_url) != ''").fetchone()[0] or 0),
        'oa_latency_ms': int(conn.execute("SELECT COALESCE(SUM(latency_ms),0) FROM cost_event WHERE stage='enrich_paper_oa' AND provider='unpaywall'").fetchone()[0] or 0),
        'oa_cost_event_count': int(conn.execute("SELECT COUNT(*) FROM cost_event WHERE stage='enrich_paper_oa' AND provider='unpaywall'").fetchone()[0] or 0),
        'oa_cache_hit_count': int(conn.execute("SELECT COUNT(*) FROM paper_oa_enrichment_status WHERE provider='unpaywall' AND cache_hit = 1").fetchone()[0] or 0),
        'oa_status_breakdown': [
            {'oa_status': row[0], 'count': int(row[1])}
            for row in conn.execute(
                "SELECT COALESCE(oa_status, 'unknown'), COUNT(*) FROM paper_open_access GROUP BY COALESCE(oa_status, 'unknown') ORDER BY COUNT(*) DESC, COALESCE(oa_status, 'unknown') ASC"
            ).fetchall()
        ],
        'oa_enrichment_status_breakdown': [
            {'status': row[0], 'count': int(row[1])}
            for row in conn.execute(
                "SELECT status, COUNT(*) FROM paper_oa_enrichment_status GROUP BY status ORDER BY COUNT(*) DESC, status ASC"
            ).fetchall()
        ],
    }
    control_has_garbage = int(conn.execute('SELECT 0').fetchone()[0])

with sqlite3.connect(project / f'data/mgap_mainline_control_{run_tag}.db') as control_conn, sqlite3.connect(treat_db) as treat_conn:
    control_garbage_present = bool(control_conn.execute('SELECT COUNT(*) FROM merged_metadata_proposal WHERE candidate_id = ?', (garbage_candidate,)).fetchone()[0])
    treat_garbage_present = bool(treat_conn.execute('SELECT COUNT(*) FROM merged_metadata_proposal WHERE candidate_id = ?', (garbage_candidate,)).fetchone()[0])
    control_candidates = {row[0] for row in control_conn.execute('SELECT candidate_id FROM merged_metadata_proposal')}
    treat_candidates = {row[0] for row in treat_conn.execute('SELECT candidate_id FROM merged_metadata_proposal')}

only_control_candidates = sorted(control_candidates - treat_candidates)
only_treat_candidates = sorted(treat_candidates - control_candidates)
collateral_loss_candidates = [cand for cand in only_control_candidates if cand != garbage_candidate]
targeted_removal_only = (
    control_garbage_present
    and not treat_garbage_present
    and only_control_candidates == [garbage_candidate]
    and not only_treat_candidates
)

summary = {
    'run_tag': run_tag,
    'control_profile': 'conditional_sources_v2',
    'treatment_profile': 'conditional_sources_v2_author_blob_fallback_only + post_dedup_unpaywall',
    'baseline_enrich_from_donor_db': {
        'db': str(donor_db),
        'provider_latency_ms': baseline_enrich_latency_ms,
        'provider_summary': baseline_provider_summary,
        'paid_llm_usage': {'present': False, 'note': 'No paid LLM call path was exercised in the donor enrich run.'},
    },
    'control_merge_dedup': control,
    'treatment_merge_dedup': treat,
    'trackA_delta': {
        'canonical_paper_count': treat['canonical_paper_count'] - control['canonical_paper_count'],
        'merge_review_queue_count': treat['merge_review_queue_count'] - control['merge_review_queue_count'],
        'severe_doi_conflict_count': treat['severe_doi_conflict_count'] - control['severe_doi_conflict_count'],
        'normalized_only_fallback_proposal_count': treat['normalized_only_fallback_proposal_count'] - control['normalized_only_fallback_proposal_count'],
    },
    'garbage_case_check': {
        'candidate_id': garbage_candidate,
        'control_present_in_merged_proposal': control_garbage_present,
        'treatment_present_in_merged_proposal': treat_garbage_present,
        'blocked_in_treatment': control_garbage_present and not treat_garbage_present,
        'only_control_candidates': only_control_candidates,
        'only_treat_candidates': only_treat_candidates,
        'collateral_loss_candidates': collateral_loss_candidates,
        'targeted_removal_only': targeted_removal_only,
    },
    'post_dedup_oa': oa_summary,
    'integrated_takeaway': {
        'trackA_removed_target_garbage_only': targeted_removal_only,
        'review_not_worse': treat['merge_review_queue_count'] <= control['merge_review_queue_count'],
        'severe_conflict_not_worse': treat['severe_doi_conflict_count'] <= control['severe_doi_conflict_count'],
        'oa_urls_added': oa_summary['best_oa_url_count'],
        'oa_stage_latency_ms': oa_summary['oa_latency_ms'],
    },
}

summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

md = f"""# Integrated mainline validation summary ({run_tag})

## Profiles
- control: `conditional_sources_v2`
- treatment: `conditional_sources_v2_author_blob_fallback_only + post_dedup_unpaywall`

## Baseline enrich cost (donor v2 source-record run)
- provider latency total: `{baseline_enrich_latency_ms}` ms
- paid LLM usage: `False`

## Track A merge/dedup delta under reused source records
| metric | control | treatment | delta |
|---|---:|---:|---:|
| canonical_paper_count | {control['canonical_paper_count']} | {treat['canonical_paper_count']} | {treat['canonical_paper_count'] - control['canonical_paper_count']} |
| merge_review_queue_count | {control['merge_review_queue_count']} | {treat['merge_review_queue_count']} | {treat['merge_review_queue_count'] - control['merge_review_queue_count']} |
| severe_doi_conflict_count | {control['severe_doi_conflict_count']} | {treat['severe_doi_conflict_count']} | {treat['severe_doi_conflict_count'] - control['severe_doi_conflict_count']} |
| normalized_only_fallback_proposal_count | {control['normalized_only_fallback_proposal_count']} | {treat['normalized_only_fallback_proposal_count']} | {treat['normalized_only_fallback_proposal_count'] - control['normalized_only_fallback_proposal_count']} |

## Garbage-case check
- candidate: `{garbage_candidate}`
- control present in merged proposal: `{control_garbage_present}`
- treatment present in merged proposal: `{treat_garbage_present}`
- blocked in treatment: `{control_garbage_present and not treat_garbage_present}`
- only-control candidate diff: `{only_control_candidates}`
- only-treatment candidate diff: `{only_treat_candidates}`
- collateral loss candidates: `{collateral_loss_candidates}`
- targeted removal only: `{targeted_removal_only}`

## Post-dedup OA stage
- canonical DOI count: `{oa_summary['canonical_doi_count']}`
- paper_open_access rows: `{oa_summary['paper_open_access_count']}`
- is_oa=true rows: `{oa_summary['is_oa_true_count']}`
- best_oa_url filled rows: `{oa_summary['best_oa_url_count']}`
- OA stage latency: `{oa_summary['oa_latency_ms']}` ms
- OA stage cost events: `{oa_summary['oa_cost_event_count']}`
- OA cache hits: `{oa_summary['oa_cache_hit_count']}`

## Bottom line
- Track A targeted garbage removal only: `{targeted_removal_only}`
- Review burden not worse: `{treat['merge_review_queue_count'] <= control['merge_review_queue_count']}`
- Severe DOI conflict not worse: `{treat['severe_doi_conflict_count'] <= control['severe_doi_conflict_count']}`
- OA URLs added by integrated candidate: `{oa_summary['best_oa_url_count']}`
"""
summary_md.write_text(md, encoding='utf-8')
print(json.dumps({'status': 'ok', 'summary_json': str(summary_json), 'summary_md': str(summary_md)}, ensure_ascii=False, indent=2))
PY

echo "[$(date '+%F %T')] integrated mainline validation complete" | tee -a "$RUN_LOG"
echo "summary_json=$SUMMARY_JSON" | tee -a "$RUN_LOG"
echo "summary_md=$SUMMARY_MD" | tee -a "$RUN_LOG"
