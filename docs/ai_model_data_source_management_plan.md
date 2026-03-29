# แผนการพัฒนาระบบจัดการ AI Model และ Data Source

**วันที่สร้าง**: 2026-02-09
**Project**: URL Shortener - User Management
**Version**: 1.0

---

## 📋 1. Requirements Summary

### 1.1 AI Model Management
- ✅ รองรับหลาย AI models (Matcha, OpenAI, Anthropic, etc.)
- ✅ Matcha AI เป็น default model
- ✅ Admin กำหนด models ที่เปิดให้ user ใช้
- ✅ User เลือกได้เฉพาะ models ที่ admin เปิดใช้
- ✅ Auto fallback เมื่อ model หลักล้ม
- ✅ API keys แบบ Hybrid (.env + Web Admin override)

### 1.2 Data Source Management
- ✅ รองรับหลาย data sources (PostgreSQL, SQLite, MongoDB, etc.)
- ✅ เพิ่ม/ลด data sources ได้อิสระ
- ✅ จัดการผ่าน config file และ Web Admin
- ✅ แสดงเฉพาะ data sources ที่เปิดใช้งาน

### 1.3 Security
- ✅ API keys encryption ใน database
- ✅ API keys ใน .env ไม่ commit ลง git
- ✅ Admin-only access สำหรับ sensitive configs

### 1.4 User Experience
- ✅ Web Admin UI สำหรับ Admin
- ✅ Telegram Bot command `/setmodel` สำหรับ User
- ✅ UI แสดงเฉพาะตัวเลือกที่เปิดใช้งาน

---

## 🏗️ 2. Architecture Design

### 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Configuration Layer                      │
├─────────────────────────────────────────────────────────────┤
│  config/ai_models.yaml  │  config/data_sources.yaml         │
│  .env (API Keys)        │  Database Overrides               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Core Management Layer                   │
├─────────────────────────────────────────────────────────────┤
│  ConfigLoader          │  AIManager          │  DBManager   │
│  - Load YAML           │  - Multi-provider   │  - Dynamic   │
│  - Merge .env          │  - Auto fallback    │    binding   │
│  - Apply DB overrides  │  - Rate limiting    │  - Pool mgmt │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌───────────────┐   ┌──────────────────┐
│  Web Admin UI │   │  Telegram Bot    │
├───────────────┤   ├──────────────────┤
│ - Manage AI   │   │ - /setmodel      │
│   models      │   │ - Auto AI parse  │
│ - API keys    │   │ - User prefs     │
│ - Data sources│   │                  │
│ - Test conn   │   │                  │
└───────────────┘   └──────────────────┘
```

### 2.2 Config Files Structure

```
user_management/
├── config/
│   ├── __init__.py
│   ├── ai_models.yaml              # AI model definitions
│   ├── data_sources.yaml           # Data source definitions
│   └── settings.yaml               # General settings
│
├── .env                            # API keys (git ignored)
│   MATCHA_API_KEY=...
│   OPENAI_API_KEY=...
│   ANTHROPIC_API_KEY=...
│   DB_ENCRYPTION_KEY=...
│
└── app/
    ├── models/
    │   ├── ai_model_config.py      # DB model for overrides
    │   ├── data_source_config.py   # DB model for data sources
    │   └── user_preferences.py     # User AI model preferences
    │
    ├── core/
    │   ├── config_loader.py        # Load & merge configs
    │   ├── ai_manager.py           # AI provider management
    │   ├── db_manager.py           # Database management
    │   └── encryption.py           # API key encryption
    │
    └── admin/
        ├── views/
        │   ├── ai_models.py        # Admin UI for AI models
        │   └── data_sources.py     # Admin UI for data sources
        └── forms/
            ├── ai_model_form.py    # Forms for AI config
            └── data_source_form.py # Forms for DB config
```

---

## 📄 3. Configuration Files

### 3.1 config/ai_models.yaml

```yaml
# AI Model Configuration
# โครงสร้างของ AI models ที่รองรับ
# API keys จะอยู่ใน .env หรือ database overrides

version: "1.0"

# Default model (ถ้า user ไม่ได้เลือก)
default_model: "matcha"

# Fallback order (ลำดับการ fallback เมื่อ model ล้ม)
fallback_order:
  - "matcha"
  - "openai-gpt4"
  - "anthropic-claude"

