from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.db import get_cached_report, save_cached_report
from app.models.schemas import ReportResponse
from app.services.analysis_service import REPORT_SCHEMA_VERSION, get_analysis_service, normalize_player_tag
from app.services.clash_api import ClashApiService

router = APIRouter()


@router.get("/demo-victims")
def demo_victims() -> dict[str, object]:
    api = ClashApiService()
    return {"mock_mode": settings.use_mock_data, "victims": api.list_demo_victims()}


@router.get("/reports/{player_tag:path}", response_model=ReportResponse)
async def report(
    player_tag: str,
    goblin_mode: bool = Query(False),
    seed: str | None = Query(None),
    refresh: bool = Query(False),
) -> dict[str, object]:
    normalized = normalize_player_tag(player_tag)
    if not normalized:
        raise HTTPException(status_code=400, detail="Invalid player tag. Try a tag like #MID001.")

    cache_key = f"{REPORT_SCHEMA_VERSION}:{normalized}:{goblin_mode}:{seed}:{settings.use_mock_data}"
    if not refresh:
        cached = get_cached_report(cache_key)
        if cached and cached.get("schema_version") == REPORT_SCHEMA_VERSION:
            return cached

    clash_api = ClashApiService()
    player = await clash_api.get_player(normalized)
    battles = await clash_api.get_battlelog(normalized)
    if not battles:
        raise HTTPException(status_code=404, detail="Battle log is empty or unavailable.")

    report_payload = get_analysis_service().build_report(
        player,
        battles,
        seed=seed or normalized,
        goblin_mode=goblin_mode,
    )
    save_cached_report(cache_key, report_payload)
    return report_payload
