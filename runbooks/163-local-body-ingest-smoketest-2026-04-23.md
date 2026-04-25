# 163-local body ingest smoke-test (2026-04-23)

## Status: ✅ PASSED

## What was tested
End-to-end pipeline from Windows-local body fetch → import → parse → normalize.

## Test conditions
- Chrome remained open on Windows with active 163 unread inbox
- `scholar_index.jsonl` baseline: 277 rows (3 pages, indexed 2026-04-23 14:19 CST)
- Body fetch: `run_163_body_fetch_sample.ps1 -Limit 1` on Windows
- Import: `import-local-bodies --input scholar_body_fetch.jsonl --limit 10`
- DB: fresh `/tmp/mgap_163_local_smoketest.db`

## Results

### Body fetch
| Field | Value |
|---|---|
| status | completed |
| success | 1 |
| failures | 0 |
| body_source | iframe |
| body_iframe_id | 1776915017057_frameBody |
| body_iframe_url | https://mail.163.com/js6/read/readhtml3.jsp?mid=733:xtbC3RkHkGnpELkTxgAA3v&... |
| body_score | 9309 |
| body_text len | 3669 |
| body_html len | 33472 |

### Pipeline
| Step | Result |
|---|---|
| import-local-bodies | processed=1, imported=1, skipped=0, no_body=0 |
| parse-mails | Found 1 unparsed Scholar mail(s) |
| normalize-candidates | Found 8 unnormalized → 8 normalized |
| DOI extracted | 2 |

### Canonical URL domains (normalized)
- www.sciencedirect.com: 4
- academic.oup.com: 1
- ieeexplore.ieee.org: 1
- link.springer.com: 1
- www.researchsquare.com: 1

## Root-cause bugs found and fixed this session

1. **iframe content missed** — 163 Scholar alert emails render body inside `<iframe id$="_frameBody">`, not the outer chrome document. `EXTRACT_MAIL_BODY_JS` was running on top frame and getting no Scholar content.
   - Fix: detect `iframe[id$="_frameBody"]` → `contentDocument.body.innerHTML` before scanning main document
   - Also increased post-click wait: 1.8s → 3.5s for iframe to load

2. **void(0) link wrapping** — earlier test showed 163 outer chrome page wrapped article links as `href="javascript:void(0)"` with real URL in onclick. After fix #1, this no longer applies to the iframe body (which has clean `href="https://scholar.google.com/scholar_url?url=..."`).

## Files modified
- `scripts/windows_local/read_163_scholar_with_manual_pause.py` — EXTRACT_MAIL_BODY_JS iframe priority + wait increase + new diagnostic fields

## Next
1. Fetch 10-20 more samples with same setup
2. Confirm stable candidate yield across different alert types (related_work vs new_article vs citation)
3. Proceed to full body fetch of all 277 indexed mails
