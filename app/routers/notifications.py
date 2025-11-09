from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps.auth import get_current_profile
from app.models.notification_preference import NotificationPreference
from app.models.profile import Profile
from app.schema.notification import (
    NotificationPreferenceRead,
    NotificationPreferenceUpdate,
)

router = APIRouter()


def _get_or_create_preferences(db: Session, profile: Profile) -> NotificationPreference:
    prefs = profile.notification_preference
    if prefs is None:
        prefs = NotificationPreference(profile_id=profile.id)
        db.add(prefs)
        db.flush()
        db.refresh(profile, attribute_names=["notification_preference"])
    return prefs


@router.get("/preferences", response_model=NotificationPreferenceRead)
def get_preferences(
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> NotificationPreference:
    return _get_or_create_preferences(db, current_profile)


@router.put("/preferences", response_model=NotificationPreferenceRead)
def update_preferences(
    payload: NotificationPreferenceUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> NotificationPreference:
    prefs = _get_or_create_preferences(db, current_profile)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(prefs, field, value)
    db.add(prefs)
    db.flush()
    return prefs

