from mygooglealertpapers.normalize.text import clean_abstract, clean_title, clean_venue


def test_clean_title_removes_tags_and_trailing_period():
    value = 'Dynamic Mode Decomposition (<scp>DMD</scp>) for Low-Latency Real-Time Cardiac MRI.'
    assert clean_title(value) == 'Dynamic Mode Decomposition ( DMD ) for Low-Latency Real-Time Cardiac MRI'


def test_clean_venue_normalizes_spacing_and_punctuation():
    assert clean_venue('  The Canadian journal of cardiology. ') == 'The Canadian journal of cardiology'


def test_clean_abstract_converts_openalex_inverted_index_to_text():
    value = '{"Hello": [0], "world": [1]}'
    assert clean_abstract(value) == 'Hello world'


def test_clean_abstract_strips_jats_tags():
    value = '<jats:sec><jats:title>Background</jats:title><jats:p>Test abstract.</jats:p></jats:sec>'
    cleaned = clean_abstract(value)
    assert cleaned is not None
    assert 'Background' in cleaned
    assert 'Test abstract.' in cleaned
