# shortener_app/main.py
from typing import Optional
import requests  # Import for checking website existence
import secrets
import validators
from fastapi import Depends, FastAPI, HTTPException, Request, status, Security, Header, BackgroundTasks, WebSocket
from fastapi.security import APIKeyHeader
from fastapi.openapi.models import APIKey, APIKeyIn, SecurityScheme
from fastapi.openapi.utils import get_openapi
from fastapi.encoders import jsonable_encoder
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from sqlalchemy.orm import Session
from starlette.datastructures import URL
from fastapi.responses import JSONResponse
from qrcodegen import QrCode
from PIL import Image
import io
import base64
from urllib.parse import urlparse, urljoin
import jwt
from datetime import datetime, timedelta, timezone
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import time 
import json
from typing import List
import sys
import os
import socket
from ipaddress import ip_network, ip_address, IPv6Address, IPv4Address

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_settings
from database import SessionLocal, SessionAPI, SessionBlacklist, engine, engine_api, engine_blacklist
from . import crud, models, schemas, keygen
from phishing import phishing_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Fetch phishing URLs
    phishing_data.fetch_phishing_urls()  # เรียกใช้งาน fetch_phishing_urls จากอินสแตนซ์ของ PhishingData
    yield
    # Shutdown: Any cleanup code would go here (ถ้ามี)

app = FastAPI(root_path="", lifespan=lifespan)
templates = Jinja2Templates(directory="shortener_app/templates")

INTERNAL_IP_RANGES = [
    # IPv4 private address ranges
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
    
    # IPv6 private address ranges
    ip_network("fc00::/7"),  # Unique Local Addresses (ULA)
    ip_network("fe80::/10"), # Link-Local Addresses
]

SECRET_KEY = get_settings().secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

models.Base.metadata.create_all(bind=engine)
models.BaseAPI.metadata.create_all(bind=engine_api)
models.BaseBlacklist.metadata.create_all(bind=engine_blacklist)

def is_internal_url(url):
    hostname = urlparse(url).hostname
    try:
        addr_info = socket.getaddrinfo(hostname, None)  # Resolves both IPv4 and IPv6
        for addr in addr_info:
            ip = ip_address(addr[4][0])
            if any(ip in network for network in INTERNAL_IP_RANGES):
                return True
        return False  # If none of the IPs are in the internal ranges
    except socket.gaierror:
        # Handle case where the hostname cannot be resolved by treating it as internal
        return True
    
@app.get("/check-phishing/", tags=["url"])
async def check_phishing(url: str, background_tasks: BackgroundTasks):
    # Schedule the feed to be updated if necessary
    if datetime.now() - phishing_data.last_update_time > timedelta(hours=12):
        background_tasks.add_task(phishing_data.update_phishing_urls)
    
    if url in phishing_data.phishing_urls:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"message": "The URL is flagged as a phishing site based on OpenPhish and Phishing Army data", "status_code": 403}
        )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "The URL is not flagged as a phishing site based on OpenPhish and Phishing Army data", "status_code": 200}
    )

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
        'secret_key': db_url.secret_key,
        'qr_code': f"data:image/png;base64,{qr_code_base64}",
        'title': db_url.title,
        'favicon_url': db_url.favicon_url
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
    
@app.websocket("/ws/url_update/{secret_key}")
async def websocket_endpoint(
    websocket: WebSocket, 
    secret_key: str, 
    db: Session = Depends(get_db)
):
    
    await websocket.accept()

    # รับข้อความแรกที่มี api_key
    auth_data = await websocket.receive_json()
    api_key = auth_data.get("api_key")

    # ตรวจสอบว่าผู้ใช้มีสิทธิ์เข้าถึง URL นี้หรือไม่
    if not crud.is_url_owner(db, secret_key, api_key): 
        await websocket.close(code=1008, reason="Unauthorized")  # ปิดการเชื่อมต่อหากไม่ได้รับอนุญาต
        return

    is_updated = False
    timeout = 10  # กำหนด timeout เป็น 10 วินาที (หรือค่าที่เหมาะสม)
    start_time = time.time()

    while not is_updated and time.time() - start_time < timeout:
        is_updated = crud.is_url_info_updated(db, secret_key, api_key)

        if is_updated:
            db_url = crud.get_db_url_by_secret_key(db, secret_key=secret_key, api_key=api_key)
            url_info = get_admin_info(db_url)

            # Decode the JSONResponse body before accessing elements
            url_info_dict = json.loads(url_info.body.decode("utf-8"))

            await websocket.send_json(url_info_dict)  # Send the content of the JSONResponse 

        await asyncio.sleep(5)

    # ถ้าออกจาก loop แสดงว่าไม่มีการอัพเดต หรือมีการอัพเดตแล้ว ให้ปิดการเชื่อมต่อ
    await websocket.close()
    
