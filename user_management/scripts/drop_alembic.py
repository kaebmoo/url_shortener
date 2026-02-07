import sys
import os

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy import text

app = create_app('development')

with app.app_context():
    try:
        db.session.execute(text("DROP TABLE alembic_version"))
        db.session.commit()
        print("Success: Dropped alembic_version table.")
    except Exception as e:
        print(f"Error: {e}")
