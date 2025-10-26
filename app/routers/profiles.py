from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps.auth import get_current_profile
from app.models.profile import Profile
from app.schema.profile import ProfileRead, ProfileUpdate

router = APIRouter()


@router.get("/me", response_model=ProfileRead)
def read_current_profile(current_profile: Profile = Depends(get_current_profile)) -> Profile:
    """Return the authenticated user's profile."""
    return current_profile


@router.put("/me", response_model=ProfileRead)
def update_current_profile(
    payload: ProfileUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> Profile:
    """Allow the authenticated user to update mutable profile fields."""
    if payload.nombre_completo:
        current_profile.nombre_completo = payload.nombre_completo

    db.add(current_profile)
    db.flush()
    return current_profile
