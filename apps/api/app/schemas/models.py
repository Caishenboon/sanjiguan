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


EvidenceDomain = Literal["ming", "gua", "karma", "vow", "dream", "sensation", "relation", "life_event"]
AnswerState = Literal["not_filled", "not_applicable", "unknown", "explicit_none", "filled"]


class OnboardingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_step: int = Field(ge=1, le=8)
    step_states: dict[str, Literal["complete", "unknown", "explicit_none", "not_applicable", "later"]]
    draft: dict


class EvidenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    domain: EvidenceDomain
    type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    raw_narrative: str = Field(default="", max_length=10000)
    structured_payload: dict = {}
    observed_from: date | None = None
    observed_to: date | None = None
    first_observed_age: float | None = Field(default=None, ge=0, le=150)
    frequency: int = Field(default=0, ge=0, le=10)
    intensity: int = Field(default=0, ge=0, le=10)
    vividness: int = Field(default=0, ge=0, le=10)
    duration_years: float = Field(default=0, ge=0)
    source_type: Literal["document", "self_memory", "family_memory",
                         "repeated_observation", "single_event"]
    user_confidence: float = Field(ge=0, le=1)
    independent_corroboration: bool = False
    possible_ordinary_explanations: list[str] = []
    counterevidence: list[str] = []
    event_occurred_at: datetime | None = None


class EvidencePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, max_length=200)
    raw_narrative: str | None = Field(default=None, max_length=10000)
    structured_payload: dict | None = None
    status: Literal["draft", "confirmed", "disputed", "withdrawn"] | None = None
    possible_ordinary_explanations: list[str] | None = None
    counterevidence: list[str] | None = None


class JournalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entry_date: date
    entry_type: Literal["practice", "dream", "emotion", "affliction", "insight",
                        "relationship", "life_event", "vow_action", "reflection"]
    fields: dict
    free_text: str = Field(default="", max_length=10000)
    tags: list[str] = []
    evidence_ids: list[UUID] = []
    candidate_evidence: bool = False


class JournalPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fields: dict | None = None
    free_text: str | None = Field(default=None, max_length=10000)
    tags: list[str] | None = None
    candidate_evidence: bool | None = None


class RelationshipSubjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["consented_profile", "pending_consent", "anonymous_event"]
    linked_profile_id: UUID | None = None
    alias: str | None = Field(default=None, max_length=100)
    event_payload: dict = {}


class RelationshipConsentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consent_version: str
    consent_status: Literal["pending", "granted", "withdrawn", "expired", "anonymous_event_mode"]
    evidence_type: Literal["self_attestation", "signed_record",
                           "linked_profile_confirmation", "none"]
    scope: list[str]
    expires_at: datetime | None = None


class CoinTossInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    line_no: int = Field(ge=1, le=6)
    coin_faces: list[Literal["heads", "tails"]] = Field(min_length=3, max_length=3)
    was_retossed: bool = False


class ThreeCoinDivinationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=2000)
    purpose: str = Field(min_length=1, max_length=1000)
    divination_at: datetime
    timezone: str
    location_precision: Literal["none", "region", "city"]
    method_id: Literal["YIJING.THREE_COIN.PHYSICAL.V1"]
    tosses: list[CoinTossInput] = Field(min_length=6, max_length=6)
    interrupted_retoss: bool = False
    repeated_due_to_dissatisfaction: bool = False
    method_version: Literal["1.0.0"]
