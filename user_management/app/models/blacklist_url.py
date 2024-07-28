from .. import db

class URL(db.Model):
    __bind_key__ = 'blacklist_db'
    __tablename__ = 'url'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    date_added = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(500), nullable=False)
    status = db.Column(db.Boolean, default=True)