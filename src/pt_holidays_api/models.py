from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


HolidayScope = Literal["national", "regional", "municipal"]
VerificationStatus = Literal["verified", "cross_checked", "needs_primary_source"]


class SourceRef(BaseModel):
    id: str
    name: str
    url: str


class Holiday(BaseModel):
    date: date
    name: str
    scope: HolidayScope
    region: str | None = None
    district: str | None = None
    municipality: str | None = None
    sources: list[str] = Field(default_factory=list)
    verification_status: VerificationStatus
    confidence: float = Field(ge=0, le=1)


class Coverage(BaseModel):
    national_years: str
    regional_years: str
    municipal_years: list[int]
    municipalities: int
    verification_policy: str


class RegionHolidaySummary(BaseModel):
    name: str
    start_year: int
    sources: list[str] = Field(default_factory=list)
    verification_status: VerificationStatus
    confidence: float = Field(ge=0, le=1)


class RegionSummary(BaseModel):
    region: str
    type: str = "autonomous_region"
    available_years: str
    holidays: list[RegionHolidaySummary]


class MunicipalitySummary(BaseModel):
    municipality: str
    district: str
    holiday_name: str
    available_years: list[int]
    sources: list[str] = Field(default_factory=list)
    verification_status: VerificationStatus
    confidence: float = Field(ge=0, le=1)
