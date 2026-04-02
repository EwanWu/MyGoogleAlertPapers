# Data Model Draft

## Core entities

### 1. mail_ingestion_record
Tracks each scanned email and processing state.

Suggested fields:
- mail_uid
- message_id
- mailbox
- internal_date
- from_address
- subject
- is_unseen_at_scan
- scan_mode
- is_google_scholar_alert
- parse_status
- num_candidates_extracted
- processing_started_at
- processing_finished_at
- wall_time_ms
- error_code
- error_message

### 2. raw_mail_snapshot
Stores raw or semi-raw mail content for debugging and reprocessing.

Suggested fields:
- mail_uid
- header_json
- body_text
- body_html
- body_hash
- snapshot_path
- extracted_at

### 3. paper_candidate
Represents a paper-like item extracted from one email.

Suggested fields:
- candidate_id
- mail_uid
- candidate_index_in_mail
- raw_title
- raw_authors
- raw_source_text
- raw_link
- raw_snippet
- parser_confidence
- template_variant
- extraction_notes
- scholar_wrapper_url
- target_url
- resource_type_hint
- venue_guess
- year_guess

### 4. paper_candidate_normalized
Normalization layer separate from raw extraction.

Suggested fields:
- candidate_id
- norm_title
- norm_title_key
- norm_authors_json
- first_author_family
- year_guess
- venue_guess
- doi_extracted
- pmid_extracted
- pmcid_extracted
- arxiv_id_extracted
- url_canonical
- scholar_cluster_hint
- normalized_at

### 5. source_record
Stores one lookup result per external source.

Suggested fields:
- source_record_id
- candidate_id
- source_name
- query_type
- query_string
- matched
- match_score
- external_id
- title
- authors_json
- abstract
- venue
- year
- publication_type
- doi
- pmid
- pmcid
- url
- raw_payload_json
- retrieved_at
- latency_ms

### 5b. source_record
Stores one enrichment result per provider query.

Suggested fields:
- candidate_id
- source_name
- query_type
- query_string
- matched
- match_score
- external_id
- title
- authors_json
- abstract
- venue
- year
- publication_type
- doi
- pmid
- pmcid
- url
- raw_payload_json
- latency_ms

### 6. merged_metadata_proposal
Multi-source merged proposal before canonicalization.

Suggested fields:
- candidate_id
- preferred_title
- preferred_authors_json
- preferred_abstract
- preferred_venue
- preferred_year
- preferred_doi
- preferred_pmid
- preferred_publication_type
- version_status
- source_priority_trace
- conflict_flags_json
- merge_confidence

### 7. canonical_paper
Primary record used downstream.

Suggested fields:
- paper_id
- canonical_title
- canonical_authors_json
- canonical_abstract
- canonical_venue
- canonical_year
- canonical_doi
- canonical_pmid
- canonical_pmcid
- publication_type
- version_preference
- influence_metrics_json
- topic_signals_json
- created_at
- updated_at

### 8. paper_version_link
Stores version relations.

Suggested fields:
- link_id
- paper_id_parent
- paper_id_child
- relation_type
- confidence
- evidence_json

### 9. cost_event
Tracks per-stage resource usage.

Suggested fields:
- event_id
- mail_uid
- candidate_id
- stage
- provider
- request_count
- tokens_prompt
- tokens_completion
- tokens_total
- estimated_cost_usd
- latency_ms
- status
- notes
