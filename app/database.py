import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

def _database_url():
    value = os.getenv("DATABASE_URL")
    if value:
        return value
    # Streamlit Community Cloud exposes secrets through st.secrets, not env vars.
    try:
        import streamlit as st
        value = st.secrets.get("DATABASE_URL")
    except Exception:
        value = None
    return value or "sqlite:///./inventory.db"

DATABASE_URL = _database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
