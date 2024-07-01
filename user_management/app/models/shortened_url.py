from datetime import datetime
from .. import db

class ShortenedURL(db.Model):
    __bind_key__ = 'shortener_db'
    __tablename__ = 'urls'
    id = db.Column(db.Integer, primary_key=True)
    target_url = db.Column(db.String(512), nullable=False)
    key = db.Column(db.String(10), unique=True, nullable=False)
    secret_key = db.Column(db.String(32), nullable=False)
    clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime)
    api_key = db.Column(db.String(64), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
