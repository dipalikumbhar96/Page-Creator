"""CRUD operations for pages."""

from __future__ import annotations

from sqlalchemy.orm import Session

from . import database, utils


def create_page(db: Session, title: str, content: str | None, url: str | None = None) -> database.Page:
    final_content = content if content and content.strip() else utils.generate_fallback_content(title)

    if url and url.strip():
        final_url = utils.slugify(url)
        existing = db.query(database.Page).filter(database.Page.url == final_url).first()
        if existing is not None:
            # fall back to auto-generation if the requested slug is taken
            final_url = utils.generate_unique_url(db, title)
    else:
        final_url = utils.generate_unique_url(db, title)

    page = database.Page(title=title, content=final_content, url=final_url)
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


def get_page_by_url(db: Session, url: str) -> database.Page | None:
    return db.query(database.Page).filter(database.Page.url == url).first()


def get_page_by_id(db: Session, page_id: int) -> database.Page | None:
    return db.query(database.Page).filter(database.Page.id == page_id).first()


def list_pages(db: Session, skip: int = 0, limit: int = 100) -> list[database.Page]:
    return (
        db.query(database.Page)
        .order_by(database.Page.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_page(db: Session, url: str) -> bool:
    page = get_page_by_url(db, url)
    if page is None:
        return False
    db.delete(page)
    db.commit()
    return True
