from __future__ import annotations

import json
import sqlite3
import statistics
from collections import Counter

from mygooglealertpapers.enrich.arxiv import query_arxiv
from mygooglealertpapers.enrich.europepmc import query_europepmc

DB = 'data/mgap_pkg3_guardrail_100.db'


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        '''
        SELECT candidate_id, norm_title, doi_extracted, pmid_extracted, arxiv_id_extracted,
               first_author_family, venue_guess, year_guess, url_canonical
        FROM paper_candidate_normalized
        ORDER BY id ASC
        LIMIT 100
        '''
    ).fetchall()

    europepmc_records = []
    arxiv_records = []

    for row in rows:
        rec_epmc = query_europepmc(
            row['candidate_id'],
            doi=row['doi_extracted'],
            pmid=row['pmid_extracted'],
            title=row['norm_title'],
            first_author_family=row['first_author_family'],
            venue_hint=row['venue_guess'],
            query_year=row['year_guess'],
        )
        if rec_epmc:
            europepmc_records.append(rec_epmc)

        rec_arxiv = None
        if row['arxiv_id_extracted'] or ('arxiv.org/' in (row['url_canonical'] or '')):
            rec_arxiv = query_arxiv(
                row['candidate_id'],
                arxiv_id=row['arxiv_id_extracted'],
                title=None if row['arxiv_id_extracted'] else row['norm_title'],
                first_author_family=row['first_author_family'],
                query_year=row['year_guess'],
            )
        elif row['norm_title']:
            rec_arxiv = query_arxiv(
                row['candidate_id'],
                title=row['norm_title'],
                first_author_family=row['first_author_family'],
                query_year=row['year_guess'],
            )
        if rec_arxiv:
            arxiv_records.append(rec_arxiv)

    def summarize(name, records):
        matched = [r for r in records if r.matched]
        latencies = [r.latency_ms for r in records]
        print(f'=== {name} ===')
        print(json.dumps({
            'tested': len(records),
            'matched': len(matched),
            'match_rate': round(len(matched) / len(records), 4) if records else 0,
            'avg_latency_ms': round(statistics.mean(latencies), 1) if latencies else None,
            'median_latency_ms': round(statistics.median(latencies), 1) if latencies else None,
            'with_abstract': sum(1 for r in matched if r.abstract),
            'with_doi': sum(1 for r in matched if r.doi),
            'with_pmid': sum(1 for r in matched if r.pmid),
        }, ensure_ascii=False))
        sample = []
        for r in matched[:8]:
            sample.append({
                'candidate_id': r.candidate_id,
                'query_type': r.query_type,
                'title': r.title,
                'venue': r.venue,
                'doi': r.doi,
                'pmid': r.pmid,
                'latency_ms': r.latency_ms,
            })
        print(json.dumps(sample, ensure_ascii=False, indent=2))

    summarize('europepmc', europepmc_records)
    summarize('arxiv', arxiv_records)


if __name__ == '__main__':
    main()
