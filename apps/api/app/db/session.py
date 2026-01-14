from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# Handle SQLite vs PostgreSQL
database_url = str(settings.DATABASE_URL)
if database_url.startswith("sqlite"):
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

