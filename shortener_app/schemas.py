# shortener_app/schemas.py

from pydantic import ConfigDict, BaseModel

class URLBase(BaseModel):
    target_url: str

class URL(URLBase):
    is_active: bool
    clicks: int
    model_config = ConfigDict(from_attributes=True)

class URLInfo(URL):
    url: str
    admin_url: str
    # This enhances URL by requiring two additional strings, url and admin_url. 
    # You could also add the two strings url and admin_url to URL. 
    # But by adding url and admin_url to the URLInfo subclass, 
    # you can use the data in your API without storing it in your database.
