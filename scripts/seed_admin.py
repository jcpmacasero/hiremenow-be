"""
Seed script to create initial admin and test users for each role.
Run with: python -m scripts.seed_admin

Creates (if not already present):
- admin@hiremenow.com / admin123 (admin)
- candidate@hiremenow.com / candidate123 (candidate + candidate profile)
- employer@hiremenow.com / employer123 (employer + company)
- partner@hiremenow.com / partner123 (partner)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User
from app.models.candidate import Candidate
from app.models.company import Company
from app.models.employer import Employer
from app.core.security import hash_password

# Test users: email -> (password, role)
TEST_USERS = [
    ("admin@hiremenow.com", "admin123", "admin"),
    ("candidate@hiremenow.com", "candidate123", "candidate"),
    ("employer@hiremenow.com", "employer123", "employer"),
    ("partner@hiremenow.com", "partner123", "partner"),
]


def create_admin(db):
    """Create admin user if not exists."""
    existing = db.query(User).filter(User.email == "admin@hiremenow.com").first()
    if existing:
        print("Admin user already exists: admin@hiremenow.com")
        return
    user = User(
        email="admin@hiremenow.com",
        password_hash=hash_password("admin123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print("Created admin: admin@hiremenow.com / admin123")


def create_candidate(db):
    """Create candidate user + profile if not exists."""
    existing = db.query(User).filter(User.email == "candidate@hiremenow.com").first()
    if existing:
        print("Candidate user already exists: candidate@hiremenow.com")
        return
    user = User(
        email="candidate@hiremenow.com",
        password_hash=hash_password("candidate123"),
        role="candidate",
        is_active=True,
    )
    db.add(user)
    db.flush()
    candidate = Candidate(
        user_id=user.id,
        first_name="Test",
        last_name="Candidate",
        phone="+421900000001",
        current_stage="lead",
        source="website",
    )
    db.add(candidate)
    db.commit()
    print("Created candidate: candidate@hiremenow.com / candidate123 (with profile)")


def create_employer(db):
    """Create company + employer user if not exists."""
    existing = db.query(User).filter(User.email == "employer@hiremenow.com").first()
    if existing:
        print("Employer user already exists: employer@hiremenow.com")
        return
    company = db.query(Company).filter(Company.slug == "test-company").first()
    if not company:
        company = Company(
            name="Test Company",
            slug="test-company",
            description="Test company for employer portal",
            location="Bratislava",
            industry="Manufacturing",
            is_agency_owned=False,
            is_active=True,
        )
        db.add(company)
        db.flush()
        print("Created company: Test Company (slug: test-company)")
    user = User(
        email="employer@hiremenow.com",
        password_hash=hash_password("employer123"),
        role="employer",
        is_active=True,
    )
    db.add(user)
    db.flush()
    employer = Employer(user_id=user.id, company_id=company.id)
    db.add(employer)
    db.commit()
    print("Created employer: employer@hiremenow.com / employer123 (linked to Test Company)")


def create_partner(db):
    """Create partner user if not exists (no Partner profile table yet)."""
    existing = db.query(User).filter(User.email == "partner@hiremenow.com").first()
    if existing:
        print("Partner user already exists: partner@hiremenow.com")
        return
    user = User(
        email="partner@hiremenow.com",
        password_hash=hash_password("partner123"),
        role="partner",
        is_active=True,
    )
    db.add(user)
    db.commit()
    print("Created partner: partner@hiremenow.com / partner123")


def seed_all():
    db = SessionLocal()
    try:
        print("Seeding users for testing...")
        create_admin(db)
        create_candidate(db)
        create_employer(db)
        create_partner(db)
        print("Seeding complete.")
        print("\nTest logins:")
        for email, password, role in TEST_USERS:
            print(f"  {role}: {email} / {password}")
        print("\nWARNING: Change passwords before production!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
