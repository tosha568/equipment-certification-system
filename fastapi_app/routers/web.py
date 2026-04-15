from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AppSetting, DictionaryItem, Product, Request as WorkRequest, Role, User
from ..security import get_password_hash, verify_password

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="fastapi_app/templates")


def _current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()


def _require_user(request: Request, db: Session) -> User:
    user = _current_user(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def _role_label(role: Role) -> str:
    labels = {
        Role.EXECUTOR: "Исполнитель",
        Role.SERVICE_MANAGER: "Руководитель службы",
        Role.CENTER_MANAGER: "Руководитель центра",
        Role.ADMIN: "Администратор",
    }
    return labels.get(role, role.value)


@router.get("/")
def index() -> RedirectResponse:
    return RedirectResponse(url="/web/dashboard", status_code=status.HTTP_302_FOUND)


@router.get("/web/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/web/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Неверный email или пароль"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    request.session["user_id"] = user.id
    return RedirectResponse(url="/web/dashboard", status_code=status.HTTP_302_FOUND)


@router.get("/web/register")
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"error": None})


@router.post("/web/register")
def register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if len(password) < 6:
        return templates.TemplateResponse(
            request,
            "register.html",
            {"error": "Пароль должен быть не менее 6 символов"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    exists = db.query(User).filter(User.email == email).first()
    if exists:
        return templates.TemplateResponse(
            request,
            "register.html",
            {"error": "Пользователь с таким email уже существует"},
            status_code=status.HTTP_409_CONFLICT,
        )

    user = User(
        full_name=full_name,
        email=email,
        password_hash=get_password_hash(password),
        role=Role.EXECUTOR,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id
    return RedirectResponse(url="/web/dashboard", status_code=status.HTTP_302_FOUND)


@router.post("/web/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)


@router.get("/web/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)

    requests_q = db.query(WorkRequest)
    products_q = db.query(Product)

    if user.role == Role.EXECUTOR:
        requests_q = requests_q.filter(WorkRequest.owner_id == user.id)
        products_q = products_q.filter(Product.owner_id == user.id)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "role_label": _role_label(user.role),
            "requests_count": requests_q.count(),
            "products_count": products_q.count(),
            "users_count": db.query(User).count(),
            "dict_count": db.query(DictionaryItem).count(),
        },
    )


@router.get("/web/requests")
def requests_page(request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    query = db.query(WorkRequest).order_by(WorkRequest.id.desc())
    if user.role == Role.EXECUTOR:
        query = query.filter(WorkRequest.owner_id == user.id)

    return templates.TemplateResponse(
        request,
        "requests.html",
        {"user": user, "items": query.all(), "Role": Role, "role_label": _role_label(user.role)},
    )


@router.post("/web/requests")
def create_request(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _require_user(request, db)
    if user.role not in {Role.EXECUTOR, Role.SERVICE_MANAGER, Role.ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    item = WorkRequest(title=title, description=description, owner_id=user.id)
    db.add(item)
    db.commit()
    return RedirectResponse(url="/web/requests", status_code=status.HTTP_302_FOUND)


@router.post("/web/requests/{item_id}/update")
def update_request(
    item_id: int,
    request: Request,
    title: str = Form(""),
    description: str = Form(""),
    status_value: str = Form(""),
    first_decision: str = Form(""),
    second_decision: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _require_user(request, db)
    item = db.query(WorkRequest).filter(WorkRequest.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if user.role == Role.EXECUTOR and item.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if user.role in {Role.EXECUTOR, Role.SERVICE_MANAGER, Role.ADMIN}:
        if title.strip():
            item.title = title.strip()
        item.description = description
        if status_value:
            item.status = status_value

    if user.role in {Role.SERVICE_MANAGER, Role.ADMIN} and first_decision.strip():
        item.first_decision = first_decision.strip()

    if user.role in {Role.CENTER_MANAGER, Role.ADMIN} and second_decision.strip() and item.first_decision:
        item.second_decision = second_decision.strip()

    db.commit()
    return RedirectResponse(url="/web/requests", status_code=status.HTTP_302_FOUND)


@router.get("/web/products")
def products_page(request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    query = db.query(Product).order_by(Product.id.desc())
    if user.role == Role.EXECUTOR:
        query = query.filter(Product.owner_id == user.id)

    return templates.TemplateResponse(
        request,
        "products.html",
        {"user": user, "items": query.all(), "Role": Role, "role_label": _role_label(user.role)},
    )


@router.post("/web/products")
def create_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _require_user(request, db)
    if user.role not in {Role.EXECUTOR, Role.SERVICE_MANAGER, Role.ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    item = Product(name=name, description=description, owner_id=user.id)
    db.add(item)
    db.commit()
    return RedirectResponse(url="/web/products", status_code=status.HTTP_302_FOUND)


@router.post("/web/products/{item_id}/update")
def update_product(
    item_id: int,
    request: Request,
    name: str = Form(""),
    description: str = Form(""),
    status_value: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _require_user(request, db)
    item = db.query(Product).filter(Product.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if user.role == Role.EXECUTOR and item.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if user.role not in {Role.EXECUTOR, Role.SERVICE_MANAGER, Role.ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if name.strip():
        item.name = name.strip()
    item.description = description
    if status_value:
        item.status = status_value

    db.commit()
    return RedirectResponse(url="/web/products", status_code=status.HTTP_302_FOUND)


@router.get("/web/users")
def users_page(request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    users = db.query(User).order_by(User.id.asc()).all()
    return templates.TemplateResponse(
        request,
        "users.html",
        {"user": user, "items": users, "Role": Role, "role_label": _role_label(user.role)},
    )


@router.post("/web/users")
def create_user_by_admin(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _require_user(request, db)
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if db.query(User).filter(User.email == email).first():
        return RedirectResponse(url="/web/users", status_code=status.HTTP_302_FOUND)

    item = User(
        full_name=full_name,
        email=email,
        password_hash=get_password_hash(password),
        role=Role(role),
    )
    db.add(item)
    db.commit()
    return RedirectResponse(url="/web/users", status_code=status.HTTP_302_FOUND)


@router.post("/web/users/{user_id}/role")
def change_user_role(
    user_id: int,
    request: Request,
    role: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _require_user(request, db)
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    item = db.query(User).filter(User.id == user_id).first()
    if item:
        item.role = Role(role)
        db.commit()
    return RedirectResponse(url="/web/users", status_code=status.HTTP_302_FOUND)


@router.get("/web/admin")
def admin_page(request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    dictionaries = db.query(DictionaryItem).order_by(DictionaryItem.id.desc()).all()
    settings = db.query(AppSetting).order_by(AppSetting.id.desc()).all()

    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "user": user,
            "dictionaries": dictionaries,
            "settings": settings,
            "role_label": _role_label(user.role),
        },
    )


@router.post("/web/admin/dictionary")
def create_dictionary_item(
    request: Request,
    category: str = Form(...),
    code: str = Form(...),
    value: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _require_user(request, db)
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    db.add(DictionaryItem(category=category, code=code, value=value, is_active=True))
    db.commit()
    return RedirectResponse(url="/web/admin", status_code=status.HTTP_302_FOUND)


@router.post("/web/admin/settings")
def upsert_setting(
    request: Request,
    key: str = Form(...),
    value: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _require_user(request, db)
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    item = db.query(AppSetting).filter(AppSetting.key == key).first()
    if item:
        item.value = value
    else:
        db.add(AppSetting(key=key, value=value))
    db.commit()

    return RedirectResponse(url="/web/admin", status_code=status.HTTP_302_FOUND)
