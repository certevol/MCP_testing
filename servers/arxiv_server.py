from __future__ import annotations
import arxiv
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("arxiv")

@mcp.tool()
def arxiv_search(topic: str, max_results: int = 5):
    """Search arXiv by topic and return basic metadata."""
    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    out = []
    for r in search.results():
        out.append({
            "title": r.title,
            "authors": [a.name for a in r.authors],
            "published": r.published.isoformat() if r.published else None,
            "pdf_url": r.pdf_url,
            "entry_id": r.entry_id,
            "summary": r.summary,
        })

    return out

if __name__ == "__main__":
    # Non usare print() su stdout in stdio: rompe JSON-RPC.
    mcp.run(transport="stdio")
