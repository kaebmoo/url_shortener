# Telegram Bot Architecture Documentation

This document explains the internal working of the Telegram Bot located in `user_management/bot_app`.

## 📂 File Structure

- **`run.py`**: The entry point of the application. Handles initialization and lifecycle.
- **`core/handlers.py`**: Contains all Telegram event handlers (commands, messages, callbacks).
- **`core/services.py`**: Business logic layer. Handles database interactions and API calls to the Shortener Service.
- **`config.py`**: Configuration constants.

---

## 🏗️ Core Components

### 1. Entry Point (`run.py`)

- **Initialization**:
  - Loads environment variables.
  - Initializes the Flask application (`create_app`) to gain access to the database context.
  - Builds the Telegram `Application` using `ApplicationBuilder`.
- **Context Sharing**:
  - Stores the `flask_app` instance in `application.bot_data`. This allows handlers to push the Flask application context when they need to access the database.
- **Graceful Shutdown**:
  - Uses `signal` module to catch `SIGINT` (Ctrl+C) and `SIGTERM`.
  - Ensures the bot stops polling and closes connections cleanly.

### 2. Handlers (`core/handlers.py`)

This file maps Telegram events to functions.

- **Rate Limiting**:
  - Implements a simple in-memory rate limiter (`check_rate_limit`) to prevent spam (2 seconds cooldown).
- **Command Handlers**:
  - `/start`, `/help`: Show welcome/help messages.
  - `/upgrade`: Initiates the VIP upgrade flow with an Inline Keyboard.
  - `/list`: Fetches and displays the user's URL history.
  - `/delete`: Deletes a URL by its secret key.
  - `/approve`, `/reject`: Admin commands to manage VIP requests.
- **Callback Query Handlers**:
  - Handles clicks on Inline Buttons (Cancel, Approve, Reject).
  - Uses strictly formatted callback data (e.g., `approve_12345`) to route actions.
- **Message Handlers**:
  - **Photos**: Captures slip images for VIP upgrades and forwards them to the admin.
  - **Text**: Treats any non-command text as a URL to be shortened.
- **State Management**:
  - Uses `pending_requests` dictionary to temporarily store upgrade request metadata (User ID, Name, Photo ID) in memory.

### 3. Services (`core/services.py`)

This layer isolates business logic and external API communication.

- **Shadow User Model**:
  - `_get_or_create_shadow_user_model`: Ensures every Telegram user has a corresponding "Shadow User" in the `users` database table. It links them via `telegram_id`.
- **API Integration**:
  - Communicates with the **Shortener App** (backend) via HTTP requests.
  - **Auth**: Generates JWT tokens (signed with the shared `SECRET_KEY`) to authenticate requests as the "User Management" service.
  - **Retry Logic**: Implements retry with exponential backoff for network resilience.
- **Features**:
  - `shorten_url_service`: Validates input, checks limits, and calls the backend to create a link.
  - `get_url_count_model`: Fetches usage stats.
  - `promote_to_vip_service`: Updates the user's role in the database to VIP.

---

## 🔄 Request Flow Example: Shortening a URL

1. **User sends a link**: `https://example.com`
2. **Handler (`handle_message`)**:
   - Checks rate limit.
   - Validates URL format.
   - Sends "Typing..." action.
   - Calls `shorten_url_service` in a non-blocking thread.
3. **Service (`shorten_url_service`)**:
   - Retrieves/Creates user in DB.
   - Checks VIP status and limits (Max 30 for free users).
   - Sends POST request to `http://127.0.0.1:8000/url`.
4. **Response**:
   - If successful, returns the short Link and QR code.
   - Handler generates a QR code image and replies to the user.

## 🔐 Security & Resilience

- **JWT Auth**: Service-to-Service communication is secured via JWT.
- **Rate Limiting**: Prevents bot abuse.
- **Error Handling**:
  - `handle_telegram_error`: Catches Telegram API limits (Retry-After).
  - Service layer catches HTTP errors and connection timeouts.
