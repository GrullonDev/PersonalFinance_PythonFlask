from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class NotificationPreferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email_enabled: bool
    push_enabled: bool
    marketing_enabled: bool


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: bool | None = None
    push_enabled: bool | None = None
    marketing_enabled: bool | None = None

