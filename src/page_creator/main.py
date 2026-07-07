"""FastAPI app exposing the page creation API."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, database, schemas

app = FastAPI(
    title="Page Creator API",
    description="Create and fetch simple content pages (title, content, url, created_at).",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    database.init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/pages", response_model=schemas.PageResponse, status_code=201)
def create_page(payload: schemas.PageCreate, db: Session = Depends(database.get_db)):
    page = crud.create_page(db, title=payload.title, content=payload.content, url=payload.url)
    return page


@app.get("/pages", response_model=list[schemas.PageListResponse])
def list_pages(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return crud.list_pages(db, skip=skip, limit=limit)


@app.get("/pages/{url}", response_model=schemas.PageResponse)
def get_page(url: str, db: Session = Depends(database.get_db)):
    page = crud.get_page_by_url(db, url)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@app.delete("/pages/{url}", status_code=204)
def delete_page(url: str, db: Session = Depends(database.get_db)):
    deleted = crud.delete_page(db, url)
    if not deleted:
        raise HTTPException(status_code=404, detail="Page not found")
    return None
