# shortener_app/schemas.py

from pydantic import ConfigDict, BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional

class URLBase(BaseModel):
    target_url: str
    custom_key: str = None # Make it optional 

class URL(URLBase):
    is_active: bool
    clicks: int
    model_config = ConfigDict(from_attributes=True)

class URLInfo(URL):
    url: str
    admin_url: str
    secret_key: str
    qr_code: str = Field(None, description="Base64 encoded QR code image for the URL")
    title: str
    favicon_url: str
    # This enhances URL by requiring two additional strings, url and admin_url. 
    # You could also add the two strings url and admin_url to URL. 
    # But by adding url and admin_url to the URLInfo subclass, 
    # you can use the data in your API without storing it in your database.

class URLUser(BaseModel):
    key: str
    secret_key: str
    target_url: HttpUrl
    is_active: bool
    clicks: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_checked: bool
    status: str
    title: Optional[str] = None
    favicon_url: Optional[HttpUrl] = None

    model_config = ConfigDict(
        from_attributes=True
    )

class APIKeyCreate(BaseModel):
    api_key: str
    role_id: int  # เพิ่ม role_id

class APIKeyDelete(BaseModel):
    api_key: str
    

class ScanStatus(BaseModel):
    url: str
    status: Optional[str] = None  # Allow status to be None
    result: str
    scan_type: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
