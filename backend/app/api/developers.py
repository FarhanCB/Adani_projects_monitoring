from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_admin, get_password_hash
from app.models.project import Project
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/developers", tags=["Developers & Users"])


@router.get("", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """List all registered users/developers. Admin only."""
    users = db.query(User).order_by(User.full_name).all()
    results = []
    for u in users:
        results.append(UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
            assigned_project_ids=[p.id for p in u.projects],
            assigned_projects_count=len(u.projects)
        ))
    return results


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Add a new developer/user. Admin only. Assign to one or multiple projects with no limit."""
    email_clean = user_in.email.lower().strip()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{email_clean}' already exists."
        )

    user = User(
        email=email_clean,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role.upper(),
        is_active=user_in.is_active
    )

    if user_in.project_ids:
        projects = db.query(Project).filter(Project.id.in_(user_in.project_ids)).all()
        user.projects = projects

    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        assigned_project_ids=[p.id for p in user.projects],
        assigned_projects_count=len(user.projects)
    )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Update user profile, role, password, or project assignments."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.email is not None:
        email_clean = user_in.email.lower().strip()
        conflict = db.query(User).filter(User.email == email_clean, User.id != user_id).first()
        if conflict:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = email_clean
    if user_in.password:
        user.hashed_password = get_password_hash(user_in.password)
    if user_in.role is not None:
        user.role = user_in.role.upper()
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.project_ids is not None:
        projects = db.query(Project).filter(Project.id.in_(user_in.project_ids)).all()
        user.projects = projects

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        assigned_project_ids=[p.id for p in user.projects],
        assigned_projects_count=len(user.projects)
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Delete a user. Admin cannot delete themselves."""
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own administrative account")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return None
