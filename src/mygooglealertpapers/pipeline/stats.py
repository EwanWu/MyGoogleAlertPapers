from __future__ import annotations

import sqlite3
from pathlib import Path
from urllib.parse import urlparse


def build_normalization_stats(db_path: Path) -> str:
    with sqlite3.connect(db_path) as conn:
        total = conn.execute('SELECT COUNT(*) FROM paper_candidate').fetchone()[0]
        normalized = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized').fetchone()[0]
        doi_count = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized WHERE doi_extracted IS NOT NULL').fetchone()[0]
        pmid_count = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized WHERE pmid_extracted IS NOT NULL').fetchone()[0]
        pmcid_count = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized WHERE pmcid_extracted IS NOT NULL').fetchone()[0]
        arxiv_count = conn.execute('SELECT COUNT(*) FROM paper_candidate_normalized WHERE arxiv_id_extracted IS NOT NULL').fetchone()[0]
        rows = conn.execute('SELECT url_canonical FROM paper_candidate_normalized WHERE url_canonical IS NOT NULL').fetchall()
        domain_counts: dict[str, int] = {}
        for (url,) in rows:
            domain = urlparse(url).netloc.lower()
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        top_domains = sorted(domain_counts.items(), key=lambda x: (-x[1], x[0]))[:10]
        lines = [
            'Normalization stats',
            f'- total candidates: {total}',
            f'- normalized candidates: {normalized}',
            f'- DOI extracted: {doi_count}',
            f'- PMID extracted: {pmid_count}',
            f'- PMCID extracted: {pmcid_count}',
            f'- arXiv extracted: {arxiv_count}',
            '- top canonical URL domains:',
        ]
        for domain, count in top_domains:
            lines.append(f'  - {domain}: {count}')
        return '\n'.join(lines)
