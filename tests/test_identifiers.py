from mygooglealertpapers.normalize.identifiers import canonicalize_url, extract_doi, extract_pmid, extract_pmcid


def test_extract_doi_from_url():
    text = 'https://doi.org/10.1002/mrm.70353'
    assert extract_doi(text) == '10.1002/mrm.70353'


def test_extract_pmid_from_pubmed_url():
    text = 'https://pubmed.ncbi.nlm.nih.gov/41802271/'
    assert extract_pmid(text) == '41802271'


def test_extract_pmcid_from_pmc_url():
    text = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12999256/'
    assert extract_pmcid(text) == 'PMC12999256'


def test_canonicalize_scholar_wrapper_url():
    wrapped = 'https://scholar.google.com/scholar_url?url=https%3A%2F%2Fexample.org%2Fpaper1&hl=en'
    assert canonicalize_url(wrapped) == 'https://example.org/paper1'
