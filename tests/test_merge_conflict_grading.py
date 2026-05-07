from mygooglealertpapers.pipeline.dedup import _parse_conflict_assessment
from mygooglealertpapers.pipeline.merge import _apply_pubmed_doi_suppression, _build_conflict_assessment, _pick_preferred, _venue_equivalent


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


def test_pubmed_pmid_doi_is_suppressed_when_europepmc_and_openalex_agree():
    rows = [
        {'source_name': 'europepmc', 'query_type': 'pmid', 'matched': 1, 'title': 'Microglia Pyroptosis-Derived IL-18 Drives White Matter Injury in Developing Brain following Hypothermic Hypoxia-Ischemia', 'doi': '10.1007/s12264-026-01602-9', 'pmid': '41796421', 'pmcid': None, 'venue': 'Neurosci Bull', 'year': '2026'},
        {'source_name': 'openalex', 'query_type': 'title', 'matched': 1, 'title': 'Microglia Pyroptosis-Derived IL-18 Drives White Matter Injury in Developing Brain following Hypothermic Hypoxia-Ischemia', 'doi': '10.1007/s12264-026-01602-9', 'pmid': '41796421', 'pmcid': None, 'venue': 'Neuroscience Bulletin', 'year': '2026'},
        {'source_name': 'pubmed', 'query_type': 'pmid', 'matched': 1, 'title': 'Microglia Pyroptosis-Derived IL-18 Drives White Matter Injury in Developing Brain following Hypothermic Hypoxia-Ischemia.', 'doi': '10.1016/S0003-4975(97)82824-X', 'pmid': '41796421', 'pmcid': '7190443', 'venue': 'Neuroscience bulletin', 'year': '2026'},
    ]
    adjusted, suppressed = _apply_pubmed_doi_suppression(rows)
    pubmed_row = next(row for row in adjusted if row['source_name'] == 'pubmed')
    assert pubmed_row['doi'] is None
    assert len(suppressed) == 1
    assert suppressed[0]['query_type'] == 'pmid'
    assert suppressed[0]['suppression_reason'] == 'pubmed_pmid_doi_conflicts_with_consensus'
    assessment = _build_conflict_assessment(adjusted, ['title', 'venue', 'year', 'doi', 'pmid'])
    assert assessment['canonical_blocked'] is False


def test_pubmed_pmid_doi_is_suppressed_when_europepmc_only_disagrees_on_pubmed_url_chain():
    rows = [
        {'source_name': 'europepmc', 'query_type': 'pmid', 'matched': 1, 'title': 'Quantitative susceptibility mapping in pediatric neuroimaging: a systematic review of applications and advancements', 'doi': '10.1007/s00247-026-06565-7', 'pmid': '41801366', 'pmcid': None, 'venue': 'Pediatr Radiol', 'year': '2026'},
        {'source_name': 'pubmed', 'query_type': 'pmid', 'matched': 1, 'title': 'Quantitative susceptibility mapping in pediatric neuroimaging: a systematic review of applications and advancements.', 'doi': '10.1111/acer.14928', 'pmid': '41801366', 'pmcid': 'PMC9183007', 'venue': 'Pediatric radiology', 'year': '2026'},
    ]
    adjusted, suppressed = _apply_pubmed_doi_suppression(
        rows,
        candidate_year='2026',
        candidate_url='https://pubmed.ncbi.nlm.nih.gov/41801366/',
        candidate_pmcid=None,
    )
    pubmed_row = next(row for row in adjusted if row['source_name'] == 'pubmed')
    assert pubmed_row['doi'] is None
    assert len(suppressed) == 1
    assert suppressed[0]['suppression_reason'] == 'pubmed_pmid_doi_conflicts_with_europepmc_pmid_consensus'
    assessment = _build_conflict_assessment(adjusted, ['title', 'venue', 'year', 'doi', 'pmid'])
    assert assessment['canonical_blocked'] is False


def test_legacy_conflict_payload_with_identifier_disagreement_still_blocks():
    assessment = _parse_conflict_assessment('{"doi": ["10.1/a", "10.1/b"]}')
    assert assessment['canonical_blocked'] is True
    assert assessment['canonical_block_reason'].startswith('legacy_severe_conflict:')


def test_venue_abbreviation_and_full_name_are_equivalent():
    assert _venue_equivalent('JACC', 'Journal of the American College of Cardiology') is True


def test_venue_alias_conflict_is_not_severe():
    rows = [
        {'title': 'Paper A', 'venue': 'JACC', 'year': '2026', 'doi': '10.1000/aaa', 'pmid': None},
        {'title': 'Paper A', 'venue': 'Journal of the American College of Cardiology', 'year': '2026', 'doi': '10.1000/aaa', 'pmid': None},
    ]
    assessment = _build_conflict_assessment(rows, ['title', 'venue', 'year', 'doi', 'pmid'])
    assert assessment['graded_conflicts']['venue']['grade'] == 'A'
    assert assessment['conflict_grade_max'] == 'A'
    assert assessment['canonical_blocked'] is False


def test_pubmed_is_fallback_only_for_title_venue_and_doi():
    rows = [
        {'source_name': 'pubmed', 'query_type': 'title', 'title': 'PubMed Title', 'venue': 'PubMed Venue', 'doi': '10.1/pubmed', 'pmid': '123', 'pmcid': 'PMC123'},
        {'source_name': 'crossref', 'query_type': 'doi', 'title': 'Crossref Title', 'venue': 'Crossref Venue', 'doi': '10.1/crossref', 'pmid': None, 'pmcid': None},
    ]
    preferred_title, title_trace = _pick_preferred(rows, 'title')
    preferred_venue, venue_trace = _pick_preferred(rows, 'venue')
    preferred_doi, doi_trace = _pick_preferred(rows, 'doi')
    preferred_pmid, pmid_trace = _pick_preferred(rows, 'pmid')

    assert preferred_title == 'Crossref Title'
    assert preferred_venue == 'Crossref Venue'
    assert preferred_doi == '10.1/crossref'
    assert preferred_pmid == '123'
    assert all(not item.startswith('pubmed[') for item in title_trace)
    assert all(not item.startswith('pubmed[') for item in venue_trace)
    assert all(not item.startswith('pubmed[') for item in doi_trace)
    assert any(item.startswith('pubmed[') for item in pmid_trace)


def test_pubmed_can_still_supply_abstract_when_no_other_source_has_one():
    rows = [
        {'source_name': 'crossref', 'query_type': 'doi', 'abstract': None},
        {'source_name': 'openalex', 'query_type': 'doi_batch', 'abstract': None},
        {'source_name': 'pubmed', 'query_type': 'title', 'abstract': 'Useful abstract from PubMed'},
    ]
    preferred_abstract, abstract_trace = _pick_preferred(rows, 'abstract')
    assert preferred_abstract == 'Useful abstract from PubMed'
    assert any(item.startswith('pubmed[') for item in abstract_trace)
