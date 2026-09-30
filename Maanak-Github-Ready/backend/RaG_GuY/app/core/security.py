from fastapi import Header, HTTPException

def verify_user_role(x_user_role: str = Header(default=None, description="Required role header ('user' or 'manufacturer')")):
    """
    Gateway Security Dependency (The Bouncer).
    Ensures the X-User-Role header is present and authorized.
    """
    if not x_user_role:
        raise HTTPException(
            status_code=400,
            detail={"error": "MISSING_HEADER", "message": "Missing required 'X-User-Role' header."}
        )
    role = x_user_role.lower().strip()
    if role not in ["user", "manufacturer"]:
        raise HTTPException(
            status_code=403,
            detail={"error": "INSUFFICIENT_CLEARANCE", "message": f"Role '{role}' is not authorized."}
        )
    return role
