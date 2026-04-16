from mygooglealertpapers.enrich.openalex import _extract_primary_location_fields


def test_extract_primary_location_fields_handles_null_source():
    item = {
        'primary_location': {
            'source': None,
            'landing_page_url': 'https://example.org/paper',
        }
    }

    venue, url = _extract_primary_location_fields(item)

    assert venue is None
    assert url == 'https://example.org/paper'


def test_extract_primary_location_fields_handles_missing_primary_location():
    venue, url = _extract_primary_location_fields({})

    assert venue is None
    assert url is None
