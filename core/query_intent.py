"""Infer a routable category from a free-text search query."""
from agents.orchestrator import OrchestratorAgent


def infer_category(query: str) -> str:
    """Map a free-text query (e.g. "kettle") to a category the orchestrator can route.

    Checks specific subcategory keys first (`CATEGORY_MAP`, e.g. "faucet", "kettle") before
    falling back to broader category keys (`BROADER_CATEGORY_MAP`, e.g. "bathroom",
    "appliances") — a specific term should win over a broader one even if the broader
    term happens to be a longer string. Falls back to "general".
    """
    query_lower = query.lower()
    for keys in (OrchestratorAgent.CATEGORY_MAP, OrchestratorAgent.BROADER_CATEGORY_MAP):
        for key in sorted(keys, key=len, reverse=True):
            if key in query_lower:
                return key
    return "general"
