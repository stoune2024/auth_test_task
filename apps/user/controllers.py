from apps.user.routers import user_router
from fastapi import APIRouter, Depends, HTTPException
from utils.permissions import get_current_user, permission_required


@user_router.get("/access-rules")
async def get_rules(user=Depends(get_current_user)):
    if user.role.name != "admin":
        raise HTTPException(403)
    return {"message": "list of access rules"}


@user_router.get("/")
async def products(user=Depends(permission_required("products", "read", session))):
    return [{"id": 1, "name": "Laptop", "owner_id": 1}]
