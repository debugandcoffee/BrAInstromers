#!/bin/sh
set -e

python -m app.cli init-db
python -m app.cli ingest-arxiv "machine learning" --max-results 50
python -m app.cli ingest-wikidata "machine learning" --max-results 50
# # python -m app.cli ingest-company "machine learning" --max-results 10
python -m app.cli ingest-eu-funding "machine learning" --max-results 50