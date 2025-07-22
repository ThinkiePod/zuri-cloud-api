from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Optional

async def verify_internal_access(x_internal_key: Optional[str] = Header(None)):
    if x_internal_key != "your-internal-secret":
        raise HTTPException(status_code=403, detail="Internal access required")

router = APIRouter(
    prefix="/internal",
    tags=["Internal API - Restricted"],
    dependencies=[Depends(verify_internal_access)],
)

@router.post("/devices/factory-reset")
async def factory_reset_device(device_id: str):
    """Internal-only factory reset endpoint"""
    pass