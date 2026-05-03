from __future__ import annotations

import html
import urllib.parse
import xml.etree.ElementTree as ET

from app.ingestion.base import SourceAdapter
from app.ingestion.chunking import clean_text
from app.models import RawDocument


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class ArxivAdapter(SourceAdapter):
    source = "arxiv"
    base_url = "https://export.arxiv.org/api/query"

    def fetch(self, query: str, limit: int = 10) -> list[RawDocument]:
        params = {
            "search_query": query if ":" in query else f"all:{query}",
            "start": 0,
            "max_results": min(limit, 100),
            "sortBy": "lastUpdatedDate",
            "sortOrder": "descending",
        }
        response = self.session.get(self.base_url, params=params, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.text)

        documents: list[RawDocument] = []
        for entry in root.findall("atom:entry", ATOM_NS):
            arxiv_id = self._text(entry, "atom:id").rsplit("/", 1)[-1]
            title = clean_text(html.unescape(self._text(entry, "atom:title")))
            summary = clean_text(html.unescape(self._text(entry, "atom:summary")))
            authors = [clean_text(self._text(author, "atom:name")) for author in entry.findall("atom:author", ATOM_NS)]
            categories = [item.attrib.get("term", "") for item in entry.findall("atom:category", ATOM_NS)]
            url = self._text(entry, "atom:id")
            published = self._text(entry, "atom:published") or None
            updated = self._text(entry, "atom:updated") or None
            text = f"{title}\n\nAuthors: {', '.join(authors)}\nCategories: {', '.join(categories)}\n\nAbstract:\n{summary}"

            documents.append(
                RawDocument(
                    source=self.source,
                    external_id=arxiv_id,
                    title=title or arxiv_id,
                    url=url,
                    text=text,
                    published_at=published,
                    updated_at=updated,
                    metadata={
                        "authors": authors,
                        "categories": categories,
                        "query": query,
                        "api_url": f"{self.base_url}?{urllib.parse.urlencode(params)}",
                    },
                )
            )
        return documents

    @staticmethod
    def _text(element: ET.Element, path: str) -> str:
        child = element.find(path, ATOM_NS)
        return child.text.strip() if child is not None and child.text else ""
