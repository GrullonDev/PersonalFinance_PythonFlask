from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps.auth import get_current_profile
from app.models.category import Category, TipoMovimiento
from app.models.profile import Profile
from app.models.transaction import Transaction
from app.schema.transaction import TransactionCreate, TransactionRead, TransactionUpdate

router = APIRouter()


def _get_transaction_owned_by_profile(
    db: Session, profile: Profile, transaction_id: int
) -> Transaction:
    transaction = db.get(Transaction, transaction_id)
    if transaction is None or transaction.profile_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    return transaction


def _validate_category_ownership(db: Session, profile: Profile, categoria_id: int) -> None:
    category = db.get(Category, categoria_id)
    if category is None or category.profile_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La categoría no pertenece al usuario autenticado",
        )


@router.get("/", response_model=list[TransactionRead])
def list_transactions(
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    categoria_id: int | None = Query(default=None),
    tipo: TipoMovimiento | None = Query(default=None),
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> list[Transaction]:
    stmt = select(Transaction).where(Transaction.profile_id == current_profile.id)

    if fecha_desde:
        stmt = stmt.where(Transaction.fecha >= fecha_desde)
    if fecha_hasta:
        stmt = stmt.where(Transaction.fecha <= fecha_hasta)
    if categoria_id:
        stmt = stmt.where(Transaction.categoria_id == categoria_id)
    if tipo:
        stmt = stmt.where(Transaction.tipo == tipo)

    stmt = stmt.order_by(Transaction.fecha.desc(), Transaction.id.desc())
    return list(db.execute(stmt).scalars().all())


@router.get("/{transaction_id}", response_model=TransactionRead)
def retrieve_transaction(
    transaction_id: int,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> Transaction:
    return _get_transaction_owned_by_profile(db, current_profile, transaction_id)


@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> Transaction:
    _validate_category_ownership(db, current_profile, payload.categoria_id)

    transaction = Transaction(
        profile_id=current_profile.id,
        tipo=payload.tipo,
        monto=payload.monto,
        descripcion=payload.descripcion,
        fecha=payload.fecha,
        categoria_id=payload.categoria_id,
        es_recurrente=payload.es_recurrente,
    )
    db.add(transaction)
    db.flush()
    return transaction


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> Transaction:
    transaction = _get_transaction_owned_by_profile(db, current_profile, transaction_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "categoria_id" in update_data:
        _validate_category_ownership(db, current_profile, update_data["categoria_id"])

    for field, value in update_data.items():
        setattr(transaction, field, value)

    db.add(transaction)
    db.flush()
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db),
) -> None:
    transaction = _get_transaction_owned_by_profile(db, current_profile, transaction_id)
    db.delete(transaction)
