from mygooglealertpapers.enrich.base import accept_result, looks_truncated_source_title, title_similarity
from mygooglealertpapers.normalize.title import make_title_key


def test_make_title_key_ignores_rendering_symbols():
    a = 'Large Language Models @ MRI: "Fast"-<Robust>* Reconstruction'
    b = 'Large Language Models MRI Fast Robust Reconstruction'
    assert make_title_key(a) == make_title_key(b)


def test_title_similarity_treats_symbol_only_differences_as_same_title():
    a = "Graph-based MRI @ scale: 'fast' \"robust\" <reconstruction>*"
    b = 'Graph based MRI scale fast robust reconstruction'
    assert title_similarity(a, b) == 1.0


def test_looks_truncated_source_title_detects_pdf_tail_noise():
    assert looks_truncated_source_title('Influences of Tongdu Tiaoshen acupuncture therapy on neurological function. .') is True
    assert looks_truncated_source_title('A clean full title') is False


def test_accept_result_salvages_truncated_title_when_author_and_venue_agree():
    assert accept_result(
        'Influences of Tongdu Tiaoshen acupuncture therapy on neurological function, inflammatory factors and carotid atherosclerotic plaques in patients diagnosed with. .',
        'Influences of Tongdu Tiaoshen acupuncture therapy on neurological function, inflammatory factors and carotid atherosclerotic plaques in patients diagnosed with atherosclerotic cerebral infarction',
        query_year='2026',
        result_year='2026',
        expected_family='Yang',
        authors_json='["Chijie Yang", "Yinyin Zhang"]',
        venue_hint='Malawi Medical Journal',
        provider_venue='Malawi Medical Journal',
        provider_name='openalex',
    ) is True


def test_accept_result_does_not_salvage_truncated_title_without_venue_and_author_support():
    assert accept_result(
        'Distinct neurologic state in patients with traumatic brain injury and hemorrhagic stroke during the stage of acute disorders of consciousness and the correlation with. .',
        'Distinct neurologic state in patients with traumatic brain injury and hemorrhagic stroke during the stage of acute disorders of consciousness and the correlation with the neurological prognosis: A multi-modal PET/rs-fMRI study',
        query_year='2026',
        result_year='2026',
        expected_family='Wang',
        authors_json='["Someone Else"]',
        venue_hint='NeuroImage: Clinical',
        provider_venue='NeuroImage Clinical',
        provider_name='openalex',
    ) is False
