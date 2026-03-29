# API Platform Development Plan

แผนพัฒนา URL API Platform แบบ API Key as a Service

## Executive Summary

สร้าง API Platform ใหม่ที่รวม:
- URL Shortener (จาก shortener_app)
- URL Scanner (จาก check_url)
- SMS URL Extraction (ใหม่)
- Scaling Architecture (จาก scale_api)

พร้อมระบบ Billing และ Developer Portal

---

## 1. สิ่งที่มีอยู่แล้ว (Existing Assets)

### 1.1 shortener_app (FastAPI)
| Component | Status | Reuse |
|-----------|--------|-------|
| URL Shortening | ✅ Production | ใช้ logic เดิม |
| QR Code Generation | ✅ Production | ใช้เลย |
| Phishing Detection | ✅ Production | ย้ายมา |
| Click Tracking | ✅ Production | ใช้เลย |
| API Key Auth | ⚠️ Basic | ปรับปรุง |

### 1.2 check_url (FastAPI)
| Component | Status | Reuse |
|-----------|--------|-------|
| Multi-source Scanning | ✅ Production | ย้ายมาเป็น service |
| Google Web Risk | ✅ Integrated | ใช้เลย |
| VirusTotal | ✅ Integrated | ใช้เลย |
| PhishTank/URLhaus | ✅ Integrated | ใช้เลย |
| Batch Scanning | ✅ Production | ใช้เลย |
| Background Worker | ✅ Production | ปรับให้เป็น Celery |

### 1.3 scale_api (Architecture) ⭐
| Component | Status | Reuse |
|-----------|--------|-------|
| Async FastAPI | ✅ Production | **ใช้เป็น base** |
| Redis Cache Layer | ✅ Production | **ใช้เลย** |
| PostgreSQL Async | ✅ Production | **ใช้เลย** |
| Real-time Sync (PG Notify) | ✅ Production | **ใช้เลย** |
| Celery Workers | ✅ Ready | **ใช้เลย** |
| Cache-First Strategy | ✅ Implemented | **ใช้เลย** |

### 1.4 user_management (Flask)
| Component | Status | Reuse |
|-----------|--------|-------|
| User Registration | ✅ Production | อ้างอิง logic |
| Email Verification | ✅ Production | ย้ายมา |
| Role Management | ✅ Production | ปรับปรุง |

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LOAD BALANCER                                   │
│                            (Nginx / Traefik)                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │  FastAPI #1  │ │  FastAPI #2  │ │  FastAPI #3  │
            │  (Async)     │ │  (Async)     │ │  (Async)     │
            └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
                   │                │                │
                   └────────────────┼────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
   ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
   │    Redis    │          │ PostgreSQL  │          │   Celery    │
   │   (Cache)   │◀────────▶│  (Primary)  │─────────▶│  Workers    │
   │             │  PG      │             │  Queue   │             │
   │ • URL Cache │  Notify  │ • Users     │          │ • Scanning  │
   │ • Sessions  │          │ • API Keys  │          │ • Billing   │
   │ • Rate Limit│          │ • URLs      │          │ • Analytics │
   └─────────────┘          │ • Usage     │          └─────────────┘
                            │ • Billing   │
                            └─────────────┘
```

### 2.1 ใช้ Pattern จาก scale_api

```python
# Cache-First Strategy (จาก scale_api)
async def get_url(key: str):
    # 1. Check Redis first
    cached = await redis.get(f"url:{key}")
    if cached:
        return json.loads(cached)

    # 2. Fallback to PostgreSQL
    url = await db.get_url(key)

    # 3. Cache for next time
    await redis.set(f"url:{key}", json.dumps(url))

    return url
```

```python
# Real-time Sync (จาก scale_api)
# PostgreSQL Trigger → Notify → Redis Update

CREATE TRIGGER url_change_trigger
AFTER INSERT OR UPDATE ON urls
FOR EACH ROW EXECUTE FUNCTION notify_url_change();

