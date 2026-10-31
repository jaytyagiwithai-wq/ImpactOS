from collections.abc import Iterator
from pgvector.psycopg import register_vector
from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    url=settings.database_url.get_secret_value(),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    hide_parameters=True,
    pool_timeout=3,
    connect_args={
        "connect_timeout": 3,
        "options": "-c statement_timeout=3000",
    },
)

@event.listens_for(engine, "connect")
def register_pgvector(dbapi_connection, _connection_record):
    register_vector(dbapi_connection)


def get_session() -> Iterator[Session]:
    """A request owns its session; the application service owns transactions."""
    with Session(engine, expire_on_commit=False) as session:
        yield session
