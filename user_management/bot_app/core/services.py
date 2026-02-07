import secrets
import string
import requests
import jwt
import datetime
import logging
import validators
from flask import current_app
from app import db
from app.models.user import User, Role, Permission
from bot_app.config import Config
from sqlalchemy.orm import joinedload

# Configure logging
logger = logging.getLogger(__name__)

# --- Constants ---
MAX_RETRY_ATTEMPTS = 2
REQUEST_TIMEOUT = 10
MAX_URL_LENGTH = 2048

# --- URL Validation ---

def is_valid_url(url: str) -> bool:
    """Validate URL format using validators library."""
    if not url or len(url) > MAX_URL_LENGTH:
        return False
    return validators.url(url) is True

def normalize_url(url: str) -> str:
    """Normalize and validate URL, add scheme if missing."""
    url = url.strip()
    if not url:
        return None

    # Add https:// if no scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    if is_valid_url(url):
        return url
    return None

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

def _make_request_with_retry(method: str, url: str, headers: dict,
                              json_data: dict = None, max_retries: int = MAX_RETRY_ATTEMPTS):
    """
    Make HTTP request with retry logic.
    Returns (response, success) tuple.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            elif method == 'POST':
                response = requests.post(url, json=json_data, headers=headers, timeout=REQUEST_TIMEOUT)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=REQUEST_TIMEOUT)
            else:
                raise ValueError(f"Unsupported method: {method}")

            return response, True
        except requests.exceptions.Timeout:
            last_error = "Request timed out"
            logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries}): {url}")
        except requests.exceptions.ConnectionError:
            last_error = "Connection failed"
            logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries}): {url}")
        except Exception as e:
            last_error = str(e)
            logger.error(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
            break  # Don't retry on unknown errors

    return None, False

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

    url = f"{Config.SHORTENER_HOST}/api/register_api_key"
    logger.info(f"Registering API Key for {api_key[:8]}... at {url}")

    response, success = _make_request_with_retry('POST', url, headers, payload)

    if not success:
        logger.error(f"Failed to register API key after retries")
        return False

    if response.status_code not in [200, 201]:
        logger.error(f"Failed to register API key. Status: {response.status_code}, Body: {response.text}")
        return False

    logger.info(f"API Key registered successfully")
    return True

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
            logger.info(f"Created new shadow user {telegram_id}. Registering API key...")
            register_api_key_remote(user.uid, 1)

            # Refresh
            user = User.query.options(joinedload(User.role)).get(user.id)

    return user

def is_vip_model(user: User) -> bool:
    return user.can(Permission.VIP) or user.can(Permission.ADMINISTER)

def _try_register_and_retry(user: User, method: str, url: str, headers: dict, json_data: dict = None):
    """
    Try to register API key and retry the request once.
    Returns (response, success) tuple.
    """
    is_vip = is_vip_model(user)
    role_id = 3 if is_vip else 1

    if register_api_key_remote(user.uid, role_id):
        # Retry once after registration
        return _make_request_with_retry(method, url, headers, json_data, max_retries=1)

    return None, False

def get_url_count_model(user: User) -> int:
    headers = {'X-API-KEY': user.uid}
    url = f"{Config.SHORTENER_HOST}/user/url_count"

    response, success = _make_request_with_retry('GET', url, headers)

    if not success:
        logger.error(f"Failed to get URL count after retries")
        return 9999

    if response.status_code == 200:
        return response.json().get('url_count', 0)
    elif response.status_code in [401, 403]:
        logger.warning(f"Auth failed for user. Attempting to register key...")
        response, success = _try_register_and_retry(user, 'GET', url, headers)
        if success and response.status_code == 200:
            return response.json().get('url_count', 0)

    logger.error(f"Failed to get URL count. Status: {response.status_code if response else 'N/A'}")
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

def validate_url_input(target_url: str) -> dict:
    """
    Validate and normalize URL input.
    Returns dict with 'url' on success or 'error' on failure.
    """
    if not target_url:
        return {"error": "Empty URL", "message": "Please provide a URL to shorten."}

    normalized = normalize_url(target_url)
    if not normalized:
        return {
            "error": "Invalid URL",
            "message": "Invalid URL format. Please use a valid URL like https://example.com"
        }

    return {"url": normalized}

def shorten_url_service(telegram_id: int, target_url: str, custom_key: str = None):
    """
    Shorten URL safe service.
    """
    # Validate URL first
    validation = validate_url_input(target_url)
    if "error" in validation:
        return validation

    target_url = validation["url"]

    user = _get_or_create_shadow_user_model(telegram_id)

    # Check Limits
    is_vip = is_vip_model(user)
    if not is_vip:
        count = get_url_count_model(user)
        if count >= 30:
            return {
                "error": "Limit Exceeded",
                "message": "You have reached the limit of 30 URLs.\n\nUse /upgrade to get unlimited URLs!"
            }

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
    elif custom_key and not is_vip:
        return {
            "error": "VIP Feature",
            "message": "Custom aliases are a VIP feature.\n\nUse /upgrade to unlock this feature!"
        }

    url = f"{Config.SHORTENER_HOST}/url"
    response, success = _make_request_with_retry('POST', url, headers, payload)

    if not success:
        return {"error": "Connection Error", "message": "Failed to connect to server. Please try again later."}

    if response.status_code in [200, 201]:
        return response.json()
    elif response.status_code == 409:
        return {"error": "Conflict", "message": "This custom alias already exists. Please choose another one."}
    elif response.status_code == 401:
        # Try to re-register and retry
        response, success = _try_register_and_retry(user, 'POST', url, headers, payload)
        if success and response.status_code in [200, 201]:
            return response.json()
        return {"error": "Auth Error", "message": "Authentication failed. Please try again."}
    else:
        logger.error(f"Shorten failed. Status: {response.status_code}, Body: {response.text}")
        return {"error": "API Error", "message": f"Failed to shorten URL. Please try again later."}

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
    url = f"{Config.SHORTENER_HOST}/user/urls"

    response, success = _make_request_with_retry('GET', url, headers)

    if not success:
        logger.error(f"Failed to list URLs after retries")
        return []

    if response.status_code == 200:
        return response.json()
    elif response.status_code in [401, 403]:
        response, success = _try_register_and_retry(user, 'GET', url, headers)
        if success and response.status_code == 200:
            return response.json()

    logger.error(f"List URLs failed. Status: {response.status_code if response else 'N/A'}")
    return []

def delete_url_service(telegram_id: int, secret_key: str):
    """
    Delete a shortened URL by secret key.
    """
    user = _get_or_create_shadow_user_model(telegram_id)
    headers = {'X-API-KEY': user.uid}
    url = f"{Config.SHORTENER_HOST}/admin/{secret_key}"

    response, success = _make_request_with_retry('DELETE', url, headers)

    if not success:
        return {"success": False, "message": "Failed to connect to server. Please try again later."}

    if response.status_code == 200:
        return {"success": True, "message": "Deleted successfully."}
    elif response.status_code == 404:
        return {"success": False, "message": "URL not found or already deleted."}
    elif response.status_code in [401, 403]:
        response, success = _try_register_and_retry(user, 'DELETE', url, headers)
        if success:
            if response.status_code == 200:
                return {"success": True, "message": "Deleted successfully."}
            elif response.status_code == 404:
                return {"success": False, "message": "URL not found."}

    return {"success": False, "message": f"Failed to delete. Please try again later."}
