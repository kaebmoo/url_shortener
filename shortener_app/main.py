# shortener_app/main.py
import requests  # Import for checking website existence
import secrets
import validators
from fastapi import Depends, FastAPI, HTTPException, Request, status, Security
from fastapi.security import APIKeyHeader
from fastapi.openapi.models import APIKey, APIKeyIn, SecurityScheme
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.datastructures import URL
from fastapi.responses import JSONResponse
from qrcodegen import QrCode
from PIL import Image
import io
import base64

from .config import get_settings
from .database import SessionLocal, SessionAPI, engine, engine_api
from . import crud, models, schemas


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

def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)

def raise_already_used(message):
    raise HTTPException(status_code=400, detail=message)

def raise_not_reachable(message):
    raise HTTPException(status_code=504, detail=message)

def raise_api_key(api_key: str):
    message = f"API key '{api_key}' is missing or invalid"
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)


app = FastAPI()

models.Base.metadata.create_all(bind=engine)
models.BaseAPI.metadata.create_all(bind=engine_api)

def normalize_url(url, add_slash=False):
    if add_slash:
        if not url.endswith('/'):
            url += '/'
    else:
        if url.endswith('/'):
            url = url[:-1]
    return url

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
    api_key: str = Depends(verify_api_key)
):
    url.target_url = normalize_url(url.target_url)

    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")
    
    # ตรวจสอบว่ามี URL นี้อยู่แล้วหรือไม่สำหรับ API key นี้

    existing_url = crud.is_url_existing_for_key(db, url.target_url, api_key)
    if existing_url:
        base_url = get_settings().base_url
        url_data = {
            "target_url": existing_url.target_url,
            "is_active": existing_url.is_active,
            "clicks": existing_url.clicks,
            "url": f"{base_url}/{existing_url.key}", 
            "admin_url": f"{base_url}/{existing_url.secret_key}",
            "message": f"A short link for this website already exists."
        }
        return JSONResponse(content=url_data, status_code=200) 

    db_url = crud.create_db_url(db=db, url=url, api_key=api_key)
    return get_admin_info(db_url)

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