import re
from urllib.parse import quote
from typing import List

import httpx


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def _is_medical_query(query: str) -> bool:
    medical_keywords = [
        "symptom", "sympto", "treatment", "disease", "medicine", "drug", "dosage", "dose",
        "diagnosis", "infection", "fever", "pain", "blood", "cancer", "diabetes",
        "hypertension", "pregnancy", "vaccine", "side effect", "contraindication",
        "medical", "health", "clinic", "hospital", "therapy", "condition", "heart",
        "stroke", "bp", "cholesterol", "asthma", "kidney", "liver", "thyroid",
    ]
    q = query.lower()
    return any(keyword in q for keyword in medical_keywords)


def _safe_append(snippets: List[str], text: str, max_items: int) -> None:
    cleaned = _clean_text(text)
    if cleaned and len(snippets) < max_items:
        snippets.append(cleaned)


async def _fetch_duckduckgo(client: httpx.AsyncClient, query: str, snippets: List[str], max_items: int) -> None:
    try:
        ddg_resp = await client.get(
            "https://api.duckduckgo.com/",
            params={"q": f"medical {query}", "format": "json", "no_html": 1, "skip_disambig": 1},
        )
        ddg_resp.raise_for_status()
        data = ddg_resp.json()

        abstract = _clean_text(data.get("AbstractText", ""))
        abstract_url = data.get("AbstractURL", "")
        if abstract:
            _safe_append(snippets, f"DuckDuckGo: {abstract} (Source: {abstract_url or 'N/A'})", max_items)

        related = data.get("RelatedTopics", []) or []
        for topic in related:
            if len(snippets) >= max_items:
                break
            if isinstance(topic, dict) and "Text" in topic:
                text = _clean_text(topic.get("Text", ""))
                first_url = topic.get("FirstURL", "")
                if text:
                    _safe_append(snippets, f"Related: {text} (Source: {first_url or 'N/A'})", max_items)
            elif isinstance(topic, dict) and "Topics" in topic:
                for nested in topic.get("Topics", []):
                    if len(snippets) >= max_items:
                        break
                    text = _clean_text(nested.get("Text", ""))
                    first_url = nested.get("FirstURL", "")
                    if text:
                        _safe_append(snippets, f"Related: {text} (Source: {first_url or 'N/A'})", max_items)
    except Exception:
        return


async def _fetch_wikipedia(client: httpx.AsyncClient, query: str, snippets: List[str], max_items: int) -> None:
    try:
        search_resp = await client.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": f"medical {query}",
                "format": "json",
                "srlimit": 2,
            },
        )
        search_resp.raise_for_status()
        search_data = search_resp.json()
        results = ((search_data.get("query") or {}).get("search") or [])

        for result in results:
            if len(snippets) >= max_items:
                break
            title = result.get("title", "")
            if not title:
                continue

            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"
            try:
                summary_resp = await client.get(summary_url)
                summary_resp.raise_for_status()
                summary_data = summary_resp.json()
                extract = _clean_text(summary_data.get("extract", ""))
                wiki_url = ((summary_data.get("content_urls") or {}).get("desktop") or {}).get("page", "")
                if extract:
                    _safe_append(snippets, f"Wikipedia ({title}): {extract[:420]} (Source: {wiki_url or 'N/A'})", max_items)
            except Exception:
                continue
    except Exception:
        return


async def _fetch_europe_pmc(client: httpx.AsyncClient, query: str, snippets: List[str], max_items: int) -> None:
    try:
        epmc_resp = await client.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={
                "query": f"{query} AND (medicine OR clinical OR treatment)",
                "format": "json",
                "pageSize": 2,
            },
        )
        epmc_resp.raise_for_status()
        epmc_data = epmc_resp.json()
        results = ((epmc_data.get("resultList") or {}).get("result") or [])

        for article in results:
            if len(snippets) >= max_items:
                break
            title = _clean_text(article.get("title", ""))
            abstract = _clean_text(article.get("abstractText", ""))
            source = _clean_text(article.get("source", ""))
            pmid = _clean_text(article.get("pmid", ""))
            if not title:
                continue
            article_url = f"https://europepmc.org/article/{source}/{pmid}" if source and pmid else "https://europepmc.org"
            snippet = f"Europe PMC: {title}. {abstract[:320] if abstract else ''} (Source: {article_url})"
            _safe_append(snippets, snippet, max_items)
    except Exception:
        return


async def fetch_web_medical_context(query: str, max_items: int = 3) -> str:
    """Fetches medical context from public web sources with graceful fallbacks."""
    query = _clean_text(query)
    if not query:
        return ""

    # Keep the model focused on medical topics. For clearly non-medical queries,
    # avoid adding unrelated web noise.
    if not _is_medical_query(query):
        return ""

    snippets: List[str] = []

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        await _fetch_duckduckgo(client, query, snippets, max_items)
        if len(snippets) < max_items:
            await _fetch_wikipedia(client, query, snippets, max_items)
        if len(snippets) < max_items:
            await _fetch_europe_pmc(client, query, snippets, max_items)

    if not snippets:
        return ""

    return "\n".join(f"- {item}" for item in snippets[:max_items])
