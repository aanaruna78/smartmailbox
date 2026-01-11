import asyncio
import os
import sys

# Add the parent directory to sys.path to identify 'apps'
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.api.app.core.config import settings
from apps.api.app.models.user import User
from apps.api.app.core.security.jwt import get_password_hash

def seed_admin_user():
    print("Seeding admin user...")
    engine = create_engine(str(settings.DATABASE_URL))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        admin_email = "admin@smartmailbox.com"
        existing_user = db.query(User).filter(User.email == admin_email).first()
        
        if not existing_user:
            print(f"Creating admin user: {admin_email}")
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash("admin123"),
                full_name="System Admin",
                is_active=True,
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")
            
    except Exception as e:
        print(f"Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin_user()
