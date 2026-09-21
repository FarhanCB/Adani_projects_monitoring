from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with email (seamless frictionless access for all developer and team emails)."""
    email = credentials.email.lower().strip()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is required"
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Auto-create user for frictionless login for all developer emails
        raw_name = email.split("@")[0].replace(".", " ").replace("_", " ").title()
        user = User(
            email=email,
            full_name=raw_name,
            hashed_password=get_password_hash(credentials.password or "Adani@12345"),
            role="USER",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not user.is_active:
        user.is_active = True
        db.commit()
        db.refresh(user)

    access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "assigned_project_ids": [p.id for p in user.projects]
        }
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get profile of current authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        assigned_project_ids=[p.id for p in current_user.projects],
        assigned_projects_count=len(current_user.projects)
    )
