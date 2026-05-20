from fastapi import APIRouter
from fastapi.responses import Response

from app.core.metrics import metrics_payload

router = APIRouter()


@router.get("/", include_in_schema=False)
@router.get("", include_in_schema=False)
async def metrics() -> Response:
    body, content_type = metrics_payload()
    return Response(content=body, media_type=content_type)
