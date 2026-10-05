import pytest
from fastapi import HTTPException

from app.accounts import AccountRepository, account_repository
from app.auth import Role, verify_token


def test_bootstrap_persistence_passwords_and_last_admin(tmp_path):
    store = AccountRepository(tmp_path / "accounts.sqlite3")
    owner = store.create("Owner",Role.ADMIN,"Strong password fixture!",actor="bootstrap",bootstrap=True)
    assert store.authenticate("owner","wrong password") is None
    assert AccountRepository(store.path).authenticate("OWNER","Strong password fixture!")["id"] == owner["id"]
    with pytest.raises(ValueError,match="empty"):
        store.create("second",Role.ADMIN,"Strong password fixture!",actor="bootstrap",bootstrap=True)
    with pytest.raises(ValueError,match="last active"):
        store.change(owner["id"],actor="owner",active=False)
    assert "password" not in str(store.audit_records())
    unusual = store.create("dummy",Role.READER,"invalid-password",actor="owner")
    assert store.authenticate("dummy","x") is None
    assert store.authenticate("dummy","invalid-password")["id"] == unusual["id"]


def test_login_role_change_password_reset_revokes_sessions_and_audits(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient

    import app.accounts as module
    from app.main import app

    store = AccountRepository(tmp_path / "accounts.sqlite3")
    store.create("owner",Role.ADMIN,"Strong password fixture!",actor="bootstrap",bootstrap=True)
    app.dependency_overrides[account_repository] = lambda: store
    monkeypatch.setattr(module,"account_repository",lambda:store)
    try:
        with TestClient(app) as client:
            login = client.post("/api/v1/accounts/login",json={"username":"owner","password":"Strong password fixture!"})
            assert login.status_code == 200
            owner = {"Authorization":"Bearer "+login.json()["access_token"]}
            created = client.post("/api/v1/accounts",headers=owner,json={"username":"reader","password":"Reader password fixture!","role":"reader"})
            assert created.status_code == 200
            identifier = created.json()["id"]
            session = client.post("/api/v1/accounts/login",json={"username":"reader","password":"Reader password fixture!"}).json()["access_token"]
            assert verify_token(session)["role"] == "reader"
            assert client.get("/api/v1/accounts",headers={"Authorization":"Bearer "+session}).status_code == 403
            assert client.patch(f"/api/v1/accounts/{identifier}",headers=owner,json={"role":"researcher"}).status_code == 200
            with pytest.raises(HTTPException):
                verify_token(session)
            second = client.post("/api/v1/accounts/login",json={"username":"reader","password":"Reader password fixture!"}).json()["access_token"]
            assert client.patch(f"/api/v1/accounts/{identifier}",headers=owner,json={"password":"New reader password!"}).status_code == 200
            with pytest.raises(HTTPException):
                verify_token(second)
            assert client.post("/api/v1/accounts/login",json={"username":"reader","password":"Reader password fixture!"}).status_code == 401
            assert client.patch(f"/api/v1/accounts/{identifier}",headers=owner,json={"active":False}).status_code == 200
            assert client.post("/api/v1/accounts/login",json={"username":"reader","password":"New reader password!"}).status_code == 401
            assert any(row["action"]=="password-reset" for row in client.get("/api/v1/accounts/audit",headers=owner).json())
    finally:
        app.dependency_overrides.pop(account_repository,None)
