from __future__ import annotations

from mygooglealertpapers.config import _default_policy_profile


def test_builtin_default_policy_profile_promotes_identifier_plus_title_core_runtime():
    profile = _default_policy_profile()

    assert profile.name == 'builtin_identifier_plus_title_core_default'
    assert profile.merge_value('normalized_only_fallback') is True
    assert profile.merge_value('fallback_reject_author_blob_identifier_aware') is True
    assert profile.runtime_value('enabled_lanes') == ['identifier_fastpath', 'title_core']
    assert profile.runtime_value('lane_order') == ['identifier_fastpath', 'title_core', 'biomedical_fallback', 'slow_fallback']
    assert profile.provider_value('openalex', 'doi_batch_enabled') is True
    assert profile.provider_value('crossref', 'title_payload_reuse_enabled') is True
