from __future__ import annotations

import re

from pydantic import BaseModel, Field, ValidationError, field_validator

from .schema import MalwareLabel, NormalAppLabel


SAFE_PART = re.compile(r"^[A-Za-z0-9._-]+$")


class InvalidLabelError(ValueError):
    """Raised when a label component contains invalid characters."""


class MalwareLabelPayload(BaseModel):
    platform: str = Field(min_length=1, max_length=32)
    malware_primary: str = Field(min_length=1, max_length=64)
    family: str = Field(min_length=1, max_length=64)
    variant: str = Field(min_length=1, max_length=32)
    subtype: str = Field(min_length=1, max_length=64)

    @field_validator("platform", "malware_primary", "family", "variant", "subtype")
    @classmethod
    def validate_text_part(cls, value: str) -> str:
        if not SAFE_PART.fullmatch(value):
            raise InvalidLabelError(
                f"Invalid label part '{value}'. Allowed chars are letters, numbers, . _ -."
            )
        return value


class NormalAppLabelPayload(BaseModel):
    platform: str = Field(min_length=1, max_length=32)
    app_name: str = Field(min_length=1, max_length=64)
    build_ref: str = Field(min_length=1, max_length=64)
    app_category: str = Field(min_length=1, max_length=64)

    @field_validator("platform", "app_name", "build_ref", "app_category")
    @classmethod
    def validate_text_part(cls, value: str) -> str:
        if not SAFE_PART.fullmatch(value):
            raise InvalidLabelError(
                f"Invalid label part '{value}'. Allowed chars are letters, numbers, . _ -."
            )
        return value


def _to_payload(model_type, raw):
    if isinstance(raw, (MalwareLabel, NormalAppLabel)):
        return model_type(**raw.__dict__)
    if isinstance(raw, dict):
        return model_type(**raw)
    raise TypeError("label payload must be a dict or a dataclass")


def render_malware_label(payload: dict | MalwareLabel) -> str:
    try:
        data = _to_payload(MalwareLabelPayload, payload)
    except ValidationError as exc:
        raise InvalidLabelError(str(exc)) from exc
    return f"{data.platform}:{data.malware_primary}.{data.family}-{data.variant}:[{data.subtype}]"


def render_normal_app_label(payload: dict | NormalAppLabel) -> str:
    try:
        data = _to_payload(NormalAppLabelPayload, payload)
    except ValidationError as exc:
        raise InvalidLabelError(str(exc)) from exc
    return f"{data.platform}:{data.app_name}-{data.build_ref}:[{data.app_category}]"
