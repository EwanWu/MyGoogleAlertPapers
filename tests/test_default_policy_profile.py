from __future__ import annotations

from mygooglealertpapers.config import _default_policy_profile


def test_builtin_default_policy_profile_promotes_post_openalex_crossref_suppression_runtime():
    profile = _default_policy_profile()

    assert profile.name == 'builtin_identifier_plus_title_core_same_batch_cluster_post_openalex_skip_crossref_url_only_openalex_top5_url_only_arxiv_gate_default'
    assert profile.merge_value('normalized_only_fallback') is True
    assert profile.merge_value('fallback_reject_author_blob_identifier_aware') is True
    assert profile.runtime_value('enabled_lanes') == ['identifier_fastpath', 'title_core']
    assert profile.runtime_value('lane_order') == ['identifier_fastpath', 'title_core', 'biomedical_fallback', 'slow_fallback']
    assert profile.runtime_value('library_prelink_enabled') is True
    assert profile.runtime_value('same_batch_clustering_enabled') is True
    assert profile.runtime_value('title_lane_post_openalex_skip_subreasons_by_provider') == {'crossref': ['url_canonical_only']}
    assert profile.runtime_value('openalex_title_per_page_by_subreason') == {'url_canonical_only': 5}
    assert profile.runtime_value('openalex_title_pick_best_accepted_subreasons') == ['url_canonical_only']
    assert profile.runtime_value('openalex_title_extra_result_require_arxiv_id_subreasons') == ['url_canonical_only']
    assert profile.provider_value('openalex', 'doi_batch_enabled') is True
    assert profile.provider_value('crossref', 'title_payload_reuse_enabled') is True
