import os

class Config:
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    SHORTENER_HOST = os.environ.get('SHORTENER_HOST', 'http://127.0.0.1:8000')
    ADMIN_TELEGRAM_ID = os.environ.get('ADMIN_TELEGRAM_ID') 
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    VIP_PRICE = os.environ.get('VIP_PRICE', '99 THB/Year')
    VIP_BANK = os.environ.get('VIP_BANK', 'Unknown Bank')
    VIP_ACCOUNT = os.environ.get('VIP_ACCOUNT', 'Unknown Account')
    # Add other bot-specific configs here
