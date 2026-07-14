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

This server talks to the database DIRECTLY (via crud.py / database.py) —
it does NOT make an HTTP call to the FastAPI app in main.py. This means
it works the same way whether it's run locally or deployed to a remote
host: there's no "localhost:8000" to be unreachable, because there's no
second process to reach.

(main.py / the FastAPI app is still there if you want a REST API or a
browser-facing view of the same data — it shares the same SQLite DB —
but the MCP server does not depend on it being up.)
"""

from __future__ import annotations

from fastmcp import FastMCP

from page_creator import crud, database

mcp = FastMCP("page-creator")


def _get_session() -> database.Session:
    database.init_db()
    return database.SessionLocal()


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
    db = _get_session()
    try:
        page = crud.create_page(db, title=title, content=content or None, url=url or None)
        return (
            f"Page created successfully.\n"
            f"Title: {page.title}\n"
            f"URL: /pages/{page.url}\n"
            f"Created at: {page.created_at}"
        )
    except Exception as e:  # keep the tool resilient; surface the real error
        return f"Failed to create page: {e}"
    finally:
        db.close()


@mcp.tool()
async def list_pages(limit: int = 20) -> str:
    """List recently created pages (title, url, created date)."""
    db = _get_session()
    try:
        pages = crud.list_pages(db, limit=limit)
        if not pages:
            return "No pages found yet."
        return "\n".join(
            f"- {p.title}  ->  /pages/{p.url}  (created {p.created_at})" for p in pages
        )
    except Exception as e:
        return f"Failed to list pages: {e}"
    finally:
        db.close()


@mcp.tool()
async def get_page(url: str) -> str:
    """Fetch the full content of a page by its URL slug."""
    db = _get_session()
    try:
        page = crud.get_page_by_url(db, url)
        if page is None:
            return f"No page found with url '{url}'."
        return f"# {page.title}\n\n{page.content}\n\n(Created: {page.created_at})"
    except Exception as e:
        return f"Failed to get page: {e}"
    finally:
        db.close()

def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()