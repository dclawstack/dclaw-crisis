"""Public download endpoint for exports stored in the in-memory simulator.

When `MINIO_DISABLED=true`, the object store's "presigned URL" is just
`/api/v1/exports/local/{key}` served by this router. With real MinIO,
presigned URLs hit MinIO directly and this route is unused.

Deliberately unprotected so download links work without re-attaching the
bearer token (the same way real S3 presigned URLs work — the signature
in the URL is the auth).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response

from app.core.object_store import get_object_store

router = APIRouter()


@router.get("/local/{key:path}", include_in_schema=False)
async def download_local_export(key: str) -> Response:
    store = get_object_store()
    text = store.get_text(key)
    if text is None:
        raise HTTPException(status_code=404, detail="Export not found")
    media = "text/markdown" if key.endswith(".md") else "text/plain"
    return PlainTextResponse(text, media_type=media)
