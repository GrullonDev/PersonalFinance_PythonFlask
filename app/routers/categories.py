from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps.auth import get_current_profile
from app.models.category import Category
from app.models.profile import Profile
from app.schema.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter()


def _get_category_owned_by_profile(db: Session, profile: Profile, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None or category.profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    return category


@router.get("/", response_model=list[CategoryRead])
def list_categories(
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> list[Category]:
    stmt = (
        select(Category)
        .where(Category.profile_id == current_profile.id)
        .order_by(Category.tipo, func.lower(Category.nombre))
    )
    return list(db.execute(stmt).scalars().all())


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> Category:
    duplicate_stmt = select(Category).where(
        and_(
            Category.profile_id == current_profile.id,
            func.lower(Category.nombre) == func.lower(payload.nombre),
            Category.tipo == payload.tipo,
        )
    )
    if db.execute(duplicate_stmt).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una categoría con ese nombre y tipo",
        )

    category = Category(
        profile_id=current_profile.id,
        nombre=payload.nombre,
        tipo=payload.tipo,
    )
    db.add(category)
    db.flush()
    return category


@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> Category:
    category = _get_category_owned_by_profile(db, current_profile, category_id)

    if payload.nombre is not None and payload.tipo is None:
        # Validamos duplicados si cambia únicamente el nombre
        duplicate_stmt = select(Category).where(
            and_(
                Category.id != category.id,
                Category.profile_id == current_profile.id,
                func.lower(Category.nombre) == func.lower(payload.nombre),
                Category.tipo == category.tipo,
            )
        )
        if db.execute(duplicate_stmt).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una categoría con ese nombre y tipo",
            )

    if payload.tipo is not None and payload.nombre is None:
        duplicate_stmt = select(Category).where(
            and_(
                Category.id != category.id,
                Category.profile_id == current_profile.id,
                Category.nombre == category.nombre,
                Category.tipo == payload.tipo,
            )
        )
        if db.execute(duplicate_stmt).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una categoría con ese nombre y tipo",
            )

    if payload.nombre is not None:
        category.nombre = payload.nombre
    if payload.tipo is not None:
        category.tipo = payload.tipo

    db.add(category)
    db.flush()
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> None:
    category = _get_category_owned_by_profile(db, current_profile, category_id)
    db.delete(category)
