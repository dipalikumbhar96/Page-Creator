def main() -> None:
    """Entry point: runs the FastAPI server with uvicorn."""
    import uvicorn

    uvicorn.run("page_creator.main:app", host="0.0.0.0", port=8000, reload=True)
