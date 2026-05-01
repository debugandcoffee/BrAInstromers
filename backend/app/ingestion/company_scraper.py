from __future__ import annotations

import json
from urllib.parse import urlparse

import requests

from BrAInstromers.backend.app.config import settings
from BrAInstromers.backend.app.ingestion.base import SourceAdapter
from BrAInstromers.backend.app.ingestion.chunking import clean_text
from BrAInstromers.backend.app.models import RawDocument


COMPANY_PATHS = (
    "",
    "/about",
    "/about-us",
    "/company",
    "/solutions",
    "/technology",
    "/products",
    "/services",
    "/platform",
    "/markets",
    "/industries",
    "/customers",
    "/case-studies",
    "/resources",
)


class CompanyScraperAdapter(SourceAdapter):
    source = "company"

    def fetch(self, query: str, limit: int = 1) -> list[RawDocument]:
        url = normalize_company_url(query)
        pages = collect_company_pages(url, self.session)
        if not pages:
            return []

        combined_text = "\n\n".join(page["text"] for page in pages)
        structured = extract_company_data(combined_text) if settings.openai_api_key else {}
        domain = urlparse(url).netloc
        title = structured.get("company_name") or domain
        summary = structured.get("summary") or combined_text[:1000]
        text = clean_text(
            f"{title}\n\nSummary: {summary}\n\n"
            f"Industry: {structured.get('industry', '')}\n"
            f"Technologies: {', '.join(structured.get('technologies', []))}\n"
            f"Products: {', '.join(structured.get('products', []))}\n"
            f"Research areas: {', '.join(structured.get('research_areas', []))}\n\n"
            f"Source text:\n{combined_text[:18000]}"
        )
        return [
            RawDocument(
                source=self.source,
                external_id=domain,
                title=title,
                url=url,
                text=text,
                metadata={"pages": pages, "structured": structured},
            )
        ]


def normalize_company_url(value: str) -> str:
    value = value.strip()
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    return value.rstrip("/")


def collect_company_pages(base_url: str, session: requests.Session | None = None) -> list[dict[str, str]]:
    session = session or requests.Session()
    session.headers.update({"User-Agent": settings.user_agent})
    pages: list[dict[str, str]] = []
    for url in candidate_urls(base_url):
        html = fetch_page(url, session)
        if not html:
            continue
        text = extract_main_text(html)
        if text:
            pages.append({"url": url, "text": clean_text(text)[:12000]})
    return pages


def candidate_urls(base_url: str) -> list[str]:
    return [base_url.rstrip("/") + path for path in COMPANY_PATHS]


def fetch_page(url: str, session: requests.Session) -> str | None:
    try:
        response = session.get(url, timeout=12)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None


def extract_main_text(html: str) -> str:
    try:
        import trafilatura
    except ImportError as exc:
        raise RuntimeError("Install backend requirements before using company scraping: pip install -r requirements.txt") from exc

    return trafilatura.extract(html, include_comments=False, include_tables=True) or ""


def extract_company_data(text: str) -> dict:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install backend requirements before using OpenAI extraction: pip install -r requirements.txt") from exc

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = f"""
Extract structured company information for a business-opportunity RAG database.
Ignore marketing fluff and return strict JSON only.

Schema:
{{
  "company_name": "",
  "industry": "",
  "technologies": [],
  "products": [],
  "research_areas": [],
  "customer_segments": [],
  "business_model": "",
  "summary": ""
}}

TEXT:
{text[:18000]}
"""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    content = response.choices[0].message.content or "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"summary": content}
