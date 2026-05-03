from __future__ import annotations

from app.ingestion.base import SourceAdapter
from app.ingestion.chunking import clean_text
from app.models import RawDocument


class WikidataAdapter(SourceAdapter):
    source = "wikidata"
    search_endpoint = "https://www.wikidata.org/w/api.php"
    entity_endpoint = "https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"

    def fetch(self, query: str, limit: int = 10) -> list[RawDocument]:
        response = self.session.get(
            self.search_endpoint,
            params={
                "action": "wbsearchentities",
                "format": "json",
                "language": "en",
                "uselang": "en",
                "search": query,
                "limit": max(1, min(limit, 20)),
            },
            timeout=20,
        )
        response.raise_for_status()
        search_results = response.json().get("search", [])

        documents: list[RawDocument] = []
        for result in search_results:
            entity_id = result.get("id")
            if not entity_id:
                continue
            entity = self._entity(entity_id)
            label = self._localized(entity.get("labels", {}), fallback=result.get("label", entity_id))
            description = self._localized(
                entity.get("descriptions", {}),
                fallback=result.get("description", ""),
            )
            aliases = [
                alias.get("value", "")
                for alias in entity.get("aliases", {}).get("en", [])
                if alias.get("value")
            ]
            website = self._claim_value(entity, "P856")
            inception = self._claim_value(entity, "P571")
            official_name = self._claim_value(entity, "P1448")
            item_url = f"https://www.wikidata.org/wiki/{entity_id}"
            text = clean_text(
                f"{label}\n\n"
                f"Official name: {official_name}\n"
                f"Description: {description}\n"
                f"Aliases: {', '.join(aliases)}\n"
                f"Website: {website}\n"
                f"Inception: {inception}\n"
                f"Wikidata entity: {item_url}"
            )
            documents.append(
                RawDocument(
                    source=self.source,
                    external_id=entity_id,
                    title=label,
                    url=item_url,
                    text=text,
                    metadata={
                        "description": description,
                        "website": website,
                        "aliases": aliases,
                        "inception": inception,
                        "query": query,
                    },
                )
            )
        return documents

    def _entity(self, entity_id: str) -> dict:
        response = self.session.get(self.entity_endpoint.format(entity_id=entity_id), timeout=20)
        response.raise_for_status()
        return response.json().get("entities", {}).get(entity_id, {})

    @staticmethod
    def _localized(values: dict, fallback: str = "") -> str:
        return values.get("en", {}).get("value") or fallback

    @staticmethod
    def _claim_value(entity: dict, property_id: str) -> str:
        claims = entity.get("claims", {}).get(property_id, [])
        if not claims:
            return ""
        value = claims[0].get("mainsnak", {}).get("datavalue", {}).get("value", "")
        if isinstance(value, dict):
            if "time" in value:
                return str(value["time"]).lstrip("+")
            if "text" in value:
                return str(value["text"])
            if "id" in value:
                return str(value["id"])
        return str(value)
