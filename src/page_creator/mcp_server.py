"""
MCP server for Page Creator.

Exposes a `create_page` tool to any MCP-compatible client (e.g. Claude
Desktop / claude.ai connectors). When you say something like:

    "create a page for me on home loan"

Claude will call this tool with the title ("Home Loan") and content that
IT generates on the fly (that's the "AI generates the content" part -
it happens on the Claude side, before the tool call). This server's job
is simply to:

  1. Receive title (+ optionally content / url) from Claude.
  2. If content wasn't provided, fall back to a basic placeholder.
  3. Derive a unique URL slug from the title (unless one is given).
  4. Persist the page via the FastAPI backend (POST /pages).
  5. Return the final page URL so the user can go check it.

This talks to the FastAPI server over HTTP, so make sure the API is
running first:

    uv run page-creator
    # (or) uv run uvicorn page_creator.main:app --reload

Then run this MCP server (stdio transport) and point your MCP client
(e.g. Claude Desktop config) at it.
"""

from __future__ import annotations

import os

import httpx
from fastmcp import FastMCP

API_BASE_URL = os.environ.get("PAGE_CREATOR_API_URL", "http://127.0.0.1:8000")

mcp = FastMCP("page-creator")


@mcp.tool()
async def create_page(title: str, content: str = "", url: str = "") -> str:
    """
    Create a new page and return its URL.

    Args:
        title: The title of the page to create, e.g. "Home Loan".
        content: The full body content for the page. The calling AI
            should generate rich, relevant content for the given title
            (e.g. an overview of home loans, types, eligibility, etc.)
            before calling this tool. If left empty, a basic placeholder
            is stored instead.
        url: Optional custom URL slug. If left empty, one is
            auto-generated from the title (e.g. "home-loan").

    Returns:
        A confirmation message containing the page's URL/slug so the
        user can look it up.
    """
    payload = {"title": title}
    if content:
        payload["content"] = content
    if url:
        payload["url"] = url

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/pages", json=payload)
            resp.raise_for_status()
        except httpx.ConnectError:
            return (
                "Could not reach the Page Creator API at "
                f"{API_BASE_URL}. Make sure it's running "
                "(`uv run page-creator`) and try again."
            )
        except httpx.HTTPStatusError as e:
            return f"Failed to create page: {e.response.status_code} {e.response.text}"

    data = resp.json()
    return (
        f"Page created successfully.\n"
        f"Title: {data['title']}\n"
        f"URL: /pages/{data['url']}\n"
        f"Created at: {data['created_at']}\n\n"
        f"You can view it via GET {API_BASE_URL}/pages/{data['url']}"
    )


@mcp.tool()
async def list_pages(limit: int = 20) -> str:
    """List recently created pages (title, url, created date)."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/pages", params={"limit": limit})
            resp.raise_for_status()
        except httpx.ConnectError:
            return f"Could not reach the Page Creator API at {API_BASE_URL}."
        except httpx.HTTPStatusError as e:
            return f"Failed to list pages: {e.response.status_code} {e.response.text}"

    pages = resp.json()
    if not pages:
        return "No pages found yet."

    lines = [
        f"- {p['title']}  ->  /pages/{p['url']}  (created {p['created_at']})"
        for p in pages
    ]
    return "\n".join(lines)


@mcp.tool()
async def get_page(url: str) -> str:
    """Fetch the full content of a page by its URL slug."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/pages/{url}")
        except httpx.ConnectError:
            return f"Could not reach the Page Creator API at {API_BASE_URL}."

    if resp.status_code == 404:
        return f"No page found with url '{url}'."
    resp.raise_for_status()
    data = resp.json()
    return f"# {data['title']}\n\n{data['content']}\n\n(Created: {data['created_at']})"


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
