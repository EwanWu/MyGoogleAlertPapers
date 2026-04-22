"""Test fallback_reject_author_blob_identifier_aware: only fires when no strong identifier."""

from pathlib import Path

from mygooglealertpapers.config import PolicyProfile, Settings
from mygooglealertpapers.normalize.text import clean_title


def _make_settings(merge_rules: dict[str, object]) -> Settings:
    """Build a minimal Settings with a policy profile for merge rule testing."""
    profile = PolicyProfile(
        name='test_author_blob_fb',
        path=None,
        provider_rules={},
        merge_rules=merge_rules,
        replay_defaults={},
        raw={},
    )
    return Settings(
        imap_host=None,
        imap_port=993,
        imap_username=None,
        imap_password=None,
        imap_mailbox='INBOX',
        sqlite_path=str(Path('/tmp/test_author_blob_fb.db')),
        log_level='INFO',
        workspace_root=Path('/tmp'),
        config_source='test',
        imap_account=None,
        crossref_mailto=None,
        openalex_email=None,
        semantic_scholar_api_key=None,
        unpaywall_email=None,
        policy_profile=profile,
    )


def _guardrail(settings: Settings, norm_title, norm_doi=None, norm_pmid=None, norm_pmcid=None, **kwargs):
    """Call _normalized_fallback_guardrail with only the fields relevant to this test."""
    from mygooglealertpapers.pipeline.merge import _normalized_fallback_guardrail
    return _normalized_fallback_guardrail(
        settings,
        norm_title=norm_title,
        norm_authors_json=kwargs.get('norm_authors_json'),
        norm_venue_guess=kwargs.get('norm_venue_guess'),
        norm_year_guess=kwargs.get('norm_year_guess'),
        norm_doi=norm_doi,
        norm_pmid=norm_pmid,
        norm_pmcid=norm_pmcid,
        unmatched_rows=kwargs.get('unmatched_rows', []),
    )


class TestFallbackRejectAuthorBlobIdentifierAware:
    """Only fires when has_identifier=False and title matches author-blob pattern."""

    def test_fires_when_no_identifier_and_author_blob(self):
        """With DOI present, identifier-aware author-blob rule must NOT fire."""
        settings = _make_settings({'fallback_reject_author_blob_identifier_aware': True})
        result = _guardrail(
            settings,
            norm_title="Huan Yang 1 Yunchao Chen 1 Teng Ma 1 Jizhen Feng 1 Chencui Huang 3",
            norm_doi="10.1016/j.hrthm.2026.03.1889",  # strong identifier present
        )
        assert result['decision'] == 'accept', (
            f"With DOI present, author_blob rule should NOT fire. Got: {result['decision']}"
        )

    def test_blocks_when_no_identifier_and_author_blob(self):
        """Without DOI, the identifier-aware rule must reject author-blob."""
        settings = _make_settings({'fallback_reject_author_blob_identifier_aware': True})
        result = _guardrail(
            settings,
            norm_title="Huan Yang 1 Yunchao Chen 1 Teng Ma 1 Jizhen Feng 1 Chencui Huang 3",
            norm_doi=None,
            norm_pmid=None,
            norm_pmcid=None,
        )
        assert result['decision'] == 'reject', (
            f"Without DOI and with author-blob title, should reject. Got: {result['decision']}"
        )
        assert 'title_looks_like_author_footnote_blob_identifier_aware' in result['reasons']

    def test_legitimate_paper_not_blocked_without_doi(self):
        """A normal English title should never be rejected even without DOI."""
        cases = [
            ("PRESERVE: Randomized trial of intensive vs standard blood pressure control in small vessel disease", None),
            ("Spironolactone, Early Acute eGFR Changes, and Clinical Outcomes in Heart Failure with Preserved Ejection Fraction", None),
            ("Vascular and Hematologic Disorders", None),
            ("Left Bundle Branch Area Stylet-Driven Lead: Performance, Safety and Quality of Life at 12 Months", None),
        ]
        settings = _make_settings({'fallback_reject_author_blob_identifier_aware': True})
        for title, doi in cases:
            result = _guardrail(settings, norm_title=title, norm_doi=doi, norm_pmid=None, norm_pmcid=None)
            assert result['decision'] != 'reject', (
                f"Legitimate title '{title[:50]}' should not be rejected. "
                f"Got: {result['decision']}, reasons: {result['reasons']}"
            )

    def test_identifier_present_blocks_even_with_author_blob(self):
        """PMID is a strong identifier too — with it present, block must not fire."""
        settings = _make_settings({'fallback_reject_author_blob_identifier_aware': True})
        result = _guardrail(
            settings,
            norm_title="Huan Yang 1 Yunchao Chen 1 Teng Ma 1 Jizhen Feng 1 Chencui Huang 3",
            norm_doi=None,
            norm_pmid="38293847",
        )
        assert result['decision'] == 'accept', (
            f"With PMID present, author-blob rule should NOT fire. Got: {result['decision']}"
        )

    def test_old_fallback_reject_author_blob_still_works(self):
        """The old reject_author_blob (without identifier check) must still work."""
        settings = _make_settings({'fallback_reject_author_blob': True})
        result = _guardrail(
            settings,
            norm_title="Huan Yang 1 Yunchao Chen 1 Teng Ma 1 Jizhen Feng 1 Chencui Huang 3",
            norm_doi=None,
            norm_pmid=None,
            norm_pmcid=None,
        )
        assert result['decision'] == 'reject'
        assert 'title_looks_like_author_footnote_blob' in result['reasons']

    def test_identifier_aware_only_when_profile_enabled(self):
        """Without the identifier-aware flag, author_blob with DOI should NOT be blocked by that rule."""
        settings = _make_settings({'fallback_reject_author_blob_identifier_aware': False})
        result = _guardrail(
            settings,
            norm_title="Huan Yang 1 Yunchao Chen 1 Teng Ma 1 Jizhen Feng 1 Chencui Huang 3",
            norm_doi="10.1016/j.hrthm.2026.03.1889",
        )
        # Without the identifier-aware flag, the fallback guardrail should accept (no reject rules active)
        assert result['decision'] != 'reject'