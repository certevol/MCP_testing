from __future__ import annotations
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("openalex")
BASE = "https://api.openalex.org"

@mcp.tool()
def openalex_search_works(query: str, per_page: int = 5, mode: str = "ai"):
    """
    mode:
      - "ai": filtra per risultati AI/RAG/LLM (più precisione)
      - "general": nessun filtro AI (più recall)
    """
    url = f"{BASE}/works"

    fetch_n = max(per_page * 10, 50)
    params = {"search": query, "per_page": fetch_n}

    r = httpx.get(url, params=params, timeout=30.0)
    r.raise_for_status()
    data = r.json()

    keywords_ai = (
        "retrieval",
        "generation",
        "rag",
        "language model",
        "llm",
        "agent",
        "benchmark",
        "transformer",
    )

    negative_rag_bio = (
        "mice", "mouse", "murine",
        "gene", "genes", "genetic", "immun", "chemotherapy",
        "hiv", "cancer", "tumor",
    )

    results = []
    for w in data.get("results", []):
        title = (w.get("title") or "")
        t = title.lower()

        # se la query contiene "rag", evitiamo il significato biologico (RAG gene)
        if "rag" in query.lower() and any(bad in t for bad in negative_rag_bio):
            continue

        if mode == "ai":
            if not any(k in t for k in keywords_ai):
                continue

        results.append({
            "id": w.get("id"),
            "doi": (w.get("doi") or "").replace("https://doi.org/", "") if w.get("doi") else None,
            "title": title,
            "publication_year": w.get("publication_year"),
            "cited_by_count": w.get("cited_by_count"),
            "primary_location": (
                (w.get("primary_location") or {})
                .get("source", {})
                .get("display_name")
            ),
            "openalex_url": w.get("id"),
        })

        if len(results) >= per_page:
            break

    return results


if __name__ == "__main__":
    mcp.run(transport="stdio")
