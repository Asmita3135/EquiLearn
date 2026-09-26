"""
Database initialisation – creates all tables.
Called on app startup (app.py lifespan) and from test setUp.
No migrations framework yet; Alembic can replace this in a later stage.
"""
from db.models import Base
from db.session import engine


def create_tables() -> None:
    """Idempotently create all tables (safe to call repeatedly)."""
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """Test helper – destroy all tables so setUp starts clean."""
    Base.metadata.drop_all(bind=engine)