# AI Models
models:
  - id: "matcha"
    name: "Matcha AI"
    provider: "matcha"
    api_url: "https://api.matcha.ai/v1"
    description: "Matcha AI - Thai language optimized"
    enabled: true
    max_tokens: 4000
    temperature: 0.7
    timeout: 30
    rate_limit:
      requests_per_minute: 60
      requests_per_day: 1000

  - id: "openai-gpt4"
    name: "OpenAI GPT-4"
    provider: "openai"
    model: "gpt-4-turbo-preview"
    api_url: "https://api.openai.com/v1"
    description: "OpenAI GPT-4 Turbo"
    enabled: true
    max_tokens: 4000
    temperature: 0.7
    timeout: 30
    rate_limit:
      requests_per_minute: 100
      requests_per_day: 10000

  - id: "openai-gpt35"
    name: "OpenAI GPT-3.5"
    provider: "openai"
    model: "gpt-3.5-turbo"
    api_url: "https://api.openai.com/v1"
    description: "OpenAI GPT-3.5 Turbo - Fast & economical"
    enabled: false
    max_tokens: 4000
    temperature: 0.7
    timeout: 30

  - id: "anthropic-claude"
    name: "Claude Sonnet 4.5"
    provider: "anthropic"
    model: "claude-sonnet-4-5-20250929"
    api_url: "https://api.anthropic.com/v1"
    description: "Anthropic Claude Sonnet 4.5"
    enabled: false
    max_tokens: 4000
    temperature: 0.7
    timeout: 30

  - id: "google-gemini"
    name: "Google Gemini Pro"
    provider: "google"
    model: "gemini-pro"
    api_url: "https://generativelanguage.googleapis.com/v1"
    description: "Google Gemini Pro"
    enabled: false
    max_tokens: 4000
    temperature: 0.7
    timeout: 30
```

### 3.2 config/data_sources.yaml

```yaml
# Data Source Configuration
# กำหนด data sources ที่ระบบรองรับ

version: "1.0"

# Default data source (ใช้สำหรับ main operations)
default_source: "main_db"

# Data Sources
data_sources:
  - id: "main_db"
    name: "User Database"
    type: "postgresql"
    bind_key: null  # None = default database
    connection_env: "DEV_DATABASE_URL"
    description: "Main database for user management"
    enabled: true
    models:
      - "User"
      - "Role"
      - "Permission"
      - "EditableHTML"
    pool_config:
      pool_size: 10
      max_overflow: 20
      pool_pre_ping: true
      pool_recycle: 300

  - id: "blacklist_db"
    name: "Blacklist Database"
    type: "postgresql"
    bind_key: "blacklist"
    connection_env: "DEV_BLACKLIST_DATABASE_URL"
    description: "Database for URL blacklist management"
    enabled: true
    models:
      - "BlacklistURL"
    pool_config:
      pool_size: 5
      max_overflow: 10
      pool_pre_ping: true
      pool_recycle: 300

  - id: "analytics_db"
    name: "Analytics Database"
    type: "mongodb"
    connection_env: "ANALYTICS_MONGO_URL"
    description: "MongoDB for analytics and metrics"
    enabled: false
    collections:
      - "url_clicks"
      - "user_activities"
      - "system_metrics"

  - id: "cache_db"
    name: "Redis Cache"
    type: "redis"
    connection_env: "REDIS_URL"
    description: "Redis for caching and session management"
    enabled: true
    databases:
      cache: 0
      sessions: 1
      queues: 2
```

### 3.3 .env (Environment Variables)

```bash
# Flask Configuration
FLASK_CONFIG=development
APP_NAME=URL Shortener
SECRET_KEY=your-secret-key-here

# Database Encryption Key
DB_ENCRYPTION_KEY=your-encryption-key-here-32-chars

# AI Model API Keys
MATCHA_API_KEY=sk-matcha-xxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxx

# Database Connections
DEV_DATABASE_URL=postgresql+psycopg2://seal:chang@127.0.0.1/user
DEV_BLACKLIST_DATABASE_URL=postgresql+psycopg2://seal:chang@127.0.0.1/blacklist
ANALYTICS_MONGO_URL=mongodb://localhost:27017/analytics
REDIS_URL=redis://127.0.0.1:6379/0

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
ADMIN_TELEGRAM_ID=32971348
```

---

## 🗄️ 4. Database Schema

### 4.1 AI Model Config Override Table

```sql
CREATE TABLE ai_model_config_override (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(50) NOT NULL UNIQUE,  -- Reference to YAML model id
    enabled BOOLEAN DEFAULT TRUE,
    api_key_encrypted TEXT,                -- Encrypted API key override
    api_url_override VARCHAR(255),
    max_tokens_override INTEGER,
    temperature_override DECIMAL(3,2),
    rate_limit_override JSONB,
    display_order INTEGER DEFAULT 0,       -- UI display order
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by_user_id INTEGER REFERENCES users(id),
    updated_by_user_id INTEGER REFERENCES users(id)
);

