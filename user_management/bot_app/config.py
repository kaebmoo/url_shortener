import os

class Config:
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    SHORTENER_HOST = os.environ.get('SHORTENER_HOST', 'http://127.0.0.1:8000')
    ADMIN_TELEGRAM_ID = os.environ.get('ADMIN_TELEGRAM_ID') 
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    print(f"DEBUG: Config.ADMIN_TELEGRAM_ID = {ADMIN_TELEGRAM_ID}")
    # Add other bot-specific configs here