async def fetch_page_info(url: str):
    """Fetch title and favicon from the given URL asynchronously."""

    try:
        async with aiohttp.ClientSession() as session:  # ใช้ aiohttp สำหรับ async request
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                content = await response.text()  # รอรับเนื้อหาของหน้าเว็บ

        soup = BeautifulSoup(content, 'html.parser')

        title = soup.find('title')
        title = title.text.strip() if title else 'No title found'

        favicon = soup.find('link', rel='icon')
        if favicon:
            favicon_url = favicon['href']
            if not favicon_url.startswith('http'):
                favicon_url = urljoin(url, favicon_url)
        else:
            favicon_url = None

        return title, favicon_url

    except aiohttp.ClientError:  # จัดการ exception จาก aiohttp
        return None, None
    
# Create a thread pool executor (you can adjust the max_workers if needed)
executor = ThreadPoolExecutor(max_workers=2)

def fetch_page_info_and_update_sync(db_url: models.URL):
    """Fetch page info and update the database synchronously."""
    with SessionLocal() as db:
        loop = asyncio.new_event_loop()  # Create a new event loop
        asyncio.set_event_loop(loop)  # Set the new event loop as the current one
        title, favicon_url = loop.run_until_complete(fetch_page_info(db_url.target_url))  # Await the coroutine
        loop.close()  # Close the event loop

        db_url = db.merge(db_url)
        db_url.title = title
        db_url.favicon_url = favicon_url
        db.commit()

async def fetch_page_info_and_update(db_url: models.URL):
    """Wrapper to run the synchronous function in a separate thread."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        executor, partial(fetch_page_info_and_update_sync, db_url)
    )

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


@app.post("/api/register_api_key", tags=["api key"])
def register_api_key(api_key: schemas.APIKeyCreate, db: Session = Depends(get_api_db), _: str = Depends(verify_jwt_token)):
    result = crud.register_api_key(db, api_key.api_key, api_key.role_id)
    return JSONResponse(content={"message": result["message"]}, status_code=result["status_code"])

@app.post("/api/deactivate_api_key", tags=["api key"])
def deactivate_api_key(api_key: schemas.APIKeyDelete, db: Session = Depends(get_api_db), _: str = Depends(verify_jwt_token)):
    result = crud.deactivate_api_key(db=db, api_key=api_key.api_key)
    return JSONResponse(content={"message": result["message"]}, status_code=result["status_code"])


@app.post("/api/refresh_token", tags=["api key"])
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
        # Check if target URL exists or is in the internal network
        if is_internal_url(db_url.target_url):
            # Skip the reachability check for internal URLs
            crud.update_db_clicks(db=db, db_url=db_url)
            return RedirectResponse(db_url.target_url)
        else:
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
async def create_url(
    url: schemas.URLBase,
    background_tasks: BackgroundTasks,
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

    # ตรวจสอบว่า URL เป็น phishing หรือไม่โดยใช้ check_phishing
    phishing_check_response = await check_phishing(url.target_url, background_tasks)
    if phishing_check_response.status_code == 403:
        raise_forbidden(message=phishing_check_response.content["message"])
    
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
            "secret_key": existing_url.secret_key,
            "title": existing_url.title,
            "favicon_url": existing_url.favicon_url,
            "message": f"A short link for this website already exists."
        }
        return JSONResponse(content=url_data, status_code=409) 

    db_url = crud.create_db_url(db=db, url=url, api_key=api_key)

    # เพิ่ม task การดึงข้อมูล title และ favicon ลงใน background
    background_tasks.add_task(fetch_page_info_and_update, db_url)

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

@app.get("/user/urls", tags=["info"])
async def get_user_url(
    api_key: str = Depends(verify_api_key), 
    db: Session = Depends(get_db)
):
    user_urls = db.query(models.URL).filter(models.URL.api_key == api_key, models.URL.is_active == 1).all()
    user_urls_json = jsonable_encoder(user_urls)
    return JSONResponse(content=user_urls_json, status_code=200)

@app.get("/user/url/status", response_model=List[schemas.ScanStatus], tags=["info"])
def get_url_scan_status(
    secret_key: str,
    target_url: str,
    scan_type: str = None,  # Optional filter for scan_type
    api_key: str = Depends(verify_api_key), 
    db: Session = Depends(get_db),
    api_db: Session = Depends(get_api_db),
):
    is_valid = crud.verify_secret_and_api_key(db, secret_key=secret_key, api_key=api_key, api_db=api_db)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Secret key or API key not found or invalid."
        )

    query = db.query(models.scan_records).filter(models.scan_records.url == target_url)
    
    if scan_type:
        query = query.filter(models.scan_records.scan_type == scan_type)

    scan_records = query.order_by(models.scan_records.timestamp.desc()).all()

    if not scan_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan records not found."
        )

    return [
        schemas.ScanStatus(
            url=record.url,
            status=record.status if record.status is not None else "None",
            result=record.result,
            scan_type=record.scan_type,
            timestamp=record.timestamp
        )
        for record in scan_records
    ]

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
    if db_url := crud.get_db_url_by_secret_key(db, secret_key=secret_key, api_key=api_key):
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
    if db_url := crud.deactivate_db_url_by_secret_key(db, secret_key=secret_key, api_key=api_key):
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