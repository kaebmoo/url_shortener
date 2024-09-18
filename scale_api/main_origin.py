import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from redis import Redis


# PostgreSQL connection
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://username:password@127.0.0.1/shortener"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis connection
redis = Redis(host='localhost', port=6379, db=0)

# SQLAlchemy model
class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    secret_key = Column(String, unique=True, index=True)
    target_url = Column(String, index=True)
    is_active = Column(Boolean)
    clicks = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    api_key = Column(String, index=True)
    is_checked = Column(Boolean, default=False)
    status = Column(String)
    title = Column(String(255))
    favicon_url = Column(String(255))

# Function to sync data from PostgreSQL to Redis
def sync_to_redis(url: URL):
    url_data = {
        "id": url.id,
        "key": url.key,
        "secret_key": url.secret_key,
        "target_url": url.target_url,
        "is_active": url.is_active,
        "clicks": url.clicks,
        "created_at": url.created_at.isoformat() if url.created_at else None,
        "updated_at": url.updated_at.isoformat() if url.updated_at else None,
        "api_key": url.api_key,
        "is_checked": url.is_checked,
        "status": url.status,
        "title": url.title,
        "favicon_url": url.favicon_url
    }
    redis.set(f"url:{url.key}", json.dumps(url_data))

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Sync all data from PostgreSQL to Redis
    db = SessionLocal()
    urls = db.query(URL).all()
    for url in urls:
        sync_to_redis(url)
    db.close()
    yield
    # Shutdown: You can add cleanup code here if needed

# FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Route to get URL by key
@app.get("/url/{key}")
def get_url(key: str, db: Session = Depends(get_db)):
    # Try to get data from Redis
    url_data = redis.get(f"url:{key}")
    if url_data:
        url_dict = json.loads(url_data)
        # Update clicks in PostgreSQL
        db_url = db.query(URL).filter(URL.key == key).first()
        if db_url:
            db_url.clicks += 1
            db_url.updated_at = datetime.now(timezone.utc)
            db.commit()
            # Update Redis data
            url_dict["clicks"] += 1
            url_dict["updated_at"] = db_url.updated_at.isoformat()
            redis.set(f"url:{key}", json.dumps(url_dict))
        return url_dict
    else:
        # If not in Redis, get from PostgreSQL and sync to Redis
        db_url = db.query(URL).filter(URL.key == key).first()
        if db_url:
            db_url.clicks += 1
            db_url.updated_at = datetime.now(timezone.utc)
            db.commit()
            sync_to_redis(db_url)
            return {
                "id": db_url.id,
                "key": db_url.key,
                "target_url": db_url.target_url,
                "clicks": db_url.clicks,
                "updated_at": db_url.updated_at.isoformat()
            }
    raise HTTPException(status_code=404, detail="URL not found")

# Route to create new URL
@app.post("/url")
def create_url(url: dict, db: Session = Depends(get_db)):
    current_time = datetime.now(timezone.utc)
    url["created_at"] = current_time
    url["updated_at"] = current_time
    db_url = URL(**url)
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    sync_to_redis(db_url)
    return {"message": "URL created successfully", "key": db_url.key}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9000)