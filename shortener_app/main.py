# shortener_app/main.py
from typing import Optional
import requests  # Import for checking website existence
import secrets
import validators
from fastapi import Depends, FastAPI, HTTPException, Request, status, Security, Header
from fastapi.security import APIKeyHeader
from fastapi.openapi.models import APIKey, APIKeyIn, SecurityScheme
from fastapi.openapi.utils import get_openapi
from fastapi.encoders import jsonable_encoder
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from sqlalchemy.orm import Session
from starlette.datastructures import URL
from fastapi.responses import JSONResponse
from qrcodegen import QrCode
from PIL import Image
import io
import base64
from urllib.parse import urlparse
import jwt
from datetime import datetime, timedelta, timezone

from .config import get_settings
from .database import SessionLocal, SessionAPI, SessionBlacklist, engine, engine_api, engine_blacklist
from . import crud, models, schemas, keygen


app = FastAPI(root_path="")
templates = Jinja2Templates(directory="shortener_app/templates")

SECRET_KEY = get_settings().secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

models.Base.metadata.create_all(bind=engine)
models.BaseAPI.metadata.create_all(bind=engine_api)
models.BaseBlacklist.metadata.create_all(bind=engine_blacklist)

def get_admin_info(db_url: models.URL) -> schemas.URLInfo:
    base_url = URL(get_settings().base_url)
    admin_endpoint = app.url_path_for(
        "administration info", secret_key=db_url.secret_key
    )
    db_url.url = str(base_url.replace(path=db_url.key))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))
    qr_code_base64 = generate_qr_code(db_url.url)
    
    # ต้องดู Model ด้วย
    response = {
        'target_url': db_url.target_url,
        'is_active': db_url.is_active,
        'clicks': db_url.clicks,
        'url': db_url.url,
        'admin_url': db_url.admin_url,
        'qr_code': f"data:image/png;base64,{qr_code_base64}"
    }
    return JSONResponse(content=response, status_code=200)
    # return db_url
    

def raise_not_found(request):
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)

def raise_forbidden(message):
    raise HTTPException(status_code=403, detail=message)

def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)

def raise_already_used(message):
    raise HTTPException(status_code=400, detail=message)

def raise_not_reachable(message):
    raise HTTPException(status_code=504, detail=message)

def raise_api_key(api_key: str):
    message = f"API key '{api_key}' is missing or invalid"
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)

def normalize_url(url: str, trailing_slash: bool = False) -> str:
    """Normalizes a URL by optionally adding or removing trailing slashes.

    Args:
        url: The URL to normalize.
        trailing_slash: Whether to ensure a trailing slash (True) or remove it (False).

    Returns:
        The normalized URL.
    """
    # Strip leading and trailing whitespace from the URL
    url = url.strip()

    parsed_url = urlparse(url)
    path = parsed_url.path.rstrip("/")  # Remove all trailing slashes from the path
    
    if trailing_slash:
        path += "/"  # Add a single trailing slash if requested

    return parsed_url._replace(path=path).geturl()

# ฐานข้อมูลหลัก main database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ฟังก์ชันสำหรับการเชื่อมต่อกับฐานข้อมูล API keys
def get_api_db():
    db = SessionAPI()
    try:
        yield db
    finally:
        db.close()

def get_blacklist_db():
    db = SessionBlacklist()
    try:
        yield db
    finally:
        db.close()

def get_optional_api_db():
    if get_settings().use_api_db:
        return next(get_api_db())
    return None

def verify_jwt_token(authorization: str = Header(None)):
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload["sub"] != "user_management":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token subject",
            )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
        )
    
def create_access_token():
    now = datetime.now(timezone.utc)
    payload = {
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now,
        "sub": "user_management"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
api_key_header = APIKeyHeader(name="X-API-KEY")

# Updated API key verification function
async def verify_api_key(
    request: Request, db: Session = Depends(get_api_db)
):
    api_key = request.headers.get("X-API-KEY")  # Get API key from headers
    if not api_key:
        raise_api_key(api_key) 

    db_api_key = crud.get_api_key(db, api_key)
    if not db_api_key:
        raise_api_key(api_key)
    else:
        return api_key

def generate_qr_code(data):
    qr = QrCode.encode_text(data, QrCode.Ecc.MEDIUM)
    size = qr.get_size()
    scale = 5
    img_size = size * scale
    img = Image.new('1', (img_size, img_size), 'white')

    for y in range(size):
        for x in range(size):
            if qr.get_module(x, y):
                for dy in range(scale):
                    for dx in range(scale):
                        img.putpixel((x * scale + dx, y * scale + dy), 0)

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

@app.get("/")
def read_root():
    return "Welcome to the URL shortener API :)"

@app.get("/about", response_class=HTMLResponse)
async def read_about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "title": "About Page"})


@app.post("/api/register_api_key", tags=["register api key"])
def register_api_key(api_key: schemas.APIKeyCreate, db: Session = Depends(get_api_db), _: str = Depends(verify_jwt_token)):
    result = crud.register_api_key(db, api_key.api_key, api_key.role_id)
    return JSONResponse(content={"message": result["message"]}, status_code=result["status_code"])


@app.post("/api/refresh_token", tags=["register api key"])
def refresh_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload["sub"] != "user_management":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token subject",
            )
        new_access_token = create_access_token()
        return {"access_token": new_access_token}
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired refresh token",
        )

