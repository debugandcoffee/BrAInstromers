from __future__ import annotations

import base64
import xml.etree.ElementTree as ET

from BrAInstromers.backend.app.config import settings
from BrAInstromers.backend.app.ingestion.base import SourceAdapter
from BrAInstromers.backend.app.ingestion.chunking import clean_text
from BrAInstromers.backend.app.models import RawDocument


class OPSAdapter(SourceAdapter):
    source = "ops"
    auth_url = "https://ops.epo.org/3.2/auth/accesstoken"
    base_url = "https://ops.epo.org/3.2/rest-services/published-data/search"

    def fetch(self, query: str, limit: int = 10) -> list[RawDocument]:
        token = self._access_token()
        response = self.session.get(
            self.base_url,
            params={"q": query, "Range": f"1-{max(1, min(limit, 100))}"},
            headers={"Authorization": f"Bearer {token}", "Accept": "application/xml"},
            timeout=45,
        )
        response.raise_for_status()
        return self._parse_search_response(response.text, query)

    def _access_token(self) -> str:
        if not settings.ops_consumer_key or not settings.ops_consumer_secret:
            raise RuntimeError("OPS_CONSUMER_KEY and OPS_CONSUMER_SECRET are required for OPS ingestion.")

        credentials = f"{settings.ops_consumer_key}:{settings.ops_consumer_secret}".encode("utf-8")
        encoded = base64.b64encode(credentials).decode("ascii")
        response = self.session.post(
            self.auth_url,
            data={"grant_type": "client_credentials"},
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def _parse_search_response(self, xml_text: str, query: str) -> list[RawDocument]:
        root = ET.fromstring(xml_text)
        documents: list[RawDocument] = []

        for item in root.findall(".//{*}publication-reference"):
            country = self._first_text(item, ".//{*}country")
            doc_number = self._first_text(item, ".//{*}doc-number")
            kind = self._first_text(item, ".//{*}kind")
            date = self._first_text(item, ".//{*}date")
            external_id = "-".join(part for part in [country, doc_number, kind] if part)
            if not external_id:
                continue

            title = f"Patent publication {external_id}"
            text = clean_text(
                f"{title}\n\nCountry: {country}\nDocument number: {doc_number}\nKind: {kind}\nPublication date: {date}\nQuery: {query}"
            )
            documents.append(
                RawDocument(
                    source=self.source,
                    external_id=external_id,
                    title=title,
                    url=f"https://worldwide.espacenet.com/patent/search?q={doc_number}",
                    text=text,
                    published_at=date or None,
                    metadata={"country": country, "doc_number": doc_number, "kind": kind, "query": query},
                )
            )
        return documents

    @staticmethod
    def _first_text(element: ET.Element, path: str) -> str:
        child = element.find(path)
        return child.text.strip() if child is not None and child.text else ""
