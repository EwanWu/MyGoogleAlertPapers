from mygooglealertpapers.mail.candidate_extractor import extract_candidates
from mygooglealertpapers.mail.message_parser import ParsedEmail


def test_extract_candidates_from_simple_html_anchor_context():
    html = """
    <html><body>
      <div>
        <a href="https://scholar.google.com/scholar_url?url=https%3A%2F%2Fexample.org%2Fpaper1&hl=en">[PDF] A long enough paper title for extraction testing in scholar email</a>
      </div>
      <div>Author A, Author B - Journal of Tests, 2026</div>
    </body></html>
    """
    parsed = ParsedEmail(
        message_id="m1",
        subject="new articles",
        from_address="scholaralerts-noreply@google.com",
        headers={},
        body_text="",
        body_html=html,
        body_hash="hash",
    )
    candidates = extract_candidates(parsed, mail_uid="123")
    assert len(candidates) == 1
    assert candidates[0].raw_title == "A long enough paper title for extraction testing in scholar email"
    assert candidates[0].raw_link == "https://example.org/paper1"
    assert candidates[0].target_url == "https://example.org/paper1"
    assert candidates[0].resource_type_hint == "pdf"
    assert candidates[0].venue_guess == "Journal of Tests"
    assert candidates[0].year_guess == "2026"
