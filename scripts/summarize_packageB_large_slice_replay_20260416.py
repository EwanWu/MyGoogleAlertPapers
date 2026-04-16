from __future__ import annotations

import json
import sqlite3
from pathlib import Path

project = Path(__file__).resolve().parents[1]
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
    encoding='utf-8',
)

print(json.dumps(summary, ensure_ascii=False, indent=2))
