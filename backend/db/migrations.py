"""Idempotent table creation — called on every app startup."""
from db.connection import Base, engine

def create_tables() -> None:
    # Import models so Base.metadata is populated
    import db.models  # noqa: F401
    Base.metadata.create_all(bind=engine)