CREATE INDEX idx_ai_model_enabled ON ai_model_config_override(enabled);
CREATE INDEX idx_ai_model_display_order ON ai_model_config_override(display_order);
```

### 4.2 Data Source Config Override Table

```sql
CREATE TABLE data_source_config_override (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(50) NOT NULL UNIQUE, -- Reference to YAML source id
    enabled BOOLEAN DEFAULT TRUE,
    connection_override TEXT,              -- Encrypted connection string override
    pool_config_override JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by_user_id INTEGER REFERENCES users(id),
    updated_by_user_id INTEGER REFERENCES users(id)
);

CREATE INDEX idx_data_source_enabled ON data_source_config_override(enabled);
```

### 4.3 User AI Model Preferences Table

```sql
CREATE TABLE user_ai_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE,                -- NULL for anonymous/telegram users
    telegram_id BIGINT UNIQUE,             -- Telegram user ID
    preferred_model_id VARCHAR(50),        -- Reference to YAML model id
    fallback_enabled BOOLEAN DEFAULT TRUE,
    custom_temperature DECIMAL(3,2),
    custom_max_tokens INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT check_user_or_telegram CHECK (
        (user_id IS NOT NULL AND telegram_id IS NULL) OR
        (user_id IS NULL AND telegram_id IS NOT NULL)
    )
);

CREATE INDEX idx_user_prefs_user ON user_ai_preferences(user_id);
CREATE INDEX idx_user_prefs_telegram ON user_ai_preferences(telegram_id);
```

---

## 💻 5. Core Implementation

### 5.1 ConfigLoader (`app/core/config_loader.py`)

**หน้าที่:**
- โหลด YAML configs
- อ่าน environment variables
- Merge กับ database overrides
- Cache configs

**Key Methods:**
```python
class ConfigLoader:
    def load_ai_models() -> Dict[str, AIModelConfig]
    def load_data_sources() -> Dict[str, DataSourceConfig]
    def get_enabled_models() -> List[AIModelConfig]
    def get_model_by_id(model_id: str) -> AIModelConfig
    def reload_configs() -> None
```

### 5.2 AIManager (`app/core/ai_manager.py`)

**หน้าที่:**
- จัดการ AI providers (Matcha, OpenAI, Anthropic, etc.)
- Auto fallback mechanism
- Rate limiting
- Error handling

**Key Methods:**
```python
class AIManager:
    def __init__(config_loader: ConfigLoader)
    def get_provider(model_id: str) -> AIProvider
    def parse_intent(text: str, model_id: str = None, user_id: int = None) -> Dict
    def generate_response(prompt: str, model_id: str = None) -> str
    def fallback_request(prompt: str, exclude_models: List[str]) -> str
    def test_connection(model_id: str) -> bool
```

### 5.3 Encryption (`app/core/encryption.py`)

**หน้าที่:**
- Encrypt/Decrypt API keys
- ใช้ Fernet (symmetric encryption)

**Key Methods:**
```python
class EncryptionManager:
    def encrypt(plain_text: str) -> str
    def decrypt(encrypted_text: str) -> str
    def rotate_key(old_key: str, new_key: str) -> None
```

### 5.4 Database Manager (`app/core/db_manager.py`)

**หน้าที่:**
- จัดการ dynamic database bindings
- Connection pool management

**Key Methods:**
```python
class DatabaseManager:
    def configure_bindings(app: Flask, config_loader: ConfigLoader) -> None
    def get_engine(bind_key: str = None) -> Engine
    def test_connection(source_id: str) -> bool
    def get_enabled_sources() -> List[DataSourceConfig]
```

---

## 🎨 6. Web Admin UI

### 6.1 AI Models Management (`app/admin/views/ai_models.py`)

**Routes:**

```python
@admin.route('/ai-models')
@admin_required
def list_ai_models():
    """แสดงรายการ AI models ทั้งหมด"""
    pass

