# BrAInstromers

**Turn research ↔ business ↔ investment into actionable connections.**

A 3-way matchmaking platform that connects researchers, companies, and investors by translating research ideas into business value. Powered by RAG (Retrieval-Augmented Generation) with persona-aware response tailoring.

## What It Does

- **Data Ingestion**: Fetches from arXiv, EU Funding portal, patents (OPS), Wikidata, company websites
- **Semantic Search**: Hybrid lexical + semantic retrieval with multilingual embeddings
- **RAG Engine**: LLM-powered answers grounded in ingested documents
- **Matchmaking**: Connects researchers to companies solving their problems, investors to opportunities
- **Persona Awareness**: Tailors responses for company/researcher/investor perspectives

## Tech Stack

- **Backend**: FastAPI, SQLite, sentence-transformers, LLaMA (via Groq)
- **Frontend**: React, Vite
- **Deployment**: Docker Compose

## Quick Start

### Docker

```bash
# Clone and setup
git clone https://github.com/debugandcoffee/BrAInstromers.git
cd BrAInstromers

# Copy env file
cp backend/.env.example backend/.env

# Edit .env with your API keys
# - OPENAI_API_KEY (for Groq LLaMA)
# - OPS_CONSUMER_KEY / OPS_CONSUMER_SECRET (optional, for patents)
nano backend/.env

# Start full stack (backend + frontend)
docker compose up --build

# Open http://localhost:8080
```

**Potential errors** 
To avoid error remove folder `data` in folder `backend` or comment line 4 in entrypoint.sh `bash ingestion.sh` before starting docker multiple times.
```
cd backend
rm -rf data
```
