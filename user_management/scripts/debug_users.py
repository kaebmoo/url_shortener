import sys
import os

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import User
from sqlalchemy import inspect

app = create_app('development')

with app.app_context():
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('users')]
    print(f"Columns in users table: {columns}")
    
    if 'telegram_id' not in columns:
        print("CRITICAL: telegram_id column missing!")
    else:
        print("telegram_id column exists.")

    print("\nExisting Users:")
    users = User.query.all()
    for u in users:
        print(f"ID: {u.id}, Email: {u.email}, TelegramID: {u.telegram_id}, UID: {u.uid}, Role: {u.role.name if u.role else 'None'}")