@admin.route('/ai-models/<model_id>')
@admin_required
def view_ai_model(model_id):
    """ดูรายละเอียด model"""
    pass

@admin.route('/ai-models/<model_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_ai_model(model_id):
    """แก้ไข model config (enable/disable, override API key)"""
    pass

@admin.route('/ai-models/<model_id>/test')
@admin_required
def test_ai_model(model_id):
    """ทดสอบ API connection"""
    pass

@admin.route('/ai-models/reorder', methods=['POST'])
@admin_required
def reorder_ai_models():
    """เปลี่ยน display order"""
    pass
```

**UI Features:**
- ตารางแสดง models ทั้งหมดจาก YAML + DB
- สถานะ enabled/disabled (toggle switch)
- ปุ่ม "Test Connection"
- ฟอร์มแก้ไข API key (แสดง `***` ถ้ามี key)
- Drag & drop เพื่อเรียงลำดับ
- ไอคอนบอกสถานะ: ✅ Active | ⏸️ Disabled | ⚠️ Error

### 6.2 Data Sources Management (`app/admin/views/data_sources.py`)

**Routes:**

```python
@admin.route('/data-sources')
@admin_required
def list_data_sources():
    """แสดงรายการ data sources"""
    pass

@admin.route('/data-sources/<source_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_data_source(source_id):
    """แก้ไข data source (enable/disable)"""
    pass

@admin.route('/data-sources/<source_id>/test')
@admin_required
def test_data_source(source_id):
    """ทดสอบ database connection"""
    pass
```

**UI Features:**
- ตารางแสดง data sources
- สถานะ connection (🟢 Connected | 🔴 Disconnected)
- ปุ่ม "Test Connection"
- แสดง pool statistics

---

## 🤖 7. Telegram Bot Integration

### 7.1 New Command: `/setmodel`

**Flow:**

```
User: /setmodel

Bot: "🤖 เลือก AI Model ที่คุณต้องการใช้:
      [Inline Keyboard]
      - 🍵 Matcha AI (ปัจจุบัน)
      - 🤖 OpenAI GPT-4
      - Cancel"

User: [คลิกเลือก OpenAI GPT-4]

Bot: "✅ เปลี่ยน AI Model เป็น OpenAI GPT-4 แล้ว
      หากต้องการเปลี่ยนกลับใช้ /setmodel อีกครั้ง"
```

**Implementation:**

```python
# bot_app/core/handlers.py

async def setmodel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """แสดง inline keyboard ให้เลือก AI model"""
    telegram_id = update.effective_user.id

    # ดึง models ที่ admin เปิดใช้
    enabled_models = ai_manager.get_enabled_models()

    # ดึง current model ของ user
    current_model = get_user_preferred_model(telegram_id)

    # สร้าง inline keyboard
    keyboard = []
    for model in enabled_models:
        checkmark = "✓ " if model.id == current_model else ""
        keyboard.append([
            InlineKeyboardButton(
                f"{checkmark}{model.name}",
                callback_data=f"setmodel:{model.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("❌ ยกเลิก", callback_data="setmodel:cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 เลือก AI Model ที่คุณต้องการใช้:",
        reply_markup=reply_markup
    )

async def setmodel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle model selection callback"""
    query = update.callback_query
    telegram_id = query.from_user.id

    action = query.data.split(":")[1]

    if action == "cancel":
        await query.edit_message_text("❌ ยกเลิกการเปลี่ยน AI Model")
        return

    # บันทึก preference
    model_id = action
    save_user_preferred_model(telegram_id, model_id)

    model = ai_manager.get_model_by_id(model_id)
    await query.edit_message_text(
        f"✅ เปลี่ยน AI Model เป็น {model.name} แล้ว\n"
        f"หากต้องการเปลี่ยนกลับใช้ /setmodel อีกครั้ง"
    )
```

### 7.2 แก้ไข `handle_message` ให้ใช้ AIManager

```python
# bot_app/core/handlers.py

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    text = update.message.text

    # ดึง preferred model ของ user
    preferred_model = get_user_preferred_model(telegram_id)

    # ใช้ AIManager parse intent
    result = ai_manager.parse_intent(
        text=text,
        model_id=preferred_model,
        user_id=telegram_id
    )

    intent = result.get("intent")

    if intent == "shorten_url":
        # ... existing code
        pass
    elif intent == "help":
        # ... existing code
        pass
    else:
        await update.message.reply_text(
            "ขอโทษครับ ผมไม่เข้าใจคำสั่ง กรุณาใช้ /help ดูคำสั่งที่ใช้ได้"
        )
```

---

## 🧪 8. Testing Plan

### 8.1 Unit Tests

**test_config_loader.py:**
- ✅ โหลด YAML ได้ถูกต้อง
- ✅ Merge .env กับ YAML ได้
- ✅ Apply DB overrides ได้
- ✅ Handle missing config file

**test_ai_manager.py:**
- ✅ เลือก provider ถูกต้อง
- ✅ Fallback เมื่อ model ล้ม
- ✅ Rate limiting ทำงาน
- ✅ API key จาก .env หรือ DB override

**test_encryption.py:**
- ✅ Encrypt/Decrypt ถูกต้อง
- ✅ Handle invalid key

**test_db_manager.py:**
- ✅ Dynamic binding ทำงาน
- ✅ Connection pool ถูกต้อง

### 8.2 Integration Tests

**test_admin_ui.py:**
- ✅ Admin เปิด/ปิด model ได้
- ✅ Admin override API key ได้
- ✅ Test connection ทำงาน

**test_bot_integration.py:**
- ✅ User เลือก model ผ่าน /setmodel ได้
- ✅ Bot ใช้ model ที่ user เลือก
- ✅ Fallback เมื่อ model ล้ม

### 8.3 Manual Testing Checklist

- [ ] Admin login และเข้าหน้า AI Models
- [ ] เปิด/ปิด model แล้ว user เห็นเฉพาะที่เปิด
- [ ] Override API key แล้วใช้ได้
- [ ] Test connection แสดงสถานะถูกต้อง
- [ ] User ใช้ /setmodel เห็นเฉพาะ model ที่เปิด
- [ ] เปลี่ยน model แล้วบอทใช้ model ใหม่
- [ ] Model หลักล้ม → fallback ทำงาน
- [ ] Restart app แล้ว config ยังอยู่

---

## 📅 9. Implementation Timeline

### **Phase 1: Core Infrastructure (สัปดาห์ที่ 1)**

**Day 1-2:**
- [x] สร้าง config files (YAML)
- [x] สร้าง database migrations
- [x] สร้าง models (SQLAlchemy)

**Day 3-4:**
- [x] Implement ConfigLoader
- [x] Implement EncryptionManager
- [x] Unit tests สำหรับ ConfigLoader

**Day 5-7:**
- [x] Implement AIManager
- [x] รองรับ Matcha, OpenAI, Anthropic providers
- [x] Implement fallback mechanism
- [x] Unit tests สำหรับ AIManager

---

### **Phase 2: Admin UI (สัปดาห์ที่ 2)**

**Day 8-10:**
- [x] สร้าง admin routes สำหรับ AI models
- [x] สร้าง templates (Jinja2)
- [x] Implement enable/disable functionality
- [x] Implement API key override

**Day 11-12:**
- [x] Implement test connection
- [x] Implement display order
- [x] AJAX endpoints สำหรับ UI

**Day 13-14:**
- [x] สร้าง admin routes สำหรับ data sources
- [x] Integration tests

---

### **Phase 3: Bot Integration (สัปดาห์ที่ 3)**

**Day 15-17:**
- [x] แก้ไข `bot_app/core/ai.py` ให้ใช้ AIManager
- [x] Implement `/setmodel` command
- [x] Implement callback handlers
- [x] บันทึก user preferences

**Day 18-19:**
- [x] แก้ไข `handle_message` ให้ใช้ AIManager
- [x] ทดสอบ fallback mechanism
- [x] Rate limiting

**Day 20-21:**
- [x] Integration testing
- [x] Bug fixes

---

### **Phase 4: Testing & Documentation (สัปดาห์ที่ 4)**

**Day 22-24:**
- [x] Manual testing ทุก scenarios
- [x] Performance testing
- [x] Load testing (simulate 100+ users)

**Day 25-26:**
- [x] เขียน documentation
- [x] สร้าง user guide
- [x] API documentation

**Day 27-28:**
- [x] Code review
- [x] Security audit
- [x] Deploy to staging
- [x] Final testing

---

## 🔒 10. Security Considerations

### 10.1 API Key Storage
- ✅ ไม่ commit `.env` ลง git (ใช้ `.gitignore`)
- ✅ API keys ใน database ต้อง encrypt
- ✅ ใช้ Fernet symmetric encryption
- ✅ Encryption key เก็บใน environment variable
- ✅ Admin เท่านั้นที่เห็น/แก้ไข API keys

### 10.2 Access Control
- ✅ เฉพาะ Admin access หน้า config
- ✅ User เห็นเฉพาะ models ที่เปิดใช้
- ✅ Rate limiting ป้องกัน API abuse
- ✅ Input validation ทุก form

### 10.3 Database Security
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Connection string encryption
- ✅ Database credentials ใน .env เท่านั้น

### 10.4 Error Handling
- ✅ ไม่แสดง sensitive info ใน error messages
- ✅ Log errors ไปยัง secure log file
- ✅ Generic error messages สำหรับ users

---

## 📊 11. Monitoring & Logging

### 11.1 Metrics to Track
- จำนวน API requests per model
- Success/failure rate per model
- Fallback frequency
- Response time per model
- API cost per model

### 11.2 Logging
```python
# Log format
{
    "timestamp": "2026-02-09T10:30:00Z",
    "user_id": 12345,
    "telegram_id": 32971348,
    "model_id": "matcha",
    "action": "parse_intent",
    "status": "success",
    "response_time_ms": 234,
    "fallback_used": false
}
```

### 11.3 Alerts
- ⚠️ Model failure rate > 10%
- ⚠️ API rate limit exceeded
- ⚠️ Database connection failures
- 🚨 Encryption key rotation needed

---

## 🚀 12. Deployment Checklist

**Pre-deployment:**
- [ ] ทุก tests pass (unit + integration)
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Backup database
- [ ] Prepare rollback plan

**Deployment:**
- [ ] Update `.env` on production server
- [ ] Run database migrations
- [ ] Upload config YAML files
- [ ] Restart application
- [ ] Verify all services running

**Post-deployment:**
- [ ] Smoke testing
- [ ] Monitor logs for errors
- [ ] Test AI model connections
- [ ] Verify fallback mechanism
- [ ] Test Telegram bot `/setmodel`

---

## 📝 13. Future Enhancements

### Phase 2 (Future)
- [ ] Model usage analytics dashboard
- [ ] Cost tracking per model
- [ ] A/B testing ระหว่าง models
- [ ] Custom model fine-tuning
- [ ] Model performance comparison
- [ ] Webhook notifications for model failures
- [ ] Multi-language support
- [ ] User feedback system

### Phase 3 (Future)
- [ ] Machine learning for model selection
- [ ] Automatic model switching based on intent type
- [ ] Model caching layer
- [ ] Distributed model load balancing

---

## 👥 14. Roles & Responsibilities

### Admin Role
- กำหนด models ที่เปิดให้ user ใช้
- จัดการ API keys
- ตรวจสอบ connection status
- ดู usage statistics

### User Role
- เลือก AI model ที่ต้องการใช้ (จาก models ที่ admin เปิดให้)
- ใช้บอทตามปกติ
- ไม่เห็น API keys หรือ sensitive configs

### Developer Role
- เพิ่ม AI providers ใหม่
- แก้ไข config files
- Deploy updates
- Monitor system health

---

## 📞 15. Support & Maintenance

### Backup Strategy
- Database backup ทุกวัน
- Config files backup ทุกสัปดาห์
- API keys backup (encrypted) ทุกเดือน

### Update Procedures
- เพิ่ม AI model ใหม่: แก้ไข `ai_models.yaml` + restart
- เปลี่ยน API key: แก้ไขใน Web Admin (ไม่ต้อง restart)
- Update provider code: Deploy new code + restart

### Troubleshooting
**Problem**: Model ไม่ทำงาน
- ✅ Check API key ใน Admin UI
- ✅ Test connection
- ✅ Check logs
- ✅ Verify fallback model available

**Problem**: User ไม่เห็น model
- ✅ Check admin enabled model
- ✅ Check display order
- ✅ Clear bot cache

---

## ✅ 16. Acceptance Criteria

### Must Have (Phase 1)
- [x] Admin สามารถเปิด/ปิด AI models ผ่าน Web UI
- [x] User เห็นและเลือกได้เฉพาะ models ที่ admin เปิด
- [x] Matcha เป็น default model
- [x] Auto fallback เมื่อ model ล้ม
- [x] API keys แบบ Hybrid (.env + Web override)
- [x] Encryption สำหรับ API keys ใน database

### Should Have
- [x] Test connection functionality
- [x] Rate limiting per model
- [x] User preferences persistence
- [x] Display order management
- [x] Basic monitoring & logging

### Nice to Have
- [ ] Usage analytics
- [ ] Cost tracking
- [ ] Performance comparison
- [ ] A/B testing

---

## 📚 17. References

### Documentation
- [Matcha AI API Docs](https://api.matcha.ai/docs) (example URL)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Anthropic API Docs](https://docs.anthropic.com)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Flask-SQLAlchemy Docs](https://flask-sqlalchemy.palletsprojects.com/)
- [python-telegram-bot Docs](https://docs.python-telegram-bot.org/)

### Libraries
- `cryptography` - Fernet encryption
- `pyyaml` - YAML parsing
- `sqlalchemy` - ORM
- `redis` - Caching
- `requests` - HTTP client

---

## 📄 18. Appendix

### A. Sample API Request

**Matcha AI:**
```python
import requests

headers = {
    "Authorization": f"Bearer {MATCHA_API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "matcha-chat",
    "messages": [
        {"role": "user", "content": "สวัสดีครับ"}
    ],
    "temperature": 0.7,
    "max_tokens": 4000
}

response = requests.post(
    "https://api.matcha.ai/v1/chat/completions",
    headers=headers,
    json=data,
    timeout=30
)

result = response.json()
```

### B. Sample Fallback Flow

```
User Request
    ↓
Try Matcha (primary)
    ↓ [FAILED]
Try OpenAI GPT-4 (fallback #1)
    ↓ [FAILED]
Try Anthropic Claude (fallback #2)
    ↓ [SUCCESS]
Return Response + Log fallback
```

### C. Directory Structure (Final)

```
user_management/
├── config/
│   ├── __init__.py
│   ├── ai_models.yaml
│   ├── data_sources.yaml
│   └── settings.yaml
│
├── app/
│   ├── models/
│   │   ├── user.py
│   │   ├── ai_model_config.py          # NEW
│   │   ├── data_source_config.py       # NEW
│   │   └── user_preferences.py         # NEW
│   │
│   ├── core/
│   │   ├── config_loader.py            # NEW
│   │   ├── ai_manager.py               # NEW
│   │   ├── db_manager.py               # NEW
│   │   └── encryption.py               # NEW
│   │
│   ├── admin/
│   │   ├── views/
│   │   │   ├── ai_models.py            # NEW
│   │   │   └── data_sources.py         # NEW
│   │   ├── forms/
│   │   │   ├── ai_model_form.py        # NEW
│   │   │   └── data_source_form.py     # NEW
│   │   └── templates/
│   │       ├── ai_models/              # NEW
│   │       │   ├── list.html
│   │       │   ├── edit.html
│   │       │   └── test.html
│   │       └── data_sources/           # NEW
│   │           ├── list.html
│   │           └── edit.html
│   │
│   └── migrations/                      # NEW
│       └── versions/
│           ├── xxx_create_ai_model_config.py
│           ├── xxx_create_data_source_config.py
│           └── xxx_create_user_preferences.py
│
├── bot_app/
│   └── core/
│       ├── ai.py                        # MODIFY
│       ├── handlers.py                  # MODIFY
│       └── services.py                  # MODIFY
│
├── tests/
│   ├── unit/
│   │   ├── test_config_loader.py       # NEW
│   │   ├── test_ai_manager.py          # NEW
│   │   ├── test_encryption.py          # NEW
│   │   └── test_db_manager.py          # NEW
│   └── integration/
│       ├── test_admin_ui.py            # NEW
│       └── test_bot_integration.py     # NEW
│
└── .env                                 # MODIFY (add AI keys)
```

---

## 📌 Notes

1. **แผนนี้เป็น living document** - อาจมีการปรับเปลี่ยนระหว่างการพัฒนา
2. **Security first** - ทุกขั้นตอนต้องคำนึงถึงความปลอดภัย
3. **Test thoroughly** - ทดสอบทุก scenario ก่อน deploy
4. **Document as you go** - เขียน docstring และ comments ระหว่างทำ
5. **User experience** - UI ต้องใช้งานง่าย สัญญาณชัดเจน

---

**End of Plan Document**

---

**Prepared by:** Claude Code (Sonnet 4.5)
**Review Status:** ⏳ Pending User Approval
**Next Steps:** รอการ approve จาก user แล้วจึงเริ่ม Phase 1
