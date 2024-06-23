# shortener_app/models.py

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, event
from sqlalchemy.sql import func
from sqlalchemy import event
from sqlalchemy.orm import mapper

from .database import Base, BaseAPI

class URL(Base):
    __tablename__ = "urls"  # ชื่อ table ใน sqlite

    id = Column(Integer, primary_key=True)                  # primary key
    key = Column(String, unique=True, index=True)           # shorten 
    secret_key = Column(String, unique=True, index=True)    # a secret key to the user to manage their shortened URL and see statistics.
    target_url = Column(String, index=True)                 # to store the URL strings for which your app provides shortened URLs.
    is_active = Column(Boolean, default=True)               # false is delete
    clicks = Column(Integer, default=0)     # this field will increase the integer each time someone clicks the shortened link.
    api_key = Column(String, index=True)  # เพิ่มฟิลด์นี้เพื่อเก็บ API key
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # เพิ่มฟิลด์วันที่และเวลาในการสร้าง
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())       # เพิ่มฟิลด์วันที่และเวลาในการอัปเดต

class APIKey(BaseAPI):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    confirmed = Column(Boolean, default=False)
    first_name = Column(String(64), index=True)
    last_name = Column(String(64), index=True)
    email = Column(String(64), unique=True, index=True)
    phone_number = Column(String(15), unique=True, index=True, nullable=True)
    password_hash = Column(String(128))
    role_id = Column(Integer, ForeignKey('roles.id'))
    uid = Column(String(64), unique=True, index=True)
    # created_at = Column(DateTime(timezone=True), server_default=func.now())  # เพิ่มฟิลด์วันที่และเวลาในการสร้าง
    # updated_at = Column(DateTime(timezone=True), onupdate=func.now())       # เพิ่มฟิลด์วันที่และเวลาในการอัปเดต

# ฟังก์ชันนี้จะทำให้แน่ใจว่า updated_at ถูกอัปเดตเมื่อมีการอัปเดตแถว
@event.listens_for(URL, 'before_update')
def receive_before_update(mapper, connection, target):
    target.updated_at = func.now()