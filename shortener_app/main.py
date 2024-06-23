# shortener_app/main.py

import secrets
import validators
from fastapi import Depends, FastAPI, HTTPException, Request, status, Security
from fastapi.security import APIKeyHeader
from fastapi.openapi.models import APIKey, APIKeyIn, SecurityScheme
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.datastructures import URL

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
    return db_url

def raise_not_found(request):
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)

def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)

def raise_api_key(api_key: str):
    message = f"API key '{api_key}' is missing or invalid"
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)


app = FastAPI()
models.Base.metadata.create_all(bind=engine)
models.BaseAPI.metadata.create_all(bind=engine_api)

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


'''# ฟังก์ชันตรวจสอบ API key จากฐานข้อมูล API keys
async def verify_api_key(
    api_key: str = Depends(api_key_header),
    db: Session = Depends(get_api_db)
):
    db_api_key = crud.get_api_key(db, api_key)
    if not db_api_key:
        raise_api_key(api_key)'''

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
        crud.update_db_clicks(db=db, db_url=db_url)
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)
    # The := operator is colloquially known as the walrus operator and gives you a new syntax for assigning variables in the middle of expressions.
    # If db_url is a database entry, then you return your RedirectResponse to target_url. Otherwise, you call raise_not_found()


'''@app.post("/url", response_model=schemas.URLInfo)
def create_url(url: schemas.URLBase, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    # ตรวจสอบ URL
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")
    
    db_url = crud.create_db_url(db=db, url=url)
    return get_admin_info(db_url)'''

@app.post("/url", response_model=schemas.URLInfo, tags=["url"]) # , dependencies=[Security(verify_api_key)]
def create_url(
    url: schemas.URLBase,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")
    
    # ตรวจสอบว่ามี URL นี้อยู่แล้วหรือไม่สำหรับ API key นี้
    if crud.is_url_existing_for_key(db, url.target_url, api_key):
        raise_bad_request(message="Looks like this destination is already used for another short link.")
    
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