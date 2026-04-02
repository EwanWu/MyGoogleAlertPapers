from mygooglealertpapers.mail.message_parser import ParsedEmail
from mygooglealertpapers.mail.scholar_detector import detect_google_scholar_alert


def test_detect_google_scholar_alert_from_address_match():
    parsed = ParsedEmail(
        message_id="1",
        subject="anything",
        from_address="Google Scholar Alerts <scholaralerts-noreply@google.com>",
        headers={},
        body_text="",
        body_html="",
        body_hash="x",
    )
    result = detect_google_scholar_alert(parsed)
    assert result.is_match is True
