"""hackernews-mcp: 返回 Hacker News 最新热门新闻的 MCP Server (stdio)。

对应客户端配置:
{
  "mcpServers": {
    "hackernews": {
      "command": "python",
      "args": ["/absolute/path/to/hackernews-mcp/server.py"]
    }
  }
}
"""

import json
import urllib.request

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hackernews-mcp")

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


def _http_get_json(url: str, timeout: float = 10.0):
    req = urllib.request.Request(url, headers={"User-Agent": "hackernews-mcp/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_story(item_id: int) -> dict | None:
    """拉取单条故事并裁剪成精简字段，网络异常时返回 None 保证整体不中断。"""
    try:
        item = _http_get_json(f"{HN_API_BASE}/item/{item_id}.json")
    except Exception:
        return None
    if not item or item.get("type") != "story":
        return None
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "url": item.get("url"),
        "score": item.get("score", 0),
        "by": item.get("by"),
        "time": item.get("time"),
        "comments": item.get("descendants", 0),
        "hn_link": f"https://news.ycombinator.com/item?id={item.get('id')}",
    }


@mcp.tool()
def get_top_stories(limit: int = 10) -> str:
    """获取 Hacker News 当前最新热门故事（实时数据，无需 API Key）。

    Args:
        limit: 返回条数，1-30，默认 10。
    """
    limit = max(1, min(limit, 30))
    try:
        top_ids = _http_get_json(f"{HN_API_BASE}/topstories.json")[:limit]
    except Exception as exc:
        return json.dumps({"error": f"failed to fetch top stories: {exc}"}, ensure_ascii=False)

    stories = [s for s in (_fetch_story(i) for i in top_ids) if s]
    return json.dumps(
        {"count": len(stories), "source": "Hacker News", "stories": stories},
        ensure_ascii=False,
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()  # 默认 stdio 传输
