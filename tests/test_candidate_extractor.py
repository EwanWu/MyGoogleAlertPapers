from mygooglealertpapers.mail.candidate_extractor import extract_candidates
from mygooglealertpapers.mail.message_parser import ParsedEmail


def test_extract_candidates_from_simple_html_anchor_context():
    html = """
    <html><body>
      <div>
        <a href="https://example.org/paper1">A long enough paper title for extraction testing in scholar email</a>
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
    assert candidates[0].raw_title.startswith("A long enough paper title")
    assert candidates[0].raw_link == "https://example.org/paper1"
