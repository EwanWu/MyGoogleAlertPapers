PYTHON ?= python
PIP ?= $(PYTHON) -m pip

.PHONY: install-dev test smoke

install-dev:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

test:
	PYTHONPATH=src $(PYTHON) -m pytest tests

smoke:
	PYTHONPATH=src $(PYTHON) -m pytest \
		tests/test_scholar_detector.py \
		tests/test_candidate_extractor.py \
		tests/test_candidate_parser_quality.py \
		tests/test_identifier_extraction.py \
		tests/test_identifiers.py \
		tests/test_title_normalization.py \
		tests/test_merge_conflict_grading.py
