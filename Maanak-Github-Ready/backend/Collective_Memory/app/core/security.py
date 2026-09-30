from fastapi import Header, HTTPException

def verify_user_role(x_user_role: str = Header(default=None)):
    """
    Gateway Security Dependency (The Bouncer).
    Ensures the X-User-Role header is present and valid.
    """
    if not x_user_role:
        raise HTTPException(status_code=400, detail="Missing X-User-Role header")
    role = x_user_role.lower()
    if role not in ["user", "manufacturer"]:
        raise HTTPException(status_code=403, detail="INSUFFICIENT_CLEARANCE")
    return role
