from fastapi import APIRouter

from app.routers import auth_local, budgets, categories, goals, profiles, transactions, users, notifications

api_router = APIRouter()
api_router.include_router(auth_local.router, prefix="/auth", tags=["auth"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

__all__ = ["api_router"]
