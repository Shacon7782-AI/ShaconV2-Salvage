import asyncio
from sqlalchemy import text
from app.db.schemas.session import engine, SessionLocal
from app.db.schemas.models import Base

def init_db():
    print("Creating vector extension...")
    db = SessionLocal()
    try:
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        db.commit()
    except Exception as e:
        print(f"Error creating extension: {e}")
        db.rollback()
    finally:
        db.close()

    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
