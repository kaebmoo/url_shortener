# API Reference

Quick reference สำหรับ URL Shortener API

## Authentication

ทุก request ต้องส่ง header:
```
X-API-KEY: your_api_key
```

---

## Endpoints

### URL Operations

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/url` | สร้าง short URL | API Key |
| `POST` | `/url/guest` | สร้าง short URL (ไม่ต้อง API Key, หมดอายุ 7 วัน) | - |
| `GET` | `/{key}` | Redirect ไปยัง target URL | - |
| `GET` | `/{key}*` | Preview URL (แสดง warning ถ้าไม่ปลอดภัย) | - |

### User Operations

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/user/urls` | ดูรายการ URL ทั้งหมด | API Key |
| `GET` | `/user/url_count` | ดูจำนวน URL | API Key |
| `POST` | `/user/url/status` | ดูสถานะ scan ของ URL | API Key |

### Admin Operations

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/admin/{secret_key}` | ดูข้อมูล URL | API Key |
| `DELETE` | `/admin/{secret_key}` | ลบ/ปิด URL | API Key |

### Safety Operations

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/check-phishing/?url=...` | ตรวจสอบ phishing | - |
| `GET` | `/preview_url?url=...` | Preview หน้าเว็บ | Token |
| `POST` | `/capture_screen` | Capture screenshot | API Key |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://host/ws/url_update/{secret_key}` | Real-time updates |

---

## Request/Response Examples

### POST /url

**Request:**
```json
{
  "target_url": "https://example.com/page",
  "custom_key": "my-link"  // optional, VIP only
}
```

**Response:** `201 Created`
```json
{
  "target_url": "https://example.com/page",
  "is_active": true,
  "clicks": 0,
  "url": "https://short.url/my-link",
  "qr_code": "data:image/png;base64,...",
  "admin_url": "https://short.url/admin/my-link_abc12345"
}
```

### GET /user/urls

**Response:** `200 OK`
```json
[
  {
    "key": "abc123",
    "target_url": "https://example.com",
    "url": "https://short.url/abc123",
    "clicks": 42,
    "is_active": true,
    "secret_key": "abc123_x7k9m2p1",
    "created_at": "2024-02-08T10:30:00Z",
    "status": "safe"
  }
]
```

### POST /user/url/status

**Request:**
```json
{
  "secret_key": "abc123_x7k9m2p1"
}
```

**Response:** `200 OK`
```json
{
  "url": "https://example.com",
  "status": "safe",
  "is_checked": true,
  "scan_results": [
    {"scan_type": "google", "result": "safe"},
    {"scan_type": "virustotal", "result": "safe"}
  ]
}
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| `200` | OK |
| `201` | Created |
| `400` | Bad Request |
| `401` | Unauthorized (Invalid API Key) |
| `403` | Forbidden (No permission) |
| `404` | Not Found |
| `409` | Conflict (Key exists) |
| `429` | Rate Limited |
| `500` | Server Error |

---

## Error Response

```json
{
  "detail": "Error message"
}
```

---

## Rate Limits

| Plan | Limit |
|------|-------|
| Guest | 30/min |
| Free | 100/min |
| VIP | 1000/min |

---

## URL Status Values

| Status | Meaning |
|--------|---------|
| `safe` | URL ปลอดภัย |
| `danger` | URL อันตราย |
| `no info` | รอ scan |
| `unknown` | ไม่สามารถตรวจสอบได้ |

---

## Reserved Keys

ไม่สามารถใช้เป็น custom key:
```
apps, docs, redoc, openapi, about, api,
url, user, admin, login, register
```

---

## Limits

| Item | Limit |
|------|-------|
| Custom key length | 15 characters |
| Target URL length | 2048 characters |
| URLs per Free user | 30 |
| URLs per VIP user | Unlimited |
| Guest URL expiry | 7 days |
