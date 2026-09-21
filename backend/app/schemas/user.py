from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = Field(default="USER", pattern="^(ADMIN|USER)$")
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=6)
    project_ids: List[int] = []


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=6)
    role: Optional[str] = Field(default=None, pattern="^(ADMIN|USER)$")
    is_active: Optional[bool] = None
    project_ids: Optional[List[int]] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    assigned_project_ids: List[int] = []
    assigned_projects_count: int = 0

    class Config:
        from_attributes = True


class DeveloperSummary(BaseModel):
    id: int
    full_name: str
    email: str
    role: str

    class Config:
        from_attributes = True