@app.get("/{url_key}")
def forward_to_target_url(
        url_key: str,
        request: Request,
        db: Session = Depends(get_db)
    ):
    
    if db_url := crud.get_db_url_by_key(db=db, url_key=url_key):
        # Check if target URL exists
        try:
            # https://www.tutorialspoint.com/how-to-check-whether-user-s-internet-is-on-or-off-using-python
            response = requests.head(db_url.target_url, timeout=10)
            # เพิ่มการ click +1
            crud.update_db_clicks(db=db, db_url=db_url)
            return RedirectResponse(db_url.target_url)  # ไปยัง url ปลายทาง
            #if response.status_code >= 400:  # Check for client or server errors
            #    raise_not_reachable(message=f"The target URL '{db_url.target_url}' is not reachable.")
        except requests.ConnectionError:
            raise_not_reachable(message=f"The target URL '{db_url.target_url}' does not seem to be reachable.")
        except requests.RequestException: # Catch all request exceptions
            raise_not_reachable(message=f"The target URL '{db_url.target_url}' does not seem to be reachable.")

    else:
        raise_not_found(request)

    # The := operator is colloquially known as the walrus operator and gives you a new syntax for assigning variables in the middle of expressions.
    # If db_url is a database entry, then you return your RedirectResponse to target_url. Otherwise, you call raise_not_found()


@app.post("/url", response_model=schemas.URLInfo, tags=["url"]) # , dependencies=[Security(verify_api_key)]
def create_url(
    url: schemas.URLBase,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
    api_db: Optional[Session] = Depends(get_optional_api_db),
    blacklist_db: Session = Depends(get_blacklist_db)
):
    url.target_url = normalize_url(url.target_url, trailing_slash=False)

    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    # ตรวจสอบว่า URL อยู่ใน blacklist หรือไม่
    if crud.is_url_in_blacklist(blacklist_db, url.target_url):
        raise_forbidden(message="The provided URL is blacklisted and cannot be shortened.")
    
    # ดึง role_id จาก database ถ้ามีการกำหนดให้ใช้งาน
    role_id = None
    if api_db:
        role_id = crud.get_role_id(api_db, api_key)
        if role_id is None:
            raise HTTPException(status_code=400, detail="Invalid API key")
        
        # ดึง role_name จากฐานข้อมูล Role
        role_name = crud.get_role_name(api_db, role_id)
        if role_name is None:
            raise HTTPException(status_code=400, detail="Role not found")
        
    
    # role_id = crud.get_role_id(api_db, api_key)
    # ได้ role_id มาก็ขึ้นอยู่กับว่าจะเอาไปใช้ทำอะไรต่อ
    
    if url.custom_key:
        if role_id is not None and role_id not in [2, 3]:
            raise_forbidden(message="You do not have permission to use custom keys")
            
        
        if not keygen.is_valid_custom_key(url.custom_key):
            raise_bad_request(message="Your provided custom key is not valid. It should only contain letters and digits.")
        if len(url.custom_key) > 15:
            raise_bad_request(message="Your provided custom key is too long. It should not exceed 15 characters.")
        if crud.get_db_url_by_customkey(db, url.custom_key):
            raise_already_used(message=f"The custom key '{url.custom_key}' is already in use. Please choose a different key.")
    
    # ตรวจสอบว่ามี  URL Target นี้อยู่แล้วหรือไม่สำหรับ API key นี้
    # ต้องทำเพิ่มกรณีที่มีการ custom key shorten url ให้มีการซ้ำได้ แต่ custom key ต้องไม่ซ้ำ
    
    existing_url = crud.is_url_existing_for_key(db, url.target_url, api_key)
    if existing_url:
        base_url = get_settings().base_url
        # qr_code_base64 = generate_qr_code(f"{base_url}/{existing_url.key}")
        url_data = {
            "target_url": existing_url.target_url,
            "is_active": existing_url.is_active,
            "clicks": existing_url.clicks,
            "url": f"{base_url}/{existing_url.key}", 
            "admin_url": f"{base_url}/{existing_url.secret_key}",
            # "qr_code": f"data:image/png;base64,{qr_code_base64}",
            "message": f"A short link for this website already exists."
        }
        return JSONResponse(content=url_data, status_code=409) 

    db_url = crud.create_db_url(db=db, url=url, api_key=api_key)
    return get_admin_info(db_url)

@app.get("/user/info", tags=["info"])
async def get_url_count(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    # Query the count of URLs created with the given API key
    url_count = db.query(models.URL).filter(models.URL.api_key == api_key, models.URL.is_active == 1).count()

    # Return the count as a JSON response
    return JSONResponse(content={"url_count": url_count}, status_code=200)

@app.get("/user/urls", tags=["user urls"])
async def get_user_url(
    api_key: str = Depends(verify_api_key), 
    db: Session = Depends(get_db)
):
    user_urls = db.query(models.URL).filter(models.URL.api_key == api_key, models.URL.is_active == 1).all()
    user_urls_json = jsonable_encoder(user_urls)
    return JSONResponse(content=user_urls_json, status_code=200)

@app.get(
    "/admin/{secret_key}",
    name="administration info",
    response_model=schemas.URLInfo,
    tags=["admin"],
)  # Removed Security dependency
def get_url_info(
    secret_key: str,
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)  # Added api_key dependency
):
    if db_url := crud.get_db_url_by_secret_key(db, secret_key=secret_key):
        return get_admin_info(db_url)
    else:
        raise_not_found(request)


@app.delete("/admin/{secret_key}", tags=["admin"])  # Removed Depends dependency
def delete_url(
    secret_key: str,
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)  # Added api_key dependency
):
    if db_url := crud.deactivate_db_url_by_secret_key(db, secret_key=secret_key):
        message = f"Successfully deleted shortened URL for '{db_url.target_url}'"
        return {"detail": message}
    else:
        raise_not_found(request)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="URL Shortener API",
        version="1.0.0",
        description="API for shortening URLs and managing shortened URLs",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-KEY",
        }
    }
    openapi_schema["security"] = [{"ApiKeyAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, get_settings().host, port=get_settings().port)