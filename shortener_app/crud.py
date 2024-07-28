# shortener_app/crud.py

from sqlalchemy.orm import Session
from sqlalchemy import func

from . import keygen, models, schemas

def create_db_url(db: Session, url: schemas.URLBase, api_key: str) -> models.URL:
    # key = keygen.create_random_key()
    # secret_key = keygen.create_random_key(length=8)
    
    # key = keygen.create_unique_random_key(db)
    key = url.custom_key if url.custom_key else keygen.create_unique_random_key(db)
    secret_key = f"{key}_{keygen.create_random_key(length=8)}"
    
    db_url = models.URL(
        target_url=url.target_url, 
        key=key, 
        secret_key=secret_key,
        api_key=api_key  # Store API key associated with the URL
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url

def get_db_url_by_key(db: Session, url_key: str) -> models.URL:
    return (
        db.query(models.URL)
        .filter(models.URL.key == url_key, models.URL.is_active, func.lower(models.URL.status) != 'danger' )
        .first()
    )

def get_db_url_by_customkey(db: Session, url_key: str) -> models.URL:
    return (
        db.query(models.URL)
        .filter(models.URL.key == url_key)
        .first()
    )

def get_db_url_by_secret_key(db: Session, secret_key: str) -> models.URL:
    return (
        db.query(models.URL)
        .filter(models.URL.secret_key == secret_key, models.URL.is_active)
        .first()
    )

def update_db_clicks(db: Session, db_url: schemas.URL) -> models.URL:
    db_url.clicks += 1
    db.commit()
    db.refresh(db_url)
    return db_url

def deactivate_db_url_by_secret_key(db: Session, secret_key: str) -> models.URL:
    db_url = get_db_url_by_secret_key(db, secret_key)
    if db_url:
        db_url.is_active = False
        db.commit()
        db.refresh(db_url)
    return db_url

def get_api_key(db: Session, api_key: str) -> models.APIKey:
    return db.query(models.APIKey).filter(models.APIKey.uid == api_key).first()

def get_role_id(db: Session, api_key: str) -> int:
    api_key_data = db.query(models.APIKey).filter(models.APIKey.uid == api_key).first()
    if api_key_data:
        return api_key_data.role_id
    return None

def get_role_name(api_db: Session, role_id: int) -> str:
    role = api_db.query(models.Role).filter(models.Role.id == role_id).first()
    if role:
        return role.name
    return None

# def is_url_existing_for_key(db: Session, target_url: str, api_key: str) -> bool:
#     return db.query(models.URL).filter(models.URL.target_url == target_url, models.URL.api_key == api_key, models.URL.is_active).first() is not None

def is_url_existing_for_key(db: Session, target_url: str, api_key: str) -> models.URL | None:
    """Checks if a URL exists for a given target_url and api_key. 
    Returns the URL object if found, or None if not found."""

    return db.query(models.URL).filter(
        models.URL.target_url == target_url, 
        models.URL.api_key == api_key, 
        models.URL.is_active
    ).first()  # This will return the URL object itself or None

# เพิ่มใน shortener_app/crud.py
def is_url_in_blacklist(db: Session, url: str) -> bool:
    """Checks if a URL is in the blacklist."""
    return db.query(models.Blacklist).filter(models.Blacklist.url == url).first() is not None

