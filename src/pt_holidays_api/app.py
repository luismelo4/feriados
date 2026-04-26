from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from .models import Coverage, Holiday, SourceRef
from .repository import coverage, get_holidays, list_municipalities, list_sources

app = FastAPI(
    title="PT Holidays API",
    version="0.1.0",
    description="Feriados nacionais, regionais e municipais de Portugal com proveniencia.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/holidays", response_model=list[Holiday])
def holidays(
    year: int = Query(..., ge=1900, le=2100),
    region: str | None = Query(None, description="azores/acores or madeira"),
    municipality: str | None = Query(None, description="Nome do concelho"),
) -> list[Holiday]:
    result = get_holidays(year=year, region=region, municipality=municipality)
    if municipality and not any(item.scope == "municipal" for item in result):
        raise HTTPException(
            status_code=404,
            detail="Municipio sem dados para esse ano. Consulte /coverage e /municipalities.",
        )
    return result


@app.get("/municipalities")
def municipalities() -> list[dict]:
    return list_municipalities()


@app.get("/sources", response_model=list[SourceRef])
def api_sources() -> list[SourceRef]:
    return list_sources()


@app.get("/coverage", response_model=Coverage)
def api_coverage() -> Coverage:
    return coverage()
