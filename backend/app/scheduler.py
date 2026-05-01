from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from BrAInstromers.backend.app.cli import build_adapter
from BrAInstromers.backend.app.config import settings
from BrAInstromers.backend.app.storage.document_store import DocumentStore


SOURCE_TO_COMMAND = {
    "arxiv": "ingest-arxiv",
    "wikidata": "ingest-wikidata",
    "ops": "ingest-ops",
    "eu_funding": "ingest-eu-funding",
    "company": "ingest-company",
}


@dataclass(frozen=True)
class ScheduledJob:
    id: str
    source: str
    query: str
    max_results: int
    refresh_hours: float
    enabled: bool = True

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ScheduledJob":
        return cls(
            id=str(value["id"]),
            source=str(value["source"]),
            query=str(value["query"]),
            max_results=int(value.get("max_results", 10)),
            refresh_hours=float(value.get("refresh_hours", 24)),
            enabled=bool(value.get("enabled", True)),
        )


def load_config(path: Path) -> tuple[int, list[ScheduledJob]]:
    if not path.exists():
        raise FileNotFoundError(f"Scheduler config does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    poll_seconds = int(payload.get("poll_seconds", 300))
    jobs = [ScheduledJob.from_dict(item) for item in payload.get("jobs", [])]
    return poll_seconds, jobs


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"jobs": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def is_due(job: ScheduledJob, state: dict[str, Any], now: datetime) -> bool:
    job_state = state.get("jobs", {}).get(job.id, {})
    last_success_at = job_state.get("last_success_at")
    if not last_success_at:
        return True
    last_success = datetime.fromisoformat(last_success_at)
    elapsed_hours = (now - last_success).total_seconds() / 3600
    return elapsed_hours >= job.refresh_hours


def run_job(job: ScheduledJob, store: DocumentStore) -> dict[str, Any]:
    command = SOURCE_TO_COMMAND.get(job.source)
    if not command:
        raise ValueError(f"Unsupported scheduled source: {job.source}")
    adapter = build_adapter(command, store)
    return adapter.ingest(job.query, limit=job.max_results)


def run_due_jobs(
    jobs_path: Path = settings.scheduler_jobs_path,
    state_path: Path = settings.scheduler_state_path,
    force: bool = False,
) -> dict[str, Any]:
    _, jobs = load_config(jobs_path)
    state = load_state(state_path)
    state.setdefault("jobs", {})
    store = DocumentStore(settings.document_db_path)
    now = datetime.now(timezone.utc)
    summary: dict[str, Any] = {"checked": 0, "ran": 0, "skipped": 0, "errors": 0, "jobs": []}

    for job in jobs:
        if not job.enabled:
            summary["skipped"] += 1
            summary["jobs"].append({"id": job.id, "status": "disabled"})
            continue

        summary["checked"] += 1
        if not force and not is_due(job, state, now):
            summary["skipped"] += 1
            summary["jobs"].append({"id": job.id, "status": "not_due"})
            continue

        started_at = datetime.now(timezone.utc)
        job_state = state["jobs"].setdefault(job.id, {})
        job_state["last_started_at"] = started_at.isoformat()
        try:
            result = run_job(job, store)
            finished_at = datetime.now(timezone.utc)
            job_state["last_success_at"] = finished_at.isoformat()
            job_state["last_finished_at"] = finished_at.isoformat()
            job_state["last_error"] = None
            job_state["last_result"] = result
            summary["ran"] += 1
            summary["jobs"].append({"id": job.id, "status": "ok", "result": result})
        except Exception as exc:
            finished_at = datetime.now(timezone.utc)
            job_state["last_finished_at"] = finished_at.isoformat()
            job_state["last_error"] = str(exc)
            summary["errors"] += 1
            summary["jobs"].append({"id": job.id, "status": "error", "error": str(exc)})
        finally:
            save_state(state_path, state)

    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run scheduled NexusBridge ingestion jobs.")
    parser.add_argument("--jobs", type=Path, default=settings.scheduler_jobs_path)
    parser.add_argument("--state", type=Path, default=settings.scheduler_state_path)
    parser.add_argument("--once", action="store_true", help="Run due jobs once and exit.")
    parser.add_argument("--force", action="store_true", help="Run enabled jobs even when they are not due.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    poll_seconds, _ = load_config(args.jobs)

    while True:
        summary = run_due_jobs(args.jobs, args.state, force=args.force)
        print(json.dumps(summary, indent=2), flush=True)
        if args.once:
            return
        time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
