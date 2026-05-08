# NexusBridge backend data layer

This backend prepares documents for the future RAG retriever. It does not run the
chat model yet. Its job is to fetch, normalize, cache, and chunk source material.

## Sources

- `arxiv`: public Atom API from arXiv.
- `wikidata`: public SPARQL endpoint.
- `ops`: EPO Open Patent Services, OAuth credentials required.
- `eu_funding`: EU Funding & Tenders Portal via the SEDIA search API.
- `company`: first-party company website scraper.

## Storage

Documents are stored in SQLite:

- `documents`: one row per source item.
- `chunks`: retrieval-ready text chunks derived from documents.
- `ingestion_runs`: audit trail for ingestion jobs.

SQLite is enough for the preparation stage because it gives us persistence,
deduplication, refresh timestamps, and local development without operating a
database server. The next RAG step can add embeddings and copy chunks to a vector
store without changing source adapters.

## Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## Examples

```powershell
python -m app.cli init-db
python -m app.cli ingest-arxiv "artificial intelligence drug discovery" --max-results 10
python -m app.cli ingest-wikidata "OpenAI"
python -m app.cli ingest-company https://openai.com
python -m app.cli stats
```

## Scheduler

Scheduled ingestion jobs live in `scheduler_jobs.json`. Each job defines:

- `source`: `arxiv`, `eu_funding`, `wikidata`, `ops`, or `company`.
- `query`: API search query or company URL.
- `max_results`: fetch limit per run.
- `refresh_hours`: how often the job should run after a successful refresh.
- `enabled`: turn the job on or off without deleting it.

Run due jobs once:

```powershell
python -m app.scheduler --once
```

Run due jobs continuously:

```powershell
python -m app.scheduler
```

Force all enabled jobs regardless of their last successful run:

```powershell
python -m app.scheduler --once --force
```

The scheduler stores last run timestamps and errors in:

```text
data/scheduler_state.json
```

Docker scheduler:

```powershell
docker compose --profile backend up --build backend
```

OPS requires `OPS_CONSUMER_KEY` and `OPS_CONSUMER_SECRET`.

EU Funding endpoint is intentionally configurable because the portal support page
is the source of truth for the current API path. Set `EU_FUNDING_API_URL` in `.env`
after confirming it in the Funding & Tenders Portal API support page.

## Refresh strategy

The store is designed as a cache, not a one-time dump. Each document has a stable
`source + external_id`, `fetched_at`, and `content_hash`. Re-running ingestion
updates changed records and keeps unchanged records stable. A scheduler can later
run sources at different cadences:

- arXiv: daily for active topics.
- EU Funding: daily or every few hours near deadlines.
- OPS patents: daily/weekly depending on query volume and API quota.
- Wikidata: weekly for company/entity enrichment.
- Company scraper: weekly/monthly, plus manual refresh before outreach.

The default `scheduler_jobs.json` uses daily refresh for arXiv and EU Funding,
weekly refresh for Wikidata and the company scraper.

The current focused market slice is documented in `market_slice.json`:

```text
AI for energy flexibility, grid optimization, and industrial energy efficiency
```

The first company target list is in `company_targets.json`. Scheduler jobs scrape
a smaller working subset from that list so early runs stay manageable.

Golden QA examples for future RAG evaluation are in:

```text
eval/persona_golden_tests.json
```

## References

- EPO Developer Portal: https://developers.epo.org/
- arXiv API manual: https://info.arxiv.org/help/api/user-manual.html
- Wikidata SPARQL endpoint: https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service
- EU Funding & Tenders Portal APIs page: https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/support/apis

## Retrieval

The first retrieval layer has two indexes:

- lexical search: SQLite FTS5 over chunk text, title, and source;
- semantic search: sentence-transformer embeddings stored per chunk.

Default embedding model:

```text
intfloat/multilingual-e5-small
```

This model is multilingual and fits Polish questions over mostly English
documents. E5 models should use `query:` prefixes for queries and `passage:`
prefixes for documents; the code applies those automatically.

Build indexes:

```powershell
python -m app.cli build-lexical-index
python -m app.cli build-semantic-index
```

Search:

```powershell
python -m app.cli search "Which companies can help with demand response?" --mode lexical --top-n 5
python -m app.cli search "Which EU grants fit AI energy optimization?" --mode semantic --top-n 5
python -m app.cli search "Find partners for industrial energy flexibility pilots" --mode hybrid --top-n 8
```

After the model is downloaded once, you can force local-cache usage:

```powershell
$env:HF_HUB_OFFLINE="1"
$env:TRANSFORMERS_OFFLINE="1"
python -m app.cli search "Jakie firmy pomagają w demand response?" --mode hybrid --top-n 5
```
