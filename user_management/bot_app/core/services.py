import secrets
import string
import requests
import jwt
import datetime
from flask import current_app
from app import db
from app.models.user import User, Role, Permission
from bot_app.config import Config
from sqlalchemy.orm import joinedload

# --- Helpers ---

def generate_random_password(length=12):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for i in range(length))

def generate_jwt():
    """Generates a JWT token for inter-service communication."""
    payload = {
        "sub": "user_management",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")

def register_api_key_remote(api_key: str, role_id: int):
    """
    Registers or updates the API key in shortener_app via API.
    Role IDs: 1=User, 2=Admin, 3=VIP
    """
    token = generate_jwt()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "api_key": api_key,
        "role_id": role_id
    }
    try:
        # Note: SHORTENER_HOST in config might not have /api prefix in the variable itself, 
        # but the endpoint is /api/register_api_key
        url = f"{Config.SHORTENER_HOST}/api/register_api_key"
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code not in [200, 201]:
            print(f"Failed to register API key: {response.text}")
            return False
        return True
    except Exception as e:
        print(f"Error registering API key: {e}")
        return False

# --- Internal Model Access ---

def _get_or_create_shadow_user_model(telegram_id: int) -> User:
    """
    Internal function to get/create user model. 
    MUST participate in an active session.
    """
    user = User.query.options(joinedload(User.role)).filter_by(telegram_id=str(telegram_id)).first()
    
    if not user:
        email = f"tg_{telegram_id}@bot.local"
        user = User.query.options(joinedload(User.role)).filter_by(email=email).first()

        if not user:
            user = User()
            user.email = email
            user.first_name = "Telegram"
            user.last_name = str(telegram_id)
            user.telegram_id = str(telegram_id)
            user.password = generate_random_password()
            user.confirmed = True
            
            # Default role in User Management (usually User)
            default_role = Role.query.filter_by(default=True).first()
            if default_role:
                user.role = default_role
            
            import uuid
            user.uid = str(uuid.uuid4())
            
            db.session.add(user)
            db.session.commit()
            
            # Register with Shortener App (Role 1 = User)
            register_api_key_remote(user.uid, 1)
            
            # Refresh
            user = User.query.options(joinedload(User.role)).get(user.id)
            
    return user

def is_vip_model(user: User) -> bool:
    return user.can(Permission.VIP) or user.can(Permission.ADMINISTER)

def get_url_count_model(user: User) -> int:
    headers = {'X-API-KEY': user.uid}
    try:
        response = requests.get(f"{Config.SHORTENER_HOST}/user/url_count", headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json().get('url_count', 0)
        elif response.status_code in [401, 403]:
            # Try to register/sync key and retry
            print(f"Auth failed for {user.telegram_id}, attempting to register key...")
            is_vip = is_vip_model(user)
            role_id = 3 if is_vip else 1
            if register_api_key_remote(user.uid, role_id):
                 # Retry once
                 response = requests.get(f"{Config.SHORTENER_HOST}/user/url_count", headers=headers, timeout=5)
                 if response.status_code == 200:
                     return response.json().get('url_count', 0)
    except Exception as e:
        print(f"Error fetching url count: {e}")
    return 9999

# --- Public Services (Session-Safe) ---

def get_user_info(telegram_id: int):
    """
    Returns dict with user info, avoiding detached objects.
    """
    user = _get_or_create_shadow_user_model(telegram_id)
    is_vip = is_vip_model(user)
    count = get_url_count_model(user)
    
    return {
        "is_vip": is_vip,
        "url_count": count
    }

def shorten_url_service(telegram_id: int, target_url: str, custom_key: str = None):
    """
    Shorten URL safe service.
    """
    user = _get_or_create_shadow_user_model(telegram_id)
    
    # Check Limits
    is_vip = is_vip_model(user)
    if not is_vip:
        count = get_url_count_model(user)
        if count >= 30:
            return {"error": "Limit Exceeded", "message": "You have reached the limit of 30 URLs. Please upgrade to VIP."}
            
    # Prepare API Call
    headers = {
        'X-API-KEY': user.uid,
        'Content-Type': 'application/json'
    }
    payload = {
        "target_url": target_url
    }
    if custom_key and is_vip:
        payload["custom_key"] = custom_key
        
    try:
        response = requests.post(f"{Config.SHORTENER_HOST}/url", json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code == 409:
             return {"error": "Conflict", "message": "Custom key already exists."}
        elif response.status_code == 401:
             # Retry registration?
             register_api_key_remote(user.uid, 3 if is_vip else 1)
             return {"error": "Auth Error", "message": "Authentication failed. Retrying registration..."}
        else:
            return {"error": "API Error", "message": f"Failed to shorten. Status: {response.status_code}"}
    except Exception as e:
        return {"error": "Connection Error", "message": str(e)}

def promote_to_vip_service(telegram_id: int):
    """
    Promote by Telegram ID.
    """
    user = User.query.filter_by(telegram_id=str(telegram_id)).first()
    if user:
        vip_role = Role.query.filter_by(name='VIP').first()
        if vip_role:
            user.role = vip_role
            db.session.commit()
            
            # Sync to Shortener App (Role 3 = VIP)
            register_api_key_remote(user.uid, 3)
            
            return True
    return False

def list_urls_service(telegram_id: int):
    """
    Fetch list of URLs for the user.
    """
    user = _get_or_create_shadow_user_model(telegram_id)
    headers = {'X-API-KEY': user.uid}
    try:
        response = requests.get(f"{Config.SHORTENER_HOST}/user/urls", headers=headers, timeout=10)
        if response.status_code == 200:
             return response.json() # Returns list of dicts
        elif response.status_code in [401, 403]:
             register_api_key_remote(user.uid, 3 if is_vip_model(user) else 1)
             # Retry
             response = requests.get(f"{Config.SHORTENER_HOST}/user/urls", headers=headers, timeout=10)
             if response.status_code == 200:
                 return response.json()
    except Exception as e:
        print(f"Error fetching URLs: {e}")
    return []

def delete_url_service(telegram_id: int, secret_key: str):
    """
    Delete a shortened URL by secret key.
    """
    user = _get_or_create_shadow_user_model(telegram_id)
    headers = {'X-API-KEY': user.uid}
    try:
        url = f"{Config.SHORTENER_HOST}/admin/{secret_key}"
        response = requests.delete(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {"success": True, "message": "Deleted successfully."}
        elif response.status_code == 404:
            return {"success": False, "message": "URL not found or already deleted."}
        elif response.status_code in [401, 403]:
             register_api_key_remote(user.uid, 3 if is_vip_model(user) else 1)
             # Retry
             response = requests.delete(url, headers=headers, timeout=10)
             if response.status_code == 200:
                 return {"success": True, "message": "Deleted successfully."}
             elif response.status_code == 404:
                 return {"success": False, "message": "URL not found."}
        
        return {"success": False, "message": f"Failed to delete. Status: {response.status_code}"}
    except Exception as e:
        return {"success": False, "message": str(e)}
