from __future__ import annotations

import json
from typing import Any

from app.config import settings
from app.ingestion.base import SourceAdapter
from app.ingestion.chunking import clean_text
from app.models import RawDocument


class EUFundingAdapter(SourceAdapter):
    source = "eu_funding"

    def fetch(self, query: str, limit: int = 10) -> list[RawDocument]:
        query_body = {
            "bool": {
                "must": [
                    {"terms": {"type": ["1", "2", "8"]}},
                    {"terms": {"status": ["31094501", "31094502"]}},
                    {"term": {"programmePeriod": "2021 - 2027"}},
                ]
            }
        }
        sort_body = {"field": "startDate", "order": "DESC"}
        display_fields = [
            "type",
            "identifier",
            "reference",
            "callccm2Id",
            "title",
            "status",
            "caName",
            "projectAcronym",
            "startDate",
            "deadlineDate",
            "deadlineModel",
            "frameworkProgramme",
            "typesOfAction",
            "keywords",
            "description",
        ]

        response = self.session.post(
            settings.eu_funding_api_url,
            params={
                "apiKey": "SEDIA",
                "text": query or "***",
                "pageSize": max(1, min(limit, 50)),
                "pageNumber": 1,
            },
            files={
                "query": ("blob", json.dumps(query_body), "application/json"),
                "languages": ("blob", json.dumps(["en"]), "application/json"),
                "sort": ("blob", json.dumps(sort_body), "application/json"),
                "displayFields": ("blob", json.dumps(display_fields), "application/json"),
            },
            headers={"Accept": "application/json"},
            timeout=45,
        )
        response.raise_for_status()
        payload = response.json()
        items = self._extract_items(payload)

        documents: list[RawDocument] = []
        for item in items[:limit]:
            metadata = item.get("metadata", item)
            external_id = self._pick(metadata, "identifier", "reference", "id", "topicId", "callIdentifier", "callId")
            title = self._pick(metadata, "title", "topicTitle", "callTitle", "name") or item.get("content") or str(external_id)
            description = self._pick(metadata, "description", "shortDescription", "objective", "scope") or item.get("content", "")
            status = self._pick(metadata, "status", "statusDescription")
            programme = self._pick(metadata, "programme", "programmePeriod", "frameworkProgramme")
            deadline = self._pick(metadata, "deadlineDate", "deadline", "submissionDeadline")
            url = self._pick(item, "url", "topicUrl")
            if not url and external_id:
                url = "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/" + str(external_id)

            text = clean_text(
                f"{title}\n\nDescription: {description}\nStatus: {status}\nProgramme: {programme}\nDeadline: {deadline}"
            )
            documents.append(
                RawDocument(
                    source=self.source,
                    external_id=str(external_id or title),
                    title=str(title),
                    url=str(url) if url else None,
                    text=text,
                    metadata={"raw": item, "query": query, "api": "SEDIA"},
                )
            )
        return documents

    def _extract_items(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []
        for key in ("data", "results", "topics", "content", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                nested = self._extract_items(value)
                if nested:
                    return nested
        return []

    @staticmethod
    def _pick(item: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            value = item.get(key)
            if isinstance(value, list) and value:
                value = value[0]
            if value not in (None, ""):
                return value
        return ""
