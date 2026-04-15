from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_roles
from ..models import Request, Role, User
from ..schemas import RequestCreate, RequestDecisionUpdate, RequestOut, RequestUpdateByExecutor

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("", response_model=list[RequestOut])
def list_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Request).order_by(Request.id.desc())
    if current_user.role == Role.EXECUTOR:
        return query.filter(Request.owner_id == current_user.id).all()
    return query.all()


@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: RequestCreate,
    current_user: User = Depends(require_roles(Role.EXECUTOR, Role.SERVICE_MANAGER, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    item = Request(title=payload.title, description=payload.description, owner_id=current_user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{request_id}", response_model=RequestOut)
def update_request_by_executor(
    request_id: int,
    payload: RequestUpdateByExecutor,
    current_user: User = Depends(require_roles(Role.EXECUTOR, Role.SERVICE_MANAGER, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    item = db.query(Request).filter(Request.id == request_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if current_user.role == Role.EXECUTOR and item.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit this request")

    if payload.title is not None:
        item.title = payload.title
    if payload.description is not None:
        item.description = payload.description
    if payload.status is not None:
        item.status = payload.status

    db.commit()
    db.refresh(item)
    return item


@router.patch("/{request_id}/first-decision", response_model=RequestOut)
def first_decision(
    request_id: int,
    payload: RequestDecisionUpdate,
    _: User = Depends(require_roles(Role.SERVICE_MANAGER, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    item = db.query(Request).filter(Request.id == request_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    item.first_decision = payload.decision
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{request_id}/second-decision", response_model=RequestOut)
def second_decision(
    request_id: int,
    payload: RequestDecisionUpdate,
    _: User = Depends(require_roles(Role.CENTER_MANAGER, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    item = db.query(Request).filter(Request.id == request_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if not item.first_decision:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="First decision is required")
    item.second_decision = payload.decision
    db.commit()
    db.refresh(item)
    return item
