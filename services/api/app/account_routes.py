from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .accounts import AccountRepository, account_repository
from .auth import Role, issue_token, require_roles

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])
Store = Annotated[AccountRepository, Depends(account_repository)]
Administrator = Annotated[dict, Depends(require_roles(Role.ADMIN))]


class Login(BaseModel):
    username: str = Field(pattern=r"^[A-Za-z0-9_.@-]{3,100}$")
    password: str = Field(min_length=1,max_length=1024)


class CreateAccount(Login):
    password: str = Field(min_length=12,max_length=1024)
    role: Role = Role.READER


class ChangeAccount(BaseModel):
    role: Role | None = None
    active: bool | None = None
    password: str | None = Field(default=None,min_length=12,max_length=1024)


@router.post("/login")
def login(item: Login, store: Store):
    account = store.authenticate(item.username,item.password)
    if account is None:
        raise HTTPException(401,"Invalid credentials")
    token = issue_token(account["username"],Role(account["role"]),account_id=account["id"],session_version=account["version"])
    return {"access_token":token,"token_type":"bearer","expires_in":3600,"account":account}


@router.get("")
def accounts(store: Store, actor: Administrator):
    return store.list()


@router.post("")
def create(item: CreateAccount, store: Store, actor: Administrator):
    try:
        return store.create(item.username,item.role,item.password,actor=actor["sub"])
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc


@router.patch("/{account_id}")
def change(account_id: str, item: ChangeAccount, store: Store, actor: Administrator):
    if item.role is None and item.active is None and item.password is None:
        raise HTTPException(422,"Specify a role, active state or password reset")
    try:
        return store.change(account_id,actor=actor["sub"],role=item.role,active=item.active,password=item.password)
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc


@router.get("/audit")
def audit(store: Store, actor: Administrator):
    return store.audit_records()


@router.post("/logout")
def logout(store: Store, actor: Annotated[dict, Depends(require_roles(*Role))]):
    if not actor.get("account_id"):
        raise HTTPException(409, "Legacy tokens cannot be revoked through account logout")
    store.change(actor["account_id"],actor=actor["sub"])
    return {"revoked":True}
