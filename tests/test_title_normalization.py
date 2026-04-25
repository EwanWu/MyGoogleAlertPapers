from mygooglealertpapers.enrich.base import title_similarity
from mygooglealertpapers.normalize.title import make_title_key


def test_make_title_key_ignores_rendering_symbols():
    a = 'Large Language Models @ MRI: "Fast"-<Robust>* Reconstruction'
    b = 'Large Language Models MRI Fast Robust Reconstruction'
    assert make_title_key(a) == make_title_key(b)


def test_title_similarity_treats_symbol_only_differences_as_same_title():
    a = "Graph-based MRI @ scale: 'fast' \"robust\" <reconstruction>*"
    b = 'Graph based MRI scale fast robust reconstruction'
    assert title_similarity(a, b) == 1.0
