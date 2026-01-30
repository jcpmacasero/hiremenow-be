from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.candidate import Candidate
from app.models.employer import Employer

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id = UUID(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user


def require_roles(allowed_roles: List[str]):
    """Check if user has one of the allowed roles (use lowercase: 'admin', 'employer', etc.)"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


# Convenience dependencies
def get_admin_user(user: User = Depends(require_roles(['admin']))) -> User:
    return user


def get_employer_user(user: User = Depends(require_roles(['admin', 'employer']))) -> User:
    return user


def get_candidate_user(user: User = Depends(require_roles(['admin', 'candidate']))) -> User:
    return user


def get_current_candidate(
    current_user: User = Depends(require_roles(["candidate"])),
    db: Session = Depends(get_db),
) -> Candidate:
    """Require candidate role and return the Candidate record for current user."""
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found",
        )
    return candidate


def get_current_employer(
    current_user: User = Depends(require_roles(["employer"])),
    db: Session = Depends(get_db),
) -> Employer:
    """Require employer role and return the Employer record for current user."""
    employer = db.query(Employer).filter(Employer.user_id == current_user.id).first()
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer profile not found",
        )
    return employer
