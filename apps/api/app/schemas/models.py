from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


CalendarType = Literal["gregorian", "lunar"]
TimePrecision = Literal["minute", "double_hour", "half_day", "unknown"]


class BirthPlace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str | None = Field(default=None, max_length=200)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    coordinate_source: str = Field(min_length=1, max_length=100)


class OriginalBirthRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    calendar_type: CalendarType
    local_date: date
    local_time: time | None
    timezone_id: str = Field(min_length=1, max_length=100)
    timezone_database: str = "IANA"
    timezone_database_version: str = Field(min_length=1, max_length=30)
    time_precision: TimePrecision
    place: BirthPlace
    user_confirmed: bool
    captured_at: datetime

    @model_validator(mode="after")
    def unknown_time_has_no_value(self):
        if self.time_precision == "unknown" and self.local_time is not None:
            raise ValueError("unknown time precision must not include local_time")
        if self.time_precision != "unknown" and self.local_time is None:
            raise ValueError("known time precision requires local_time")
        return self


class ProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str | None = Field(default=None, max_length=100)
    consent_version: str = Field(min_length=1, max_length=50)
    birth: OriginalBirthRecord


class ProfilePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str | None = Field(default=None, max_length=100)
    birth: OriginalBirthRecord | None = None


class ProfileView(ProfileCreate):
    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime


class InvitationAccept(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=20, max_length=512)


class SessionView(BaseModel):
    user_id: UUID
    role: Literal["owner", "member", "viewer"]


class TimeCandidate(BaseModel):
    candidate_id: str
    basis: Literal["civil", "local_mean_solar", "local_apparent_solar", "unknown_interval"]
    local_datetime: datetime | None
    utc_datetime: datetime | None
    method_id: str
    is_primary_chart: bool = False


class BoundaryDifference(BaseModel):
    crosses_double_hour_boundary: bool
    crosses_civil_date_boundary: bool
    crosses_solar_term_boundary: bool
    sensitive_rules: list[str]


class CorrectionStep(BaseModel):
    step: str
    input_value: str
    output_value: str
    offset_minutes: float
    source_id: str


class BirthTimeNormalizationResult(BaseModel):
    original: OriginalBirthRecord
    historical_utc_offset_minutes: int | None
    dst_offset_minutes: int | None
    longitude_correction_minutes: float | None
    equation_of_time_minutes: float | None
    total_apparent_correction_minutes: float | None
    candidates: list[TimeCandidate]
    boundary_difference: BoundaryDifference
    correction_chain: list[CorrectionStep]
    warnings: list[str]
    prohibited_conclusions: list[str]


class NormalizeBirthTimeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    solar_term_instants_utc: list[datetime] = []


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
