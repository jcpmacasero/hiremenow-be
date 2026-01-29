"""
Seed script to create initial admin user.
Run with: python -m scripts.seed_admin
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password


def create_admin():
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin:
            print(f"Admin user already exists: {admin.email}")
            return

        # Create admin user
        admin = User(
            email="admin@hiremenow.com",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print(f"Created admin user: admin@hiremenow.com / admin123")
        print("WARNING: Change the password immediately!")
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
