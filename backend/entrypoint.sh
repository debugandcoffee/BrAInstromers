#!/bin/sh
set -e

echo "Initializing database..."
python -m app.cli init-db

# python -m app.cli ingest-arxiv "machine learning" --max-results 10
# python -m app.cli ingest-wikidata "machine learning" --max-results 10
# # python -m app.cli ingest-company "machine learning" --max-results 10
# python -m app.cli ingest-eu-funding "machine learning" --max-results 10

echo "Running stats..."
python -m app.cli stats || true

# echo "Test search..."
# python -m app.cli search "machine learning" --mode hybrid

echo "Starting API..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000