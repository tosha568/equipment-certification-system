import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from starlette.middleware.sessions import SessionMiddleware

from .core_config import get_settings
from .db import Base, SessionLocal, engine
from .models import Role, User
from .routers import admin, auth, products, requests, users, web
from .security import get_password_hash

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.mount("/static", StaticFiles(directory="fastapi_app/static"), name="static")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin_count = db.query(func.count(User.id)).filter(User.role == Role.ADMIN).scalar() or 0
        if admin_count == 0:
            admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@sec.local")
            admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin123!")
            admin_name = os.getenv("DEFAULT_ADMIN_NAME", "System Administrator")

            existing = db.query(User).filter(User.email == admin_email).first()
            if not existing:
                db.add(
                    User(
                        full_name=admin_name,
                        email=admin_email,
                        password_hash=get_password_hash(admin_password),
                        role=Role.ADMIN,
                    )
                )
                db.commit()
    finally:
        db.close()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "secDB FastAPI is running"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(requests.router)
app.include_router(products.router)
app.include_router(admin.router)
app.include_router(web.router)
