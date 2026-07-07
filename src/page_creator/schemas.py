"""Pydantic request/response models for the Page Creator API."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, Field


class PageCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Page title")
    content: str | None = Field(
        default=None,
        description=(
            "Page body content. If omitted, a basic placeholder is generated "
            "from the title. When called from an AI client (e.g. Claude via "
            "the MCP server), the AI is expected to generate rich content "
            "and pass it here."
        ),
    )
    url: str | None = Field(
        default=None,
        description="Optional custom URL slug. Auto-generated from the title if omitted.",
    )


class PageResponse(BaseModel):
    id: int
    title: str
    content: str
    url: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class PageListResponse(BaseModel):
    id: int
    title: str
    url: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True
