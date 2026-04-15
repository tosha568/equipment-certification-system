from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_roles
from ..models import Product, Role, User
from ..schemas import ProductCreate, ProductOut, ProductUpdateByExecutor

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Product).order_by(Product.id.desc())
    if current_user.role == Role.EXECUTOR:
        return query.filter(Product.owner_id == current_user.id).all()
    return query.all()


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    current_user: User = Depends(require_roles(Role.EXECUTOR, Role.SERVICE_MANAGER, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    item = Product(name=payload.name, description=payload.description, owner_id=current_user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdateByExecutor,
    current_user: User = Depends(require_roles(Role.EXECUTOR, Role.SERVICE_MANAGER, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    item = db.query(Product).filter(Product.id == product_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if current_user.role == Role.EXECUTOR and item.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit this product")

    if payload.name is not None:
        item.name = payload.name
    if payload.description is not None:
        item.description = payload.description
    if payload.status is not None:
        item.status = payload.status

    db.commit()
    db.refresh(item)
    return item
