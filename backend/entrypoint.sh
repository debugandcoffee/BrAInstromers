#!/bin/sh
set -e

bash ingestion.sh

echo "Running stats..."
python -m app.cli stats || true

echo "Starting API..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000