# FastAPI listener auto-updates Redis
```

---

## 3. Project Structure

```
url-api-platform/
│
├── docker-compose.yml              # All services
├── docker-compose.dev.yml          # Development overrides
├── docker-compose.prod.yml         # Production overrides
├── .env.example
├── Makefile                        # Common commands
│
├── api/                            # Main API Service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/                    # Database migrations
│   │   └── versions/
│   │
│   └── app/
│       ├── main.py                 # FastAPI entry (async, from scale_api)
│       ├── config.py               # Settings (Pydantic)
│       ├── database.py             # Async PostgreSQL (from scale_api)
│       ├── cache.py                # Redis cache layer (from scale_api)
│       ├── listener.py             # PG Notify listener (from scale_api)
│       │
│       ├── api/
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── router.py       # Main router
│       │       ├── auth.py         # Registration, Login, OAuth
│       │       ├── api_keys.py     # API Key CRUD
│       │       ├── urls.py         # URL Shortening (from shortener_app)
│       │       ├── scanner.py      # URL/SMS Scanning (from check_url)
│       │       ├── billing.py      # Subscription & Payment
│       │       ├── usage.py        # Usage statistics
│       │       └── webhooks.py     # Webhook management
│       │
│       ├── core/
│       │   ├── security.py         # JWT, API Key hashing
│       │   ├── rate_limiter.py     # Per-tier rate limiting
│       │   ├── usage_tracker.py    # Middleware for tracking
│       │   └── permissions.py      # Plan-based permissions
│       │
│       ├── models/                 # SQLAlchemy models
│       │   ├── user.py
│       │   ├── api_key.py
│       │   ├── subscription.py
│       │   ├── usage.py
│       │   ├── url.py              # From shortener_app
│       │   └── scan.py             # From check_url
│       │
│       ├── schemas/                # Pydantic schemas
│       │   └── ...
│       │
│       └── services/               # Business logic
│           ├── shortener.py        # From shortener_app
│           ├── scanner.py          # From check_url
│           ├── sms_parser.py       # New: SMS URL extraction
│           ├── qr_generator.py     # From shortener_app
│           ├── payment.py          # Stripe + PromptPay
│           └── email.py            # Transactional emails
│
├── workers/                        # Celery Workers (from scale_api)
│   ├── Dockerfile
│   ├── celery_app.py              # Celery config (from scale_api)
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── scanning.py            # URL scanning tasks
│   │   ├── billing.py             # Subscription tasks
│   │   ├── usage.py               # Usage aggregation
│   │   └── notifications.py       # Email, Webhook tasks
│   └── beat_schedule.py           # Periodic tasks
│
├── portal/                         # Developer Portal (Frontend)
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── pages/
│       │   ├── index.tsx          # Landing page
│       │   ├── dashboard.tsx      # Main dashboard
│       │   ├── api-keys.tsx       # API Key management
│       │   ├── usage.tsx          # Usage analytics
│       │   ├── billing.tsx        # Subscription & invoices
│       │   └── docs.tsx           # API documentation
│       └── components/
│
├── admin/                          # Admin Dashboard (Optional)
│   └── ...
│
├── docs/                           # Documentation
│   ├── api/
│   │   ├── openapi.yaml
│   │   └── examples/
│   ├── guides/
│   │   ├── quickstart.md
│   │   └── authentication.md
│   └── architecture/
│
├── scripts/                        # Utility scripts
│   ├── migrate.sh
│   ├── seed.sh
│   └── backup.sh
│
└── tests/
    ├── api/
    ├── workers/
    └── integration/
```

---

## 4. Database Schema

### 4.1 Core Tables

```sql
-- ============================================
-- USERS & AUTHENTICATION
-- ============================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(100),
    company VARCHAR(100),

    -- OAuth
    google_id VARCHAR(100),
    github_id VARCHAR(100),

    -- Status
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- ============================================
-- API KEYS
-- ============================================

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Key data (store hash, not plain text)
    key_prefix VARCHAR(8) NOT NULL,      -- First 8 chars for display
    key_hash VARCHAR(64) NOT NULL,        -- SHA256 hash

    -- Metadata
    name VARCHAR(100) NOT NULL,           -- "Production", "Testing"
    description TEXT,

    -- Permissions
    permissions JSONB DEFAULT '["read", "write"]',
    allowed_ips JSONB,                    -- IP whitelist (optional)
    allowed_domains JSONB,                -- Domain whitelist (optional)

    -- Rate limit override (null = use plan default)
    rate_limit_per_minute INTEGER,
    rate_limit_per_day INTEGER,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ,

    -- Usage
    last_used_at TIMESTAMPTZ,
    total_requests BIGINT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user ON api_keys(user_id);

-- ============================================
-- SUBSCRIPTIONS & BILLING
-- ============================================

