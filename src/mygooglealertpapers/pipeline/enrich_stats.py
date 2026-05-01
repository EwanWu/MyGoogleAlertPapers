from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def build_enrichment_stats(db_path: Path) -> str:
    with sqlite3.connect(db_path) as conn:
        total = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized').fetchone()[0]
        source_total = conn.execute('SELECT COUNT(*) FROM source_record').fetchone()[0]
        matched_total = conn.execute('SELECT COUNT(*) FROM source_record WHERE matched = 1').fetchone()[0]
        dispatch_stats = None
        notes_row = conn.execute(
            "SELECT notes FROM batch_run WHERE stage = 'enrich_candidates' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if notes_row and notes_row[0]:
            try:
                dispatch_stats = json.loads(notes_row[0])
            except Exception:
                dispatch_stats = None
        lines = [
            'Enrichment stats',
            f'- normalized candidates: {total}',
            f'- source records: {source_total}',
            f'- matched source records: {matched_total}',
        ]
        if dispatch_stats:
            lines.extend([
                '- dispatch summary:',
                f"  - candidate count: {dispatch_stats.get('candidate_count')}",
                f"  - unresolved candidates: {dispatch_stats.get('unresolved_candidate_count')}",
                f"  - library prelink enabled: {dispatch_stats.get('library_prelink_enabled')}",
                f"  - library prelinked candidates: {dispatch_stats.get('library_prelinked_candidate_count')}",
                f"  - library prelink rule counts: {dispatch_stats.get('library_prelink_rule_counts')}",
                f"  - same-batch clustering enabled: {dispatch_stats.get('same_batch_clustering_enabled')}",
                f"  - same-batch cluster groups: {dispatch_stats.get('same_batch_cluster_group_count')}",
                f"  - same-batch clustered candidates: {dispatch_stats.get('same_batch_clustered_candidate_count')}",
                f"  - same-batch cluster rule counts: {dispatch_stats.get('same_batch_cluster_rule_counts')}",
                f"  - same-batch naive groups: {dispatch_stats.get('same_batch_cluster_naive_group_count')}",
                f"  - same-batch effective groups: {dispatch_stats.get('same_batch_cluster_effective_group_count')}",
                f"  - same-batch estimated group savings: {dispatch_stats.get('same_batch_cluster_group_savings_estimate')}",
                f"  - runnable provider intents: {dispatch_stats.get('runnable_provider_intents')}",
                f"  - pre-experimental runnable provider intents: {dispatch_stats.get('pre_experimental_runnable_provider_intents')}",
                f"  - experimental skipped provider intents: {dispatch_stats.get('experimental_skipped_provider_intents')}",
                f"  - prelink-skipped provider intents: {dispatch_stats.get('prelink_skipped_provider_intents')}",
                f"  - unresolved provider intents: {dispatch_stats.get('unresolved_provider_intents')}",
                f"  - dispatch groups: {dispatch_stats.get('dispatch_group_count')}",
                f"  - pre-experimental dispatch groups: {dispatch_stats.get('pre_experimental_dispatch_group_count')}",
                f"  - dispatch requests: {dispatch_stats.get('dispatch_request_count')}",
                f"  - processed runnable intents: {dispatch_stats.get('processed_runnable_intents', dispatch_stats.get('runnable_provider_intents'))}/{dispatch_stats.get('runnable_provider_intents')}",
                f"  - request savings vs processed intents: {dispatch_stats.get('request_savings_vs_processed_intents', 'n/a')}",
                f"  - request savings vs total planned intents: {dispatch_stats.get('request_savings_vs_total_planned_intents', dispatch_stats.get('request_savings_vs_runnable_intents'))}",
                f"  - lane order: {dispatch_stats.get('lane_order')}",
                f"  - enabled lanes: {dispatch_stats.get('enabled_lanes')}",
                f"  - lane group counts: {dispatch_stats.get('lane_group_counts')}",
                f"  - lane intent counts: {dispatch_stats.get('lane_intent_counts')}",
                f"  - lane processed intents: {dispatch_stats.get('lane_processed_intents')}",
                f"  - lane dispatch requests: {dispatch_stats.get('lane_dispatch_request_count')}",
                f"  - lane request budgets: {dispatch_stats.get('lane_request_budgets')}",
                f"  - lane runtime budget seconds: {dispatch_stats.get('lane_runtime_budget_seconds')}",
                f"  - lane stop reasons: {dispatch_stats.get('lane_stop_reasons')}",
                f"  - lane skipped groups: {dispatch_stats.get('lane_skipped_group_count')}",
                f"  - lane skipped intents: {dispatch_stats.get('lane_skipped_intents')}",
                f"  - lane elapsed ms: {dispatch_stats.get('lane_elapsed_ms')}",
                f"  - cache-hit groups: {dispatch_stats.get('cache_hit_group_count')}",
                f"  - fanout candidates: {dispatch_stats.get('fanout_candidate_count')}",
                f"  - title-lane groups: {dispatch_stats.get('title_lane_group_count')}",
                f"  - title-lane intents: {dispatch_stats.get('title_lane_intent_count')}",
                f"  - title-lane requests: {dispatch_stats.get('title_lane_request_count')}",
                f"  - title-lane group counts by reason: {dispatch_stats.get('title_lane_group_counts_by_reason')}",
                f"  - title-lane request counts by reason: {dispatch_stats.get('title_lane_request_counts_by_reason')}",
                f"  - title-lane group counts by provider: {dispatch_stats.get('title_lane_group_counts_by_provider')}",
                f"  - title-lane request counts by provider: {dispatch_stats.get('title_lane_request_counts_by_provider')}",
                f"  - title-lane provider/reason groups: {dispatch_stats.get('title_lane_group_counts_by_provider_reason')}",
                f"  - title-lane provider/reason requests: {dispatch_stats.get('title_lane_request_counts_by_provider_reason')}",
                f"  - identifier-gap title groups by subreason: {dispatch_stats.get('title_lane_identifier_gap_group_counts_by_subreason')}",
                f"  - identifier-gap title requests by subreason: {dispatch_stats.get('title_lane_identifier_gap_request_counts_by_subreason')}",
                f"  - identifier-gap provider/subreason groups: {dispatch_stats.get('title_lane_identifier_gap_group_counts_by_provider_subreason')}",
                f"  - identifier-gap provider/subreason requests: {dispatch_stats.get('title_lane_identifier_gap_request_counts_by_provider_subreason')}",
                f"  - title-lane cache-hit groups: {dispatch_stats.get('title_lane_cache_hit_group_count')}",
                f"  - title-lane cache-hit by reason: {dispatch_stats.get('title_lane_cache_hit_counts_by_reason')}",
                f"  - title-lane cache-hit by provider: {dispatch_stats.get('title_lane_cache_hit_counts_by_provider')}",
                f"  - experimental title skip rules: {dispatch_stats.get('experimental_title_skip_subreasons_by_provider')}",
                f"  - openalex title per-page by subreason: {dispatch_stats.get('openalex_title_per_page_by_subreason')}",
                f"  - openalex title pick-best subreasons: {dispatch_stats.get('openalex_title_pick_best_accepted_subreasons')}",
                f"  - openalex title extra-result arxiv-gated subreasons: {dispatch_stats.get('openalex_title_extra_result_require_arxiv_id_subreasons')}",
                f"  - openalex title extra-result targeted groups: {dispatch_stats.get('openalex_title_extra_result_targeted_group_count')}",
                f"  - openalex title extra-result targeted groups by gate status: {dispatch_stats.get('openalex_title_extra_result_targeted_group_counts_by_gate_status')}",
                f"  - openalex title extra-result effective groups: {dispatch_stats.get('openalex_title_extra_result_effective_group_count')}",
                f"  - openalex title extra-result blocked groups: {dispatch_stats.get('openalex_title_extra_result_blocked_group_count')}",
                f"  - experimental skipped groups: {dispatch_stats.get('experimental_skipped_group_count')}",
                f"  - experimental skipped intents: {dispatch_stats.get('experimental_skipped_intent_count')}",
                f"  - experimental skipped groups by provider: {dispatch_stats.get('experimental_skipped_group_counts_by_provider')}",
                f"  - experimental skipped groups by reason: {dispatch_stats.get('experimental_skipped_group_counts_by_reason')}",
                f"  - experimental skipped groups by title subreason: {dispatch_stats.get('experimental_skipped_group_counts_by_title_subreason')}",
                f"  - post-openalex suppressed groups: {dispatch_stats.get('post_openalex_suppressed_group_count')}",
                f"  - post-openalex suppressed groups by provider: {dispatch_stats.get('post_openalex_suppressed_group_counts_by_provider')}",
                f"  - post-openalex suppressed groups by reason: {dispatch_stats.get('post_openalex_suppressed_group_counts_by_reason')}",
                f"  - post-openalex suppressed groups by title subreason: {dispatch_stats.get('post_openalex_suppressed_group_counts_by_title_subreason')}",
                f"  - post-openalex unsuppressed targeted groups: {dispatch_stats.get('post_openalex_unsuppressed_targeted_group_count')}",
                f"  - post-openalex unsuppressed targeted groups by provider: {dispatch_stats.get('post_openalex_unsuppressed_targeted_group_counts_by_provider')}",
                f"  - post-openalex unsuppressed targeted groups by reason: {dispatch_stats.get('post_openalex_unsuppressed_targeted_group_counts_by_reason')}",
                f"  - post-openalex unsuppressed targeted groups by arxiv bucket: {dispatch_stats.get('post_openalex_unsuppressed_targeted_group_counts_by_arxiv_bucket')}",
                f"  - post-openalex unsuppressed targeted groups by reason/arxiv bucket: {dispatch_stats.get('post_openalex_unsuppressed_targeted_group_counts_by_reason_arxiv_bucket')}",
                f"  - post-openalex unsuppressed targeted groups by reason/title subreason: {dispatch_stats.get('post_openalex_unsuppressed_targeted_group_counts_by_reason_title_subreason')}",
                f"  - post-openalex unsuppressed targeted groups by title subreason: {dispatch_stats.get('post_openalex_unsuppressed_targeted_group_counts_by_title_subreason')}",
                f"  - post-prelink residual title groups: {dispatch_stats.get('title_lane_post_prelink_residual_group_count')}",
                f"  - post-prelink residual title intents: {dispatch_stats.get('title_lane_post_prelink_residual_intent_count')}",
                f"  - post-prelink residual title requests: {dispatch_stats.get('title_lane_post_prelink_residual_request_count')}",
                f"  - shared title reuse groups: {dispatch_stats.get('shared_title_reuse_group_count')}",
                f"  - shared title reuse intents: {dispatch_stats.get('shared_title_reuse_intent_count')}",
                f"  - shared title reuse requests: {dispatch_stats.get('shared_title_reuse_request_count')}",
                f"  - shared title reuse request savings: {dispatch_stats.get('shared_title_reuse_request_savings')}",
                f"  - shared title reuse request savings by provider: {dispatch_stats.get('shared_title_reuse_request_savings_by_provider')}",
            ])
        lines.append('- provider breakdown:')
        for provider, count, matched in conn.execute('SELECT source_name, COUNT(*), SUM(CASE WHEN matched = 1 THEN 1 ELSE 0 END) FROM source_record GROUP BY source_name ORDER BY source_name'):
            lines.append(f'  - {provider}: {matched}/{count} matched')
        return '\n'.join(lines)
