import hmac
import hashlib
from fastapi import Header, Query, HTTPException
from .config import MANAGER_PASSWORD


def manager_token(password: str) -> str:
    """Derive a stable session token from the manager password. Because it is derived
    from the password itself, every worker computes the same token and it invalidates
    automatically if the password is changed — no separate secret needed."""
    return hmac.new((password or "").encode("utf-8"), b"smarthire-manager-portal", hashlib.sha256).hexdigest()


# Computed once from the environment-provided password at process start.
_EXPECTED_TOKEN = manager_token(MANAGER_PASSWORD)


def require_manager(x_manager_token: str = Header(default=""), t: str = Query(default="")):
    """Dependency that protects every manager API route. The token may arrive as the
    `X-Manager-Token` header (normal API calls) or a `t` query parameter (file download
    links, which cannot set headers). Rejects anything else with 401."""
    supplied = x_manager_token or t
    if not supplied or not hmac.compare_digest(supplied, _EXPECTED_TOKEN):
        raise HTTPException(status_code=401, detail="Manager authentication required.")
    return True
