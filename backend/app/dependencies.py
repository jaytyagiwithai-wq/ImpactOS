from sqlalchemy.orm import Session
from shared.db.session import engine
from uuid import UUID
from app.core.config import get_settings
from fastapi import HTTPException, status
from collections.abc import Iterator

local_org_id = UUID("11111111-1111-4111-8111-111111111111")


#Gives each req its own sqlAlchmey session. After the endpoint finishes with closes it and releases db resources

def get_session() -> Iterator[Session]:
    with Session(engine, expire_on_commit=False) as session:
        yield session

#supplies fied org for dev
def get_local_org_id() -> UUID:
    if get_settings().app_env not in ["local","test"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured"

        )
    return local_org_id