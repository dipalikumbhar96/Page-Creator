# Page Creator

A small project that lets you (or an AI assistant like Claude) create
simple content pages and fetch them back by URL.

- **FastAPI** — REST API to create/list/fetch pages
- **SQLite (SQLAlchemy)** — stores `title`, `content`, `url`, `created_at`
- **MCP server** — exposes the page-creation flow as tools so Claude can
  call it directly ("create page for me on home loan" → Claude writes the
  content → page is saved → you get back the URL to check)

## Project layout

```
page-creator/
├── pyproject.toml
├── src/page_creator/
│   ├── __init__.py       # `page-creator` CLI entry (runs the API)
│   ├── database.py       # SQLAlchemy engine, session, Page model
│   ├── schemas.py        # Pydantic request/response models
│   ├── crud.py           # DB operations (create/list/get/delete)
│   ├── utils.py          # slugify + unique URL generation + fallback content
│   ├── main.py           # FastAPI app & routes
│   └── mcp_server.py     # MCP server (stdio) exposing tools to Claude
└── data/pages.db         # SQLite DB file (created automatically)
```

## 1. Install dependencies

```bash
uv sync
```

## 2. Run the API server

```bash
uv run page-creator
# or explicitly:
uv run uvicorn page_creator.main:app --reload
```

This starts FastAPI at `http://127.0.0.1:8000`. Interactive docs at
`http://127.0.0.1:8000/docs`.

### API endpoints

| Method | Path            | Description                          |
|--------|-----------------|---------------------------------------|
| POST   | `/pages`        | Create a page (`title`, `content?`, `url?`) |
| GET    | `/pages`        | List pages (id, title, url, created_at) |
| GET    | `/pages/{url}`  | Get a full page by its URL slug       |
| DELETE | `/pages/{url}`  | Delete a page                         |

If `content` is omitted, a basic placeholder is stored. If `url` is
omitted, it's auto-generated from the title (e.g. "Home Loan" → `home-loan`,
with `-2`, `-3`, ... appended on collisions).

Example:
```bash
curl -X POST http://127.0.0.1:8000/pages \
  -H "Content-Type: application/json" \
  -d '{"title": "Home Loan", "content": "A home loan is a secured loan used to buy property..."}'
```

## 3. Run the MCP server

The MCP server talks to the FastAPI server over HTTP, so **keep the API
running** in one terminal, then in another:

```bash
uv run page-creator-mcp
```

It exposes 3 tools:
- `create_page(title, content, url?)` — creates a page and returns its URL
- `list_pages(limit?)` — lists recent pages
- `get_page(url)` — fetches a page's full content

## 4. Connect it to Claude

### Claude Desktop
Add this to your `claude_desktop_config.json` (adjust the path):

```json
{
  "mcpServers": {
    "page-creator": {
      "command": "uv",
      "args": ["run", "page-creator-mcp"],
      "cwd": "/absolute/path/to/page-creator"
    }
  }
}
```

Restart Claude Desktop. Make sure the FastAPI server (`uv run page-creator`)
is running before you use the tool.

### How the "AI generates content" flow works

When you tell Claude:

> "Create a page for me on home loan"

Claude sees the `create_page` tool description, which asks the *caller*
to generate rich content for the title. So Claude:
1. Writes the page content itself (an overview of home loans, types,
   eligibility, etc.), based on the title "Home Loan".
2. Calls `create_page(title="Home Loan", content="<generated content>")`.
3. The MCP server derives a unique URL slug and POSTs it to the FastAPI
   API, which saves it to SQLite.
4. Claude gets back the URL (e.g. `/pages/home-loan`) and shows it to you
   so you can check it via `GET http://127.0.0.1:8000/pages/home-loan`.

If you (or another non-AI client) call `create_page` without `content`,
a basic placeholder is stored instead — content generation is the AI's
job, not the server's.

## Environment variables

- `PAGE_CREATOR_API_URL` — override the API base URL the MCP server calls
  (default `http://127.0.0.1:8000`).
