from __future__ import annotations

import argparse
import json
import sys

from app.config import settings
from app.storage.document_store import DocumentStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare NexusBridge documents for retrieval.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Create SQLite tables.")
    subparsers.add_parser("stats", help="Show document cache statistics.")

    list_documents = subparsers.add_parser("list-documents", help="Show stored documents.")
    list_documents.add_argument("--limit", type=int, default=20)

    list_chunks = subparsers.add_parser("list-chunks", help="Show stored retrieval chunks.")
    list_chunks.add_argument("--limit", type=int, default=20)

    subparsers.add_parser("build-lexical-index", help="Rebuild the SQLite FTS5 lexical index.")

    semantic_index = subparsers.add_parser("build-semantic-index", help="Embed chunks for semantic search.")
    semantic_index.add_argument("--model", default=settings.embedding_model)
    semantic_index.add_argument("--batch-size", type=int, default=32)

    search = subparsers.add_parser("search", help="Search retrieval chunks.")
    search.add_argument("query")
    search.add_argument("--mode", choices=["lexical", "semantic", "hybrid"], default="hybrid")
    search.add_argument("--top-n", type=int, default=8)
    search.add_argument("--candidate-n", type=int, default=80)
    search.add_argument("--model", default=settings.embedding_model)

    for command in ("ingest-arxiv", "ingest-wikidata", "ingest-ops", "ingest-eu-funding"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("query")
        subparser.add_argument("--max-results", type=int, default=10)

    company = subparsers.add_parser("ingest-company")
    company.add_argument("url")

    return parser


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args()
    store = DocumentStore(settings.document_db_path)

    if args.command == "init-db":
        store.init_db()
        print(f"Initialized {settings.document_db_path}")
        return

    if args.command == "stats":
        print(json.dumps(store.stats(), indent=2))
        return

    if args.command == "list-documents":
        print(json.dumps(store.list_documents(limit=args.limit), indent=2, ensure_ascii=False))
        return

    if args.command == "list-chunks":
        print(json.dumps(store.list_chunks(limit=args.limit), indent=2, ensure_ascii=False))
        return

    if args.command == "build-lexical-index":
        from app.retrieval.indexer import build_lexical_index

        print(json.dumps({"indexed": build_lexical_index(store)}, indent=2))
        return

    if args.command == "build-semantic-index":
        from app.retrieval.indexer import build_semantic_index

        print(json.dumps(build_semantic_index(store, model_name=args.model, batch_size=args.batch_size), indent=2))
        return

    if args.command == "search":
        from app.retrieval.search import Retriever

        retriever = Retriever(store, model_name=args.model)
        if args.mode == "lexical":
            results = retriever.lexical(args.query, top_n=args.top_n, candidate_n=args.candidate_n)
        elif args.mode == "semantic":
            results = retriever.semantic(args.query, top_n=args.top_n)
        else:
            results = retriever.hybrid(args.query, top_n=args.top_n, candidate_n=args.candidate_n)
        print(json.dumps([result.to_dict() for result in results], indent=2, ensure_ascii=False))
        return

    adapter = build_adapter(args.command, store)
    query = getattr(args, "query", None) or getattr(args, "url")
    limit = getattr(args, "max_results", 1)
    result = adapter.ingest(query, limit=limit)
    print(json.dumps(result, indent=2))


def build_adapter(command: str, store: DocumentStore):
    if command == "ingest-arxiv":
        from app.ingestion.arxiv import ArxivAdapter

        return ArxivAdapter(store)
    if command == "ingest-wikidata":
        from app.ingestion.wikidata import WikidataAdapter

        return WikidataAdapter(store)
    if command == "ingest-ops":
        from app.ingestion.ops import OPSAdapter

        return OPSAdapter(store)
    if command == "ingest-eu-funding":
        from app.ingestion.eu_funding import EUFundingAdapter

        return EUFundingAdapter(store)
    if command == "ingest-company":
        from app.ingestion.company_scraper import CompanyScraperAdapter

        return CompanyScraperAdapter(store)
    raise ValueError(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
