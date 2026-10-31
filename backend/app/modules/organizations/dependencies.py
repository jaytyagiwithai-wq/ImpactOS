from uuid import UUID

from fastapi import HTTPException, status

from app.core.config import get_settings

LOCAL_ORG_ID = UUID("11111111-1111-4111-8111-111111111111")


def get_local_org_id() -> UUID:
    """Development fixture only; replace with verified identity before hosting."""
    if get_settings().app_env not in {"local", "test"}:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured",
        )
    return LOCAL_ORG_ID
