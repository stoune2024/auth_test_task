from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from apps.auth.services import decode_token
from apps.user.repository import UserRepository, get_session, AsyncSession
from apps.user.models import AccessRule, BusinessElement
from sqlalchemy import select


security = HTTPBearer()


async def get_current_user(
    token=Depends(security), session: AsyncSession = Depends(get_session)
):

    try:
        payload = decode_token(token.credentials)
        user = await UserRepository.get_by_id(session, payload["user_id"])
        if not user or not user.is_active:
            raise HTTPException(401)
        return user
    except:
        raise HTTPException(401, "Unauthorized")


async def permission_required(
    element_name: str,
    action: str,
    owner_id: int | None = None,
    session: AsyncSession = Depends(get_session),
):
    async def checker(user=Depends(get_current_user)):
        element = await session.scalar(
            select(BusinessElement).where(BusinessElement.name == element_name)
        )
        rule = await session.scalar(
            select(AccessRule).where(
                AccessRule.role_id == user.role_id, AccessRule.element_id == element.id
            )
        )

        if not rule:
            raise HTTPException(403)

        if action == "read":
            if rule.read_all_permission or rule.read_permission:
                return user
        if action == "update":
            if rule.update_all_permission:
                return user
            if rule.update_permission and owner_id == user.id:
                return user
        if action == "delete":
            if rule.delete_all_permission:
                return user
            if rule.delete_permission and owner_id == user.id:
                return user
        if action == "create" and rule.create_permission:
            return user

        raise HTTPException(403, "Forbidden")

    return checker
