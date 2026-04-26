from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .models import Coverage, DistrictSummary, Holiday, MunicipalitySummary, RegionSummary, SourceRef
from .repository import coverage, get_holidays, list_districts, list_municipalities, list_regions, list_sources

app = FastAPI(
    title="PT Holidays API",
    version="0.1.0",
    description="Feriados nacionais, regionais e municipais de Portugal com proveniencia.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

CACHEABLE_PATHS = {
    "/coverage",
    "/districts",
    "/health",
    "/holidays",
    "/municipalities",
    "/regions",
    "/sources",
}


@app.middleware("http")
async def add_cache_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    if request.method == "GET" and request.url.path in CACHEABLE_PATHS and response.status_code == 200:
        response.headers["Cache-Control"] = (
            "public, max-age=300, s-maxage=86400, stale-while-revalidate=604800"
        )
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/holidays", response_model=list[Holiday])
def holidays(
    year: int = Query(..., ge=1900, le=2100),
    region: str | None = Query(None, description="azores/acores or madeira"),
    district: str | None = Query(None, description="Distrito ou regiao administrativa"),
    municipality: str | None = Query(None, description="Nome do concelho"),
) -> list[Holiday]:
    result = get_holidays(year=year, region=region, district=district, municipality=municipality)
    if (municipality or district) and not any(item.scope == "municipal" for item in result):
        raise HTTPException(
            status_code=404,
            detail="Distrito/municipio sem dados para esse ano. Consulte /coverage, /districts e /municipalities.",
        )
    return result


@app.get("/regions", response_model=list[RegionSummary])
def regions() -> list[RegionSummary]:
    return list_regions()


@app.get("/districts", response_model=list[DistrictSummary])
def districts() -> list[DistrictSummary]:
    return list_districts()


@app.get("/municipalities", response_model=list[MunicipalitySummary])
def municipalities() -> list[MunicipalitySummary]:
    return list_municipalities()


@app.get("/sources", response_model=list[SourceRef])
def api_sources() -> list[SourceRef]:
    return list_sources()


@app.get("/coverage", response_model=Coverage)
def api_coverage() -> Coverage:
    return coverage()
