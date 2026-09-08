"""Manager authentication: bcrypt password hashing and signed session tokens.

Passwords are stored only as bcrypt hashes. A successful login returns a token that is
signed with SECRET_KEY and carries its own expiry, so it can be verified without a
server-side session store while still being revocable by deactivating the account.
"""
import hmac
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, Header, Query, HTTPException, Request
from sqlalchemy.orm import Session

from .config import SECRET_KEY, TOKEN_TTL_SECONDS, MANAGER_EMAIL, MANAGER_PASSWORD
from .database import get_db
from .models import Manager, AuditLog


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------
def _prepare(password: str) -> bytes:
    """bcrypt only considers the first 72 bytes of input. Longer passwords are hashed
    with SHA-256 first so every character contributes, instead of being truncated."""
    raw = (password or "").encode("utf-8")
    if len(raw) > 72:
        raw = base64.b64encode(hashlib.sha256(raw).digest())
    return raw


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(_prepare(password), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------
def _sign(payload: str) -> str:
    return hmac.new(SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def create_token(manager, ttl_seconds: int = TOKEN_TTL_SECONDS) -> str:
    """Token format: <manager_id>.<unix_expiry>.<signature>"""
    expires_at = int((datetime.utcnow() + timedelta(seconds=ttl_seconds)).timestamp())
    payload = f"{manager.id}.{expires_at}"
    return f"{payload}.{_sign(payload)}"


def verify_token(token: str) -> Optional[str]:
    """Return the manager id if the token is authentic and unexpired, else None."""
    if not token or token.count(".") != 2:
        return None
    manager_id, expires_at, signature = token.split(".")
    if not hmac.compare_digest(signature, _sign(f"{manager_id}.{expires_at}")):
        return None
    try:
        if int(expires_at) < int(datetime.utcnow().timestamp()):
            return None
    except ValueError:
        return None
    return manager_id


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------
def require_manager(
    x_manager_token: str = Header(default=""),
    t: str = Query(default=""),
    db: Session = Depends(get_db),
) -> Manager:
    """Protects every manager route. The token arrives either as the `X-Manager-Token`
    header (API calls) or a `t` query parameter (download links, which cannot set
    headers). Deactivated accounts are rejected even with a still-valid token."""
    manager_id = verify_token(x_manager_token or t)
    if not manager_id:
        raise HTTPException(status_code=401, detail="Manager authentication required.")
    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager or not manager.is_active:
        raise HTTPException(status_code=401, detail="Manager account is inactive or no longer exists.")
    return manager


def require_admin(manager: Manager = Depends(require_manager)) -> Manager:
    if not manager.is_admin:
        raise HTTPException(status_code=403, detail="This action requires an administrator account.")
    return manager


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------
def record_audit(db: Session, manager, action: str,
                 target_type: str = None, target_id: str = None,
                 details: str = None, request: Request = None) -> None:
    """Append an audit entry. Never raises: an auditing failure must not break the
    action the manager was performing."""
    try:
        ip = None
        if request is not None and request.client:
            ip = request.headers.get("x-forwarded-for", request.client.host).split(",")[0].strip()
        db.add(AuditLog(
            manager_id=manager.id if manager else None,
            manager_email=manager.email if manager else None,
            action=action, target_type=target_type, target_id=target_id,
            details=details, ip_address=ip,
        ))
        db.commit()
    except Exception:
        db.rollback()


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
def bootstrap_admin(db: Session) -> Optional[str]:
    """Create the first administrator from MANAGER_EMAIL / MANAGER_PASSWORD when no
    manager accounts exist, so a fresh deployment can be signed into immediately.
    Returns a message when an account was created, else None."""
    if db.query(Manager).count() > 0:
        return None
    admin = Manager(
        email=MANAGER_EMAIL,
        full_name="Administrator",
        password_hash=hash_password(MANAGER_PASSWORD),
        role="admin",
        is_active=True,
        must_change_password=(MANAGER_PASSWORD == "admin123"),
    )
    db.add(admin)
    db.commit()
    return f"Created bootstrap admin account: {MANAGER_EMAIL}"