CREATE TYPE plan_type AS ENUM ('free', 'starter', 'pro', 'enterprise');
CREATE TYPE subscription_status AS ENUM ('active', 'cancelled', 'past_due', 'trialing');

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- Plan
    plan plan_type DEFAULT 'free',
    status subscription_status DEFAULT 'active',

    -- Billing period
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,

    -- Payment provider
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100),

    -- Metadata
    cancelled_at TIMESTAMPTZ,
    cancel_reason TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    subscription_id UUID REFERENCES subscriptions(id),

    -- Amount
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'THB',

    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, paid, failed
    paid_at TIMESTAMPTZ,

    -- Payment
    payment_method VARCHAR(50),            -- stripe, promptpay
    payment_reference VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    due_date TIMESTAMPTZ
);

-- ============================================
-- USAGE TRACKING
-- ============================================

CREATE TABLE usage_logs (
    id BIGSERIAL PRIMARY KEY,
    api_key_id UUID REFERENCES api_keys(id),

    -- Request info
    endpoint VARCHAR(100),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,

    -- Client info
    ip_address INET,
    user_agent TEXT,

    -- Timestamp (partitioned by month)
    created_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE usage_logs_2024_01 PARTITION OF usage_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
-- ... more partitions

CREATE TABLE usage_daily (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    date DATE NOT NULL,

    -- Counts
    total_requests INTEGER DEFAULT 0,
    urls_created INTEGER DEFAULT 0,
    urls_scanned INTEGER DEFAULT 0,
    sms_scanned INTEGER DEFAULT 0,

    -- Bandwidth
    bandwidth_bytes BIGINT DEFAULT 0,

    UNIQUE(user_id, date)
);

-- ============================================
-- URLs (from shortener_app)
-- ============================================

CREATE TABLE urls (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),

    -- URL data
    key VARCHAR(15) UNIQUE NOT NULL,
    secret_key VARCHAR(30) UNIQUE NOT NULL,
    target_url TEXT NOT NULL,

    -- Custom alias
    custom_key VARCHAR(50),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Scan status
    is_checked BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'pending',  -- safe, danger, unknown

    -- Metadata
    title VARCHAR(255),
    favicon_url VARCHAR(500),

    -- Stats
    clicks BIGINT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX idx_urls_key ON urls(key);
CREATE INDEX idx_urls_user ON urls(user_id);
CREATE INDEX idx_urls_created ON urls(created_at);

-- ============================================
-- SCAN RECORDS (from check_url)
-- ============================================

CREATE TABLE scan_records (
    id BIGSERIAL PRIMARY KEY,
    url_id BIGINT REFERENCES urls(id),
    url TEXT NOT NULL,

    -- Scan results
    overall_status VARCHAR(20),  -- safe, danger, unknown

    -- Per-scanner results
    google_result VARCHAR(50),
    virustotal_result VARCHAR(50),
    phishtank_result VARCHAR(50),
    urlhaus_result VARCHAR(50),

    -- Metadata
    scan_duration_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- WEBHOOKS
-- ============================================

CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Webhook config
    url TEXT NOT NULL,
    secret VARCHAR(64),                    -- For signature verification

    -- Events to send
    events JSONB DEFAULT '["url.created", "url.clicked", "scan.completed"]',

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMPTZ,
    failure_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- TRIGGERS (from scale_api)
-- ============================================

CREATE OR REPLACE FUNCTION notify_url_change()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('url_change', json_build_object(
        'action', TG_OP,
        'key', NEW.key,
        'data', row_to_json(NEW)
    )::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER url_change_trigger
AFTER INSERT OR UPDATE ON urls
FOR EACH ROW EXECUTE FUNCTION notify_url_change();
```

### 4.2 Plan Limits Configuration

```sql
CREATE TABLE plan_limits (
    plan plan_type PRIMARY KEY,

    -- Request limits
    requests_per_minute INTEGER,
    requests_per_day INTEGER,

    -- Feature limits
    max_urls INTEGER,
    max_api_keys INTEGER,
    max_webhooks INTEGER,

    -- Features
    custom_alias BOOLEAN DEFAULT FALSE,
    analytics_basic BOOLEAN DEFAULT FALSE,
    analytics_advanced BOOLEAN DEFAULT FALSE,
    webhook_enabled BOOLEAN DEFAULT FALSE,
    priority_support BOOLEAN DEFAULT FALSE,

    -- Price (THB)
    price_monthly_cents INTEGER,
    price_yearly_cents INTEGER
);

INSERT INTO plan_limits VALUES
('free',       60,    1000,    30,   2,  0,  FALSE, FALSE, FALSE, FALSE, FALSE, 0,      0),
('starter',    300,   10000,   500,  5,  2,  TRUE,  TRUE,  FALSE, FALSE, FALSE, 19900,  199000),
('pro',        1000,  100000,  5000, 20, 10, TRUE,  TRUE,  TRUE,  TRUE,  FALSE, 59900,  599000),
('enterprise', NULL,  NULL,    NULL, NULL, NULL, TRUE, TRUE, TRUE, TRUE, TRUE,  NULL,   NULL);
```

---

## 5. API Endpoints Design

### 5.1 Public Endpoints

```
# Health & Info
GET  /health                    Health check
GET  /                          API info

# URL Redirect (no auth)
GET  /{key}                     Redirect to target URL
GET  /{key}+                    Preview URL info
```

### 5.2 Authentication

```
# Registration & Login
POST /v1/auth/register          Register with email
POST /v1/auth/verify-email      Verify email with OTP
POST /v1/auth/login             Login (email + password)
POST /v1/auth/logout            Logout
POST /v1/auth/refresh           Refresh access token
POST /v1/auth/forgot-password   Request password reset
POST /v1/auth/reset-password    Reset password

# OAuth
GET  /v1/auth/google            Google OAuth redirect
GET  /v1/auth/google/callback   Google OAuth callback
GET  /v1/auth/github            GitHub OAuth redirect
GET  /v1/auth/github/callback   GitHub OAuth callback
```

### 5.3 API Keys (JWT Required)

```
GET    /v1/api-keys             List all API keys
POST   /v1/api-keys             Create new API key
GET    /v1/api-keys/{id}        Get API key details
PATCH  /v1/api-keys/{id}        Update API key
DELETE /v1/api-keys/{id}        Revoke API key
POST   /v1/api-keys/{id}/rotate Rotate API key
```

### 5.4 URL Shortening (API Key Required)

```
POST   /v1/urls                 Create short URL
GET    /v1/urls                 List user's URLs
GET    /v1/urls/{id}            Get URL details
PATCH  /v1/urls/{id}            Update URL
DELETE /v1/urls/{id}            Delete URL

GET    /v1/urls/{id}/stats      Get URL click stats
GET    /v1/urls/{id}/clicks     Get click details (Pro+)
```

### 5.5 URL Scanning (API Key Required)

```
POST   /v1/scan/url             Scan single URL
POST   /v1/scan/batch           Scan multiple URLs (max 10)
GET    /v1/scan/{id}            Get scan result
GET    /v1/scan/history         Get scan history

POST   /v1/scan/sms             Extract & scan URLs from SMS
```

### 5.6 Billing (JWT Required)

```
GET    /v1/billing/subscription     Get current subscription
POST   /v1/billing/subscribe        Subscribe to plan
POST   /v1/billing/cancel           Cancel subscription
GET    /v1/billing/invoices         List invoices
GET    /v1/billing/invoices/{id}    Get invoice details
POST   /v1/billing/payment-method   Update payment method

# PromptPay
POST   /v1/billing/promptpay/create Create PromptPay QR
POST   /v1/billing/promptpay/verify Verify payment
```

### 5.7 Usage & Analytics (JWT Required)

```
GET    /v1/usage/summary        Usage summary
GET    /v1/usage/daily          Daily usage breakdown
GET    /v1/usage/endpoints      Per-endpoint breakdown
```

### 5.8 Webhooks (Pro+ Only)

```
GET    /v1/webhooks             List webhooks
POST   /v1/webhooks             Create webhook
PATCH  /v1/webhooks/{id}        Update webhook
DELETE /v1/webhooks/{id}        Delete webhook
POST   /v1/webhooks/{id}/test   Test webhook
```

---

## 6. Rate Limiting Strategy

### 6.1 Per-Plan Limits

```python
RATE_LIMITS = {
    "free": {
        "per_minute": 60,
        "per_hour": 500,
        "per_day": 1000,
    },
    "starter": {
        "per_minute": 300,
        "per_hour": 5000,
        "per_day": 10000,
    },
    "pro": {
        "per_minute": 1000,
        "per_hour": 20000,
        "per_day": 100000,
    },
    "enterprise": {
        "per_minute": None,  # Unlimited
        "per_hour": None,
        "per_day": None,
    }
}
```

### 6.2 Implementation (Redis-based)

```python
# Using Redis for distributed rate limiting
async def check_rate_limit(api_key: str, plan: str) -> bool:
    limits = RATE_LIMITS[plan]
    now = int(time.time())

    pipe = redis.pipeline()

    # Check minute limit
    minute_key = f"rate:{api_key}:min:{now // 60}"
    pipe.incr(minute_key)
    pipe.expire(minute_key, 60)

    # Check day limit
    day_key = f"rate:{api_key}:day:{now // 86400}"
    pipe.incr(day_key)
    pipe.expire(day_key, 86400)

    results = await pipe.execute()

    minute_count = results[0]
    day_count = results[2]

    if limits["per_minute"] and minute_count > limits["per_minute"]:
        return False
    if limits["per_day"] and day_count > limits["per_day"]:
        return False

    return True
```

---

## 7. Payment Integration

### 7.1 Stripe (International)

```python
# Subscribe to plan
@router.post("/billing/subscribe")
async def subscribe(plan: PlanType, payment_method_id: str):
    # Create Stripe subscription
    subscription = stripe.Subscription.create(
        customer=user.stripe_customer_id,
        items=[{"price": STRIPE_PRICES[plan]}],
        default_payment_method=payment_method_id,
    )

    # Update database
    await db.update_subscription(user.id, plan, subscription.id)

    return {"subscription_id": subscription.id}
```

### 7.2 PromptPay (Thailand)

```python
# Generate PromptPay QR
@router.post("/billing/promptpay/create")
async def create_promptpay(plan: PlanType):
    amount = PLAN_PRICES[plan]

    # Create pending invoice
    invoice = await db.create_invoice(user.id, amount, "promptpay")

    # Generate QR code
    qr_data = generate_promptpay_qr(
        phone="0812345678",  # PromptPay ID
        amount=amount,
        ref=invoice.id
    )

    return {
        "invoice_id": invoice.id,
        "qr_code": qr_data,
        "amount": amount,
        "expires_in": 3600  # 1 hour
    }

# Verify payment (webhook from bank or manual)
@router.post("/billing/promptpay/verify")
async def verify_promptpay(invoice_id: str, slip_image: UploadFile):
    # Verify slip (OCR or manual review)
    # Update subscription on success
    pass
```

---

## 8. Development Phases

### Phase 1: Core Platform (Week 1-3)

```
Week 1: Project Setup
├── [ ] Create project structure
├── [ ] Setup Docker Compose (PostgreSQL, Redis)
├── [ ] Setup FastAPI with async (from scale_api)
├── [ ] Setup Alembic migrations
├── [ ] Implement database models
└── [ ] Setup Redis cache layer (from scale_api)

Week 2: Authentication & API Keys
├── [ ] User registration with email verification
├── [ ] Login/Logout with JWT
├── [ ] API Key generation (hashed storage)
├── [ ] API Key validation middleware
├── [ ] Rate limiting (Redis-based)
└── [ ] Usage tracking middleware

Week 3: URL Shortening
├── [ ] Migrate URL shortening logic (from shortener_app)
├── [ ] QR Code generation
├── [ ] Click tracking
├── [ ] PostgreSQL Notify integration (from scale_api)
├── [ ] Redis cache sync
└── [ ] Basic URL management (list, delete)
```

### Phase 2: Features & Portal (Week 4-6)

```
Week 4: URL Scanning
├── [ ] Migrate scanning logic (from check_url)
├── [ ] Setup Celery workers
├── [ ] Implement batch scanning
├── [ ] SMS URL extraction (new)
└── [ ] Webhook notifications

Week 5: Developer Portal (Frontend)
├── [ ] Setup Next.js project
├── [ ] Dashboard page
├── [ ] API Keys management
├── [ ] Usage statistics
├── [ ] API Documentation page
└── [ ] Authentication UI

Week 6: Testing & Documentation
├── [ ] API tests (pytest)
├── [ ] Integration tests
├── [ ] Load testing (locust)
├── [ ] OpenAPI documentation
├── [ ] Developer guides
└── [ ] Deployment documentation
```

### Phase 3: Billing & Production (Week 7-9)

```
Week 7: Billing System
├── [ ] Stripe integration
├── [ ] PromptPay integration
├── [ ] Subscription management
├── [ ] Invoice generation
├── [ ] Payment webhook handlers
└── [ ] Billing UI in portal

Week 8: Advanced Features
├── [ ] Advanced analytics (Pro+)
├── [ ] Webhook management
├── [ ] Custom domain support (Enterprise)
├── [ ] Admin dashboard
└── [ ] Email notifications

Week 9: Production Deployment
├── [ ] Kubernetes manifests
├── [ ] CI/CD pipeline (GitHub Actions)
├── [ ] Monitoring (Prometheus + Grafana)
├── [ ] Logging (ELK Stack)
├── [ ] SSL/TLS setup
├── [ ] Performance optimization
└── [ ] Security audit
```

---

## 9. Technology Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| **API Framework** | FastAPI (Async) | From scale_api, high performance |
| **Database** | PostgreSQL 15 | Reliable, triggers, JSONB |
| **Cache** | Redis 7 | From scale_api, rate limiting |
| **Task Queue** | Celery + Redis | From scale_api, background jobs |
| **Frontend** | Next.js 14 | React, SSR, TypeScript |
| **Payment** | Stripe + PromptPay | International + Thai |
| **Email** | SendGrid / SES | Transactional emails |
| **File Storage** | S3 / MinIO | QR codes, slips |
| **Monitoring** | Prometheus + Grafana | Metrics |
| **Logging** | Loki / ELK | Centralized logs |
| **Deployment** | Docker + Kubernetes | Scalable |
| **CI/CD** | GitHub Actions | Automation |

---

## 10. Migration Strategy

### 10.1 จาก shortener_app

```python
# เอามาใช้ได้เลย:
- URL creation logic
- QR code generation
- Phishing detection (OpenPhish)
- Click redirect logic

# ต้องปรับปรุง:
- Replace API key auth with new system
- Replace database models with new schema
- Add usage tracking
```

### 10.2 จาก check_url

```python
# เอามาใช้ได้เลย:
- Scanner services (Google, VirusTotal, etc.)
- Batch scanning logic
- Result caching

# ต้องปรับปรุง:
- Move to Celery tasks
- Integrate with new database
- Add webhook notifications
```

### 10.3 จาก scale_api ⭐

```python
# เอามาใช้เป็น base:
- Async FastAPI structure
- Redis cache layer
- PostgreSQL async connection
- PG Notify listener
- Celery configuration
- Cache-first strategy
```

---

## 11. Cost Estimation

### 11.1 Infrastructure (Monthly)

| Service | Starter | Growth | Scale |
|---------|---------|--------|-------|
| **Cloud Provider** | DigitalOcean | DigitalOcean | AWS/GCP |
| API Server | $24 (2GB) | $48 (4GB x2) | $200+ |
| Database | $15 (PostgreSQL) | $30 | $100+ |
| Redis | $15 | $30 | $50+ |
| Storage | $5 | $10 | $20+ |
| **Total** | **~$60** | **~$120** | **$400+** |

### 11.2 Break-even Analysis

```
ต้นทุน/เดือน: ~$60 (~2,100 บาท)

รายได้:
- Starter (199฿): 11 users = 2,189฿
- Pro (599฿): 4 users = 2,396฿

Break-even: ~10 Starter หรือ ~4 Pro users
```

---

## 12. Success Metrics

### 12.1 Technical KPIs

| Metric | Target |
|--------|--------|
| API Response Time (p95) | < 100ms |
| API Uptime | 99.9% |
| Error Rate | < 0.1% |
| Cache Hit Rate | > 90% |

### 12.2 Business KPIs

| Metric | Month 1 | Month 3 | Month 6 |
|--------|---------|---------|---------|
| Registered Users | 100 | 500 | 2000 |
| Paid Users | 5 | 30 | 100 |
| MRR (฿) | 2,000 | 15,000 | 50,000 |
| API Calls/day | 10K | 100K | 500K |

---

## 13. Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Third-party API costs (VirusTotal) | High | Caching, quotas, fallbacks |
| DDoS attacks | High | Cloudflare, rate limiting |
| Data breach | Critical | Encryption, audit logs |
| Payment fraud | Medium | Verification, limits |
| Scaling issues | Medium | Load testing, auto-scaling |

---

## 14. Next Steps

1. **Review & Approve Plan** ✋ (รอ feedback)
2. Create GitHub Repository
3. Setup Project Structure
4. Begin Phase 1 Development

---

*Document Version: 1.0*
*Last Updated: February 2024*
*Author: Development Team*
