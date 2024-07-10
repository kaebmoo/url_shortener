# shortener_app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import get_settings

engine = create_engine(get_settings().db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database for API keys (user management or other purposes)
engine_api = create_engine(get_settings().db_api, connect_args={"check_same_thread": False})
SessionAPI = sessionmaker(autocommit=False, autoflush=False, bind=engine_api)
BaseAPI = declarative_base()

# Database for Blacklist URL
engine_blacklist = create_engine(get_settings().db_blacklist, connect_args={"check_same_thread": False})
SessionBlacklist = sessionmaker(autocommit=False, autoflush=False, bind=engine_blacklist)
BaseBlacklist = declarative_base()


# ฟังก์ชันสร้างตารางสำหรับ URL shortener
# def init_db():
#    Base.metadata.create_all(bind=engine)

# ฟังก์ชันสร้างตารางสำหรับ API keys
# def init_api_db():
#     BaseAPI.metadata.create_all(bind=engine_api)