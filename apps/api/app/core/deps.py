"""Gemeinsame Dependencies (z. B. optionaler API-Key)."""
from typing import Optional

from fastapi import Header, HTTPException

from app.core.config import settings


async def require_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Wenn API_KEY in .env gesetzt ist, muss X-API-Key Header übereinstimmen."""
    if not settings.API_KEY:
        return
    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Ungültiger oder fehlender X-API-Key")
    return x_api_key
