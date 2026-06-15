import json
import time

from ri.system_info import get_system_context
from ri.tools.registry import ToolRegistry, _tool


def register(registry: ToolRegistry) -> None:
    registry.register(
        _tool(
            "get_time",
            "Get current date and time.",
            {"type": "object", "properties": {}, "required": []},
        ),
        lambda: time.strftime("%Y-%m-%d %H:%M:%S %Z"),
    )

    registry.register(
        _tool(
            "get_system_info",
            "Get detailed OS, hardware, and environment information.",
            {"type": "object", "properties": {}, "required": []},
        ),
        lambda: get_system_context(),
    )

    registry.register(
        _tool(
            "web_search",
            "Search the web and return brief result snippets (DuckDuckGo).",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "description": "Default 5"},
                },
                "required": ["query"],
            },
        ),
        _web_search,
    )


def _web_search(query: str, max_results: int = 5) -> str:
    try:
        import urllib.parse
        import urllib.request

        url = (
            "https://api.duckduckgo.com/?"
            + urllib.parse.urlencode({"q": query, "format": "json", "no_redirect": "1"})
        )
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        parts = []
        if data.get("AbstractText"):
            parts.append(f"Summary: {data['AbstractText']}")
            if data.get("AbstractURL"):
                parts.append(f"Source: {data['AbstractURL']}")

        related = data.get("RelatedTopics") or []
        count = 0
        for item in related:
            if count >= max_results:
                break
            if isinstance(item, dict) and item.get("Text"):
                parts.append(f"- {item['Text']}")
                count += 1
            elif isinstance(item, dict) and "Topics" in item:
                for sub in item["Topics"]:
                    if count >= max_results:
                        break
                    if sub.get("Text"):
                        parts.append(f"- {sub['Text']}")
                        count += 1

        return "\n".join(parts) or f"No instant results for '{query}'. Try a browser search."
    except Exception as exc:
        return f"Web search failed: {exc}"