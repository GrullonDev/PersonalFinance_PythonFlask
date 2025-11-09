
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models.profile import Profile
from app.models.user import User
from app.schema.profile import ProfileRead

router = APIRouter()

@router.get("/", response_model=List[ProfileRead])
def read_users(
    db: Session = Depends(get_db),
):
    """
    Retrieve all users.
    """
    users = db.execute(select(Profile)).scalars().all()
    return users

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a user by profile ID.
    """
    user = db.get(Profile, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Also delete the associated user from the users table
    user_aux = db.execute(select(User).where(User.id == user.firebase_uid)).scalar_one_or_none()
    if user_aux:
        db.delete(user_aux)

    db.delete(user)
    db.commit()
    return

@router.delete("/by-email/{email}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_email(
    email: str,
    db: Session = Depends(get_db),
):
    """
    Delete a user by email.
    """
    user = db.execute(select(Profile).where(Profile.email == email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Also delete the associated user from the users table
    user_aux = db.execute(select(User).where(User.id == user.firebase_uid)).scalar_one_or_none()
    if user_aux:
        db.delete(user_aux)

    db.delete(user)
    db.commit()
    return

@router.delete("/by-firebase-uid/{firebase_uid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_firebase_uid(
    firebase_uid: str,
    db: Session = Depends(get_db),
):
    """
    Delete a user by Firebase UID.
    """
    user = db.execute(select(Profile).where(Profile.firebase_uid == firebase_uid)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Also delete the associated user from the users table
    user_aux = db.execute(select(User).where(User.id == user.firebase_uid)).scalar_one_or_none()
    if user_aux:
        db.delete(user_aux)
        
    db.delete(user)
    db.commit()
    return
