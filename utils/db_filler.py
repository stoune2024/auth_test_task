import json
from pathlib import Path
from sqlalchemy import select

from apps.user.schemas import Role, BusinessElement, AccessRule


async def seed_access_data(session, json_path: str = "access_rules.json"):
    """
    Заполняет БД тестовыми ролями/ресурсами/правами из JSON.
    Без создания дубликатов.
    """

    path = Path(json_path)

    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {json_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Roles
    for role_data in data["roles"]:
        existing = await session.scalar(
            select(Role).where(Role.name == role_data["name"])
        )

        if not existing:
            session.add(Role(name=role_data["name"]))

    await session.flush()

    # Business Elements
    for element_data in data["business_elements"]:
        existing = await session.scalar(
            select(BusinessElement).where(BusinessElement.name == element_data["name"])
        )

        if not existing:
            session.add(BusinessElement(name=element_data["name"]))

    await session.flush()

    # Access Rules
    for rule_data in data["access_rules"]:
        role = await session.scalar(select(Role).where(Role.name == rule_data["role"]))

        element = await session.scalar(
            select(BusinessElement).where(BusinessElement.name == rule_data["element"])
        )

        existing_rule = await session.scalar(
            select(AccessRule).where(
                AccessRule.role_id == role.id, AccessRule.element_id == element.id
            )
        )

        if existing_rule:
            continue

        session.add(
            AccessRule(
                role_id=role.id,
                element_id=element.id,
                read_permission=rule_data.get("read_permission", False),
                read_all_permission=rule_data.get("read_all_permission", False),
                create_permission=rule_data.get("create_permission", False),
                update_permission=rule_data.get("update_permission", False),
                update_all_permission=rule_data.get("update_all_permission", False),
                delete_permission=rule_data.get("delete_permission", False),
                delete_all_permission=rule_data.get("delete_all_permission", False),
            )
        )

    await session.commit()
