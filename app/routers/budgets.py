from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps.auth import get_current_profile
from app.models.budget import Budget
from app.models.profile import Profile
from app.schema.budget import BudgetCreate, BudgetRead, BudgetUpdate

router = APIRouter()


def _get_budget_owned_by_profile(db: Session, profile: Profile, budget_id: int) -> Budget:
    budget = db.get(Budget, budget_id)
    if budget is None or budget.profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presupuesto no encontrado")
    return budget


@router.get("/", response_model=list[BudgetRead])
def list_budgets(
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> list[Budget]:
    stmt = (
        select(Budget)
        .where(Budget.profile_id == current_profile.id)
        .order_by(Budget.fecha_inicio.desc())
    )
    return list(db.execute(stmt).scalars().all())


@router.post("/", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetCreate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> Budget:
    if payload.fecha_fin < payload.fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser mayor o igual a la fecha de inicio",
        )

    duplicate_stmt = select(Budget).where(
        and_(
            Budget.profile_id == current_profile.id,
            Budget.nombre == payload.nombre,
            Budget.fecha_inicio == payload.fecha_inicio,
            Budget.fecha_fin == payload.fecha_fin,
        )
    )
    if db.execute(duplicate_stmt).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un presupuesto con ese nombre y rango de fechas",
        )

    budget = Budget(profile_id=current_profile.id, **payload.model_dump())
    db.add(budget)
    db.flush()
    return budget


@router.put("/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: int,
    payload: BudgetUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> Budget:
    budget = _get_budget_owned_by_profile(db, current_profile, budget_id)

    new_inicio = payload.fecha_inicio or budget.fecha_inicio
    new_fin = payload.fecha_fin or budget.fecha_fin
    if new_fin < new_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser mayor o igual a la fecha de inicio",
        )

    if payload.nombre or payload.fecha_inicio or payload.fecha_fin:
        duplicate_stmt = select(Budget).where(
            and_(
                Budget.id != budget.id,
                Budget.profile_id == current_profile.id,
                Budget.nombre == (payload.nombre or budget.nombre),
                Budget.fecha_inicio == new_inicio,
                Budget.fecha_fin == new_fin,
            )
        )
        if db.execute(duplicate_stmt).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un presupuesto con ese nombre y rango de fechas",
            )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)

    db.add(budget)
    db.flush()
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> None:
    budget = _get_budget_owned_by_profile(db, current_profile, budget_id)
    db.delete(budget)
