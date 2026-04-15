from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from .models import ProductStatus, RequestStatus, Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=64)
    role: Role = Role.EXECUTOR


class SelfRegister(UserBase):
    password: str = Field(min_length=6, max_length=64)


class UserOut(UserBase):
    id: int
    role: Role
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    role: Role


class RequestBase(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str = Field(default="", max_length=5000)


class RequestCreate(RequestBase):
    pass


class RequestUpdateByExecutor(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    status: RequestStatus | None = None


class RequestDecisionUpdate(BaseModel):
    decision: str = Field(min_length=2, max_length=255)


class RequestOut(RequestBase):
    id: int
    status: RequestStatus
    first_decision: str | None
    second_decision: str | None
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str = Field(default="", max_length=5000)


class ProductCreate(ProductBase):
    pass


class ProductUpdateByExecutor(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    status: ProductStatus | None = None


class ProductOut(ProductBase):
    id: int
    status: ProductStatus
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DictionaryItemBase(BaseModel):
    category: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1, max_length=255)
    is_active: bool = True


class DictionaryItemCreate(DictionaryItemBase):
    pass


class DictionaryItemOut(DictionaryItemBase):
    id: int

    class Config:
        from_attributes = True


class AppSettingBase(BaseModel):
    key: str = Field(min_length=2, max_length=120)
    value: str = Field(min_length=1, max_length=255)


class AppSettingCreate(AppSettingBase):
    pass


class AppSettingOut(AppSettingBase):
    id: int

    class Config:
        from_attributes = True
