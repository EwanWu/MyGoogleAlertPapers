from mygooglealertpapers.pipeline.dedup import _parse_conflict_assessment
from mygooglealertpapers.pipeline.merge import _apply_pubmed_doi_suppression, _build_conflict_assessment


def test_doi_conflict_is_grade_c_and_blocks_canonicalization():
    rows = [
        {'title': 'Paper A', 'venue': 'Journal X', 'year': '2026', 'doi': '10.1000/aaa', 'pmid': None},
        {'title': 'Paper A', 'venue': 'Journal X', 'year': '2026', 'doi': '10.1000/bbb', 'pmid': None},
    ]
    assessment = _build_conflict_assessment(rows, ['title', 'venue', 'year', 'doi', 'pmid'])
    assert assessment['conflict_grade_max'] == 'C'
    assert assessment['graded_conflicts']['doi']['grade'] == 'C'
    assert assessment['canonical_blocked'] is True
    assert 'doi' in assessment['severe_conflict_fields']


def test_year_off_by_one_is_moderate_not_blocking():
    rows = [
        {'title': 'Paper A', 'venue': 'Journal X', 'year': '2025', 'doi': '10.1000/aaa', 'pmid': None},
        {'title': 'Paper A', 'venue': 'Journal X', 'year': '2026', 'doi': '10.1000/aaa', 'pmid': None},
    ]
    assessment = _build_conflict_assessment(rows, ['title', 'venue', 'year', 'doi', 'pmid'])
    assert assessment['conflict_grade_max'] == 'B'
    assert assessment['graded_conflicts']['year']['grade'] == 'B'
    assert assessment['canonical_blocked'] is False


def test_title_truncation_variant_is_moderate_not_severe():
    rows = [
        {'title': 'Comparison of 2D and 3D carotid plaque analysis and longitudinal', 'venue': 'Journal A', 'year': '2026', 'doi': None, 'pmid': None},
        {'title': 'Comparison of 2D and 3D carotid plaque analysis and longitudinal in vivo ultrasound registration using 3D histology', 'venue': 'Journal A', 'year': '2026', 'doi': None, 'pmid': None},
    ]
    assessment = _build_conflict_assessment(rows, ['title', 'venue', 'year', 'doi', 'pmid'])
    assert assessment['graded_conflicts']['title']['grade'] == 'B'
    assert assessment['canonical_blocked'] is False


def test_pubmed_title_doi_is_suppressed_when_crossref_and_openalex_agree():
    rows = [
        {'source_name': 'crossref', 'query_type': 'title', 'matched': 1, 'doi': '10.1/good', 'pmid': None, 'pmcid': None, 'venue': 'Journal A', 'year': '2026'},
        {'source_name': 'openalex', 'query_type': 'title', 'matched': 1, 'doi': '10.1/good', 'pmid': '123', 'pmcid': None, 'venue': 'Journal A', 'year': '2026'},
        {'source_name': 'pubmed', 'query_type': 'title', 'matched': 1, 'doi': '10.1/bad', 'pmid': '123', 'pmcid': None, 'venue': 'Journal A', 'year': '2026'},
    ]
    adjusted, suppressed = _apply_pubmed_doi_suppression(rows)
    pubmed_row = next(row for row in adjusted if row['source_name'] == 'pubmed')
    assert pubmed_row['doi'] is None
    assert len(suppressed) == 1
    assert suppressed[0]['suppressed_value'] == '10.1/bad'
    assert suppressed[0]['consensus_doi'] == '10.1/good'


def test_pubmed_title_doi_is_suppressed_when_crossref_matches_candidate_url_and_venue():
    rows = [
        {'source_name': 'crossref', 'query_type': 'title', 'matched': 1, 'doi': '10.3390/cancers18061005', 'pmid': None, 'pmcid': None, 'venue': 'Cancers', 'year': '2026'},
        {'source_name': 'pubmed', 'query_type': 'title', 'matched': 1, 'doi': '10.2196/55799', 'pmid': '41899606', 'pmcid': 'PMC11292156', 'venue': 'Cancers', 'year': '2026'},
    ]
    adjusted, suppressed = _apply_pubmed_doi_suppression(
        rows,
        candidate_venue='Cancers',
        candidate_year='2026',
        candidate_url='https://www.mdpi.com/2072-6694/18/6/1005',
        candidate_pmcid=None,
    )
    pubmed_row = next(row for row in adjusted if row['source_name'] == 'pubmed')
    assert pubmed_row['doi'] is None
    assert suppressed[0]['suppression_reason'] == 'pubmed_title_doi_conflicts_with_crossref_plus_candidate_url'


def test_pubmed_title_doi_is_suppressed_when_candidate_pmcid_conflicts():
    rows = [
        {'source_name': 'crossref', 'query_type': 'title', 'matched': 1, 'doi': '10.3389/fneur.2026.1677672', 'pmid': None, 'pmcid': None, 'venue': 'Frontiers in Neurology', 'year': '2026'},
        {'source_name': 'pubmed', 'query_type': 'title', 'matched': 1, 'doi': '10.1148/radiol.2020190643', 'pmid': '41859416', 'pmcid': 'PMC7965103', 'venue': 'Frontiers in neurology', 'year': '2026'},
    ]
    adjusted, suppressed = _apply_pubmed_doi_suppression(
        rows,
        candidate_venue='Frontiers in Neurology',
        candidate_year='2026',
        candidate_url='https://pmc.ncbi.nlm.nih.gov/articles/PMC12995673/',
        candidate_pmcid='PMC12995673',
    )
    pubmed_row = next(row for row in adjusted if row['source_name'] == 'pubmed')
    assert pubmed_row['doi'] is None
    assert suppressed[0]['suppression_reason'] == 'pubmed_title_doi_conflicts_with_candidate_pmcid'


def test_legacy_conflict_payload_with_identifier_disagreement_still_blocks():
    assessment = _parse_conflict_assessment('{"doi": ["10.1/a", "10.1/b"]}')
    assert assessment['canonical_blocked'] is True
    assert assessment['canonical_block_reason'].startswith('legacy_severe_conflict:')
