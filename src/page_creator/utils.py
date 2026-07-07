"""Helper functions: slug generation and fallback content generation."""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from . import database


def slugify(text: str) -> str:
    """Turn 'Home Loan' into 'home-loan'."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "page"


def generate_unique_url(db: Session, title: str) -> str:
    """Generate a URL slug from the title, appending -2, -3, ... on collision."""
    base_slug = slugify(title)
    slug = base_slug
    counter = 2
    while db.query(database.Page).filter(database.Page.url == slug).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def generate_fallback_content(title: str) -> str:
    """
    Very basic placeholder content generator, used only when no content is
    supplied by the caller (e.g. calling the API directly with curl).

    When this project is used through the MCP server with Claude, Claude
    itself generates rich, relevant content for the title and passes it
    in explicitly — this function is just a safety net.
    """
    return (
        f"# {title}\n\n"
        f"This page is about **{title}**.\n\n"
        f"Content for this page has not been customized yet. "
        f"Replace this placeholder with real content, or create the page "
        f"through the MCP-connected AI assistant so it can generate the "
        f"content for you automatically."
    )
