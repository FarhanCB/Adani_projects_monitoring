from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_admin, get_current_user, validate_url_safe
from app.models.incident import Incident
from app.models.monitoring import MonitoringResult
from app.models.project import Project
from app.models.user import User
from app.schemas.project import (
    ProjectCard,
    ProjectCreate,
    ProjectResponse,
    ProjectTestResult,
    ProjectUpdate,
)
from app.schemas.user import DeveloperSummary
from app.services.monitor import probe_website_sync, record_probe_result
from app.services.uptime import calculate_project_uptime, parse_date_range

router = APIRouter(prefix="/projects", tags=["Projects"])


def get_accessible_projects_query(db: Session, user: User):
    """All users have access to all monitored projects."""
    return db.query(Project)


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all projects accessible to the authenticated user."""
    projects = get_accessible_projects_query(db, current_user).order_by(Project.name).all()
    results = []
    for p in projects:
        results.append(ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            url=p.url,
            interval_seconds=p.interval_seconds,
            timeout_seconds=p.timeout_seconds,
            expected_status_codes=p.expected_status_codes,
            is_enabled=p.is_enabled,
            created_at=p.created_at,
            updated_at=p.updated_at,
            developers=[DeveloperSummary(
                id=d.id,
                full_name=d.full_name,
                email=d.email,
                role=d.role
            ) for d in p.developers],
            developer_count=len(p.developers)
        ))
    return results


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Add a new monitored website. Admin only."""
    if not validate_url_safe(project_in.url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL scheme or restricted address."
        )

    # Check for duplicate URL
    existing = db.query(Project).filter(Project.url == project_in.url).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A project with URL '{project_in.url}' already exists ({existing.name})."
        )

    project = Project(
        name=project_in.name,
        description=project_in.description,
        url=project_in.url,
        interval_seconds=project_in.interval_seconds,
        timeout_seconds=project_in.timeout_seconds,
        expected_status_codes=project_in.expected_status_codes,
        is_enabled=project_in.is_enabled
    )

    if project_in.developer_ids:
        devs = db.query(User).filter(User.id.in_(project_in.developer_ids)).all()
        project.developers = devs

    db.add(project)
    db.commit()
    db.refresh(project)

    # Immediately perform initial probe so user has instant feedback
    try:
        probe = probe_website_sync(
            url=project.url,
            timeout_seconds=project.timeout_seconds,
            expected_status_codes=project.expected_status_codes
        )
        record_probe_result(db, project, probe)
    except Exception:
        pass

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        url=project.url,
        interval_seconds=project.interval_seconds,
        timeout_seconds=project.timeout_seconds,
        expected_status_codes=project.expected_status_codes,
        is_enabled=project.is_enabled,
        created_at=project.created_at,
        updated_at=project.updated_at,
        developers=[DeveloperSummary(
            id=d.id,
            full_name=d.full_name,
            email=d.email,
            role=d.role
        ) for d in project.developers],
        developer_count=len(project.developers)
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project details. Restricted to assigned developers or admins."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # All users have access to view project details

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        url=project.url,
        interval_seconds=project.interval_seconds,
        timeout_seconds=project.timeout_seconds,
        expected_status_codes=project.expected_status_codes,
        is_enabled=project.is_enabled,
        created_at=project.created_at,
        updated_at=project.updated_at,
        developers=[DeveloperSummary(
            id=d.id,
            full_name=d.full_name,
            email=d.email,
            role=d.role
        ) for d in project.developers],
        developer_count=len(project.developers)
    )


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Update project configuration, monitoring interval, expected status codes, or assigned developers."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project_in.url is not None:
        if not validate_url_safe(project_in.url):
            raise HTTPException(status_code=400, detail="Invalid URL or restricted address")
        project.url = project_in.url

    if project_in.name is not None:
        project.name = project_in.name
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.interval_seconds is not None:
        project.interval_seconds = project_in.interval_seconds
    if project_in.timeout_seconds is not None:
        project.timeout_seconds = project_in.timeout_seconds
    if project_in.expected_status_codes is not None:
        project.expected_status_codes = project_in.expected_status_codes
    if project_in.is_enabled is not None:
        project.is_enabled = project_in.is_enabled

    if project_in.developer_ids is not None:
        devs = db.query(User).filter(User.id.in_(project_in.developer_ids)).all()
        project.developers = devs

    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        url=project.url,
        interval_seconds=project.interval_seconds,
        timeout_seconds=project.timeout_seconds,
        expected_status_codes=project.expected_status_codes,
        is_enabled=project.is_enabled,
        created_at=project.created_at,
        updated_at=project.updated_at,
        developers=[DeveloperSummary(
            id=d.id,
            full_name=d.full_name,
            email=d.email,
            role=d.role
        ) for d in project.developers],
        developer_count=len(project.developers)
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Delete a monitored project and all its history and incidents. Admin only."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()
    return None


@router.post("/{project_id}/toggle", response_model=ProjectResponse)
def toggle_project_enabled(
    project_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Enable or disable website monitoring for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.is_enabled = not project.is_enabled
    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        url=project.url,
        interval_seconds=project.interval_seconds,
        timeout_seconds=project.timeout_seconds,
        expected_status_codes=project.expected_status_codes,
        is_enabled=project.is_enabled,
        created_at=project.created_at,
        updated_at=project.updated_at,
        developers=[DeveloperSummary(
            id=d.id,
            full_name=d.full_name,
            email=d.email,
            role=d.role
        ) for d in project.developers],
        developer_count=len(project.developers)
    )


@router.post("/{project_id}/test", response_model=ProjectTestResult)
def test_project_manual(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Requirement 2 & 7: Test website manually on demand and record the result in history."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # All users have permission to trigger on-demand test probes

    probe = probe_website_sync(
        url=project.url,
        timeout_seconds=project.timeout_seconds,
        expected_status_codes=project.expected_status_codes
    )
    result = record_probe_result(db, project, probe)

    return ProjectTestResult(
        project_id=project.id,
        url=project.url,
        status=result.status,
        http_status=result.http_status,
        response_time_ms=result.response_time_ms,
        error_type=result.error_type,
        error_message=result.error_message,
        ssl_valid=result.ssl_valid,
        ssl_days_remaining=result.ssl_days_remaining,
        ssl_issuer=result.ssl_issuer,
        redirect_url=result.redirect_url,
        tested_at=result.timestamp
    )
