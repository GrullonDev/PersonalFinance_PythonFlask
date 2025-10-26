from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps.auth import get_current_profile
from app.models.goal import Goal
from app.models.profile import Profile
from app.schema.goal import GoalCreate, GoalRead, GoalUpdate

router = APIRouter()


def _get_goal_owned_by_profile(db: Session, profile: Profile, goal_id: int) -> Goal:
    goal = db.get(Goal, goal_id)
    if goal is None or goal.profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meta no encontrada")
    return goal


@router.get("/", response_model=list[GoalRead])
def list_goals(
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> list[Goal]:
    stmt = (
        select(Goal)
        .where(Goal.profile_id == current_profile.id)
        .order_by(Goal.fecha_limite)
    )
    return list(db.execute(stmt).scalars().all())


@router.post("/", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> Goal:
    if payload.monto_actual > payload.monto_objetivo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El monto actual no puede superar al monto objetivo",
        )

    goal = Goal(profile_id=current_profile.id, **payload.model_dump())
    db.add(goal)
    db.flush()
    return goal


@router.put("/{goal_id}", response_model=GoalRead)
def update_goal(
    goal_id: int,
    payload: GoalUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> Goal:
    goal = _get_goal_owned_by_profile(db, current_profile, goal_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "monto_actual" in update_data or "monto_objetivo" in update_data:
        nuevo_actual = update_data.get("monto_actual", goal.monto_actual)
        nuevo_objetivo = update_data.get("monto_objetivo", goal.monto_objetivo)
        if nuevo_actual > nuevo_objetivo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El monto actual no puede superar al monto objetivo",
            )

    for field, value in update_data.items():
        setattr(goal, field, value)

    db.add(goal)
    db.flush()
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> None:
    goal = _get_goal_owned_by_profile(db, current_profile, goal_id)
    db.delete(goal)
