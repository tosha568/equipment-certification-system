from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_roles
from ..models import AppSetting, DictionaryItem, Role, User
from ..schemas import (
    AppSettingCreate,
    AppSettingOut,
    DictionaryItemCreate,
    DictionaryItemOut,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dictionary", response_model=list[DictionaryItemOut])
def list_dictionary(
    _: User = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    return db.query(DictionaryItem).order_by(DictionaryItem.id.desc()).all()


@router.post("/dictionary", response_model=DictionaryItemOut, status_code=status.HTTP_201_CREATED)
def create_dictionary_item(
    payload: DictionaryItemCreate,
    _: User = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    item = DictionaryItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/settings", response_model=list[AppSettingOut])
def list_settings(
    _: User = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    return db.query(AppSetting).order_by(AppSetting.id.desc()).all()


@router.post("/settings", response_model=AppSettingOut, status_code=status.HTTP_201_CREATED)
def upsert_setting(
    payload: AppSettingCreate,
    _: User = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    setting = db.query(AppSetting).filter(AppSetting.key == payload.key).first()
    if setting:
        setting.value = payload.value
        db.commit()
        db.refresh(setting)
        return setting

    setting = AppSetting(**payload.model_dump())
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting
