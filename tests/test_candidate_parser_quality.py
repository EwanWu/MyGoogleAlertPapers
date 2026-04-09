from mygooglealertpapers.mail.candidate_extractor import extract_candidates
from mygooglealertpapers.mail.message_parser import ParsedEmail


def test_snippet_with_only_year_does_not_become_venue():
    html = """
    <html><body>
      <div><a href="https://scholar.google.com/scholar_url?url=https%3A%2F%2Fexample.org%2Fpaper2">CTA versus TOF-MRA for circle of Willis segmentation</a></div>
      <div>A Vikström, L Zarrinkoob, M Johannesdottir - 2026</div>
    </body></html>
    """
    parsed = ParsedEmail(
        message_id="m2",
        subject="new articles",
        from_address="scholaralerts-noreply@google.com",
        headers={},
        body_text="",
        body_html=html,
        body_hash="h2",
    )
    candidates = extract_candidates(parsed, mail_uid="m2")
    assert len(candidates) == 1
    assert candidates[0].venue_guess is None
    assert candidates[0].year_guess == "2026"
