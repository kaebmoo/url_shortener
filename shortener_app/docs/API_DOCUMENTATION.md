# URL Shortener API Documentation

API สำหรับย่อ URL พร้อม QR Code และระบบตรวจสอบความปลอดภัย

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Endpoints](#endpoints)
  - [URL Shortening](#url-shortening)
  - [URL Management](#url-management)
  - [User Information](#user-information)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Code Examples](#code-examples)
- [SDKs & Libraries](#sdks--libraries)

---

## Overview

URL Shortener API ช่วยให้คุณ:
- ย่อ URL ยาว ๆ ให้สั้นลง
- สร้าง QR Code อัตโนมัติ
- ติดตามจำนวนคลิก
- ตรวจสอบความปลอดภัยของ URL
- กำหนด custom alias (สำหรับ VIP)

### Features by Plan

| Feature | Free | VIP |
|---------|------|-----|
| Shorten URLs | ✅ 30 URLs | ✅ Unlimited |
| QR Code Generation | ✅ | ✅ |
| Click Analytics | ✅ | ✅ |
| Custom Alias | ❌ | ✅ |
| URL Expiry | 7 days | Never |
| API Rate Limit | 100/min | 1000/min |

---

## Authentication

API ใช้ **API Key** สำหรับ authentication ส่งผ่าน header `X-API-KEY`

### Getting Your API Key

1. สมัครสมาชิกที่ [your-domain.com/register](https://your-domain.com/register)
2. ยืนยัน email
3. เข้าสู่ระบบและไปที่ Settings > API Keys
4. Copy API Key ของคุณ

### Using API Key

```bash
curl -X POST https://api.your-domain.com/url \
  -H "X-API-KEY: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'
```

> ⚠️ **Security Warning**: เก็บ API Key เป็นความลับ อย่า commit ลง git หรือแชร์ในที่สาธารณะ

---

## Base URL

| Environment | URL |
|-------------|-----|
| Production | `https://api.your-domain.com` |
| Development | `http://localhost:8000` |

---

## Endpoints

### URL Shortening

#### Create Short URL

สร้าง URL สั้นจาก URL ยาว

```
POST /url
```

**Headers**
| Header | Required | Description |
|--------|----------|-------------|
| X-API-KEY | Yes | Your API Key |
| Content-Type | Yes | `application/json` |

**Request Body**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| target_url | string | Yes | URL ที่ต้องการย่อ |
| custom_key | string | No | Custom alias (VIP only, max 15 chars) |

**Example Request**
```bash
curl -X POST https://api.your-domain.com/url \
  -H "X-API-KEY: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://example.com/very/long/path?param=value"
  }'
```

**Example Response** `201 Created`
```json
{
  "target_url": "https://example.com/very/long/path?param=value",
  "is_active": true,
  "clicks": 0,
  "url": "https://short.url/abc123",
  "qr_code": "data:image/png;base64,iVBORw0KGgo...",
  "admin_url": "https://short.url/admin/abc123_x7k9m2p1"
}
```

**Response Fields**
| Field | Type | Description |
|-------|------|-------------|
| target_url | string | Original URL |
| is_active | boolean | URL active status |
| clicks | integer | Number of clicks |
| url | string | Shortened URL |
| qr_code | string | Base64 encoded QR code image |
| admin_url | string | Admin URL with secret key |

---

#### Create Short URL with Custom Alias (VIP)

```bash
curl -X POST https://api.your-domain.com/url \
  -H "X-API-KEY: your_vip_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://example.com",
    "custom_key": "my-brand"
  }'
```

**Response** `201 Created`
```json
{
  "url": "https://short.url/my-brand",
  "qr_code": "data:image/png;base64,..."
}
```

---

#### Create Short URL (Guest - No API Key)

สำหรับทดสอบหรือใช้งานชั่วคราว (URL หมดอายุใน 7 วัน)

```
POST /url/guest
```

**Rate Limit:** 30 requests per minute

**Example Request**
```bash
curl -X POST https://api.your-domain.com/url/guest \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'
```

---

### URL Management

#### Get URL Information

ดูข้อมูล URL รวมถึงจำนวนคลิกและสถานะ

```
GET /admin/{secret_key}
```

**Path Parameters**
| Parameter | Description |
|-----------|-------------|
| secret_key | Secret key จาก admin_url (format: `key_xxxxxxxx`) |

**Example Request**
```bash
curl https://api.your-domain.com/admin/abc123_x7k9m2p1 \
  -H "X-API-KEY: your_api_key"
```

**Example Response** `200 OK`
```json
{
  "target_url": "https://example.com/very/long/path",
  "is_active": true,
  "clicks": 42,
  "url": "https://short.url/abc123",
  "created_at": "2024-02-08T10:30:00Z",
  "status": "safe",
  "title": "Example Domain"
}
```

---

#### Delete/Deactivate URL

ลบหรือปิดการใช้งาน URL

```
DELETE /admin/{secret_key}
```

**Example Request**
```bash
curl -X DELETE https://api.your-domain.com/admin/abc123_x7k9m2p1 \
  -H "X-API-KEY: your_api_key"
```

**Example Response** `200 OK`
```json
{
  "detail": "URL deactivated successfully"
}
```

---

#### Get URL Scan Status

ดูผลการ scan ความปลอดภัยของ URL

```
POST /user/url/status
```

**Request Body**
```json
{
  "secret_key": "abc123_x7k9m2p1"
}
```

**Example Response** `200 OK`
```json
{
  "url": "https://example.com",
  "status": "safe",
  "is_checked": true,
  "scan_results": [
    {
      "scan_type": "google",
      "result": "safe",
      "timestamp": "2024-02-08T10:30:00Z"
    },
    {
      "scan_type": "virustotal",
      "result": "safe",
      "timestamp": "2024-02-08T10:30:05Z"
    }
  ]
}
```

**Status Values**
| Status | Description |
|--------|-------------|
| `safe` | URL ปลอดภัย |
| `danger` | URL อันตราย (phishing/malware) |
| `no info` | ยังไม่มีข้อมูล |
| `unknown` | ไม่สามารถตรวจสอบได้ |

---

### User Information

#### Get URL Count

ดูจำนวน URL ที่สร้างไว้

```
GET /user/url_count
```

**Example Response** `200 OK`
```json
{
  "url_count": 15
}
```

---

#### Get All URLs

ดูรายการ URL ทั้งหมดของคุณ

```
GET /user/urls
```

**Example Response** `200 OK`
```json
[
  {
    "key": "abc123",
    "target_url": "https://example.com/page1",
    "url": "https://short.url/abc123",
    "clicks": 42,
    "is_active": true,
    "secret_key": "abc123_x7k9m2p1",
    "created_at": "2024-02-08T10:30:00Z",
    "status": "safe"
  },
  {
    "key": "def456",
    "target_url": "https://example.com/page2",
    "url": "https://short.url/def456",
    "clicks": 10,
    "is_active": true,
    "secret_key": "def456_y8l0n3q2",
    "created_at": "2024-02-07T15:20:00Z",
    "status": "safe"
  }
]
```

---

### Safety Check

#### Check URL for Phishing

ตรวจสอบว่า URL เป็น phishing หรือไม่

```
GET /check-phishing/?url={url}
```

**Example Request**
```bash
curl "https://api.your-domain.com/check-phishing/?url=https://suspicious-site.com"
```

**Example Response** `200 OK`
```json
{
  "url": "https://suspicious-site.com",
  "is_phishing": true,
  "source": "openphish"
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing API Key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Custom key already exists |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

#### Invalid API Key
```json
{
  "detail": "Invalid API key"
}
```

#### URL Already Exists (Custom Key)
```json
{
  "detail": "Custom key 'my-brand' already exists"
}
```

#### URL Limit Exceeded (Free Plan)
```json
{
  "detail": "URL limit exceeded. Please upgrade to VIP."
}
```

#### Invalid URL Format
```json
{
  "detail": "Invalid URL format"
}
```

#### Dangerous URL Blocked
```json
{
  "detail": "URL is flagged as dangerous and cannot be shortened"
}
```

---

## Rate Limiting

| Plan | Limit | Window |
|------|-------|--------|
| Guest (no API Key) | 30 requests | per minute |
| Free | 100 requests | per minute |
| VIP | 1000 requests | per minute |

**Rate Limit Headers**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1707400800
```

**When Rate Limited** `429 Too Many Requests`
```json
{
  "detail": "Rate limit exceeded. Please wait 60 seconds."
}
```

---

## Code Examples

### Python

```python
import requests

class URLShortener:
    def __init__(self, api_key: str, base_url: str = "https://api.your-domain.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }

    def shorten(self, url: str, custom_key: str = None) -> dict:
        """Shorten a URL."""
        payload = {"target_url": url}
        if custom_key:
            payload["custom_key"] = custom_key

        response = requests.post(
            f"{self.base_url}/url",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_urls(self) -> list:
        """Get all URLs."""
        response = requests.get(
            f"{self.base_url}/user/urls",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def delete_url(self, secret_key: str) -> dict:
        """Delete a URL."""
        response = requests.delete(
            f"{self.base_url}/admin/{secret_key}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
shortener = URLShortener("your_api_key")

# Shorten URL
result = shortener.shorten("https://example.com/very/long/url")
print(f"Short URL: {result['url']}")

# Get all URLs
urls = shortener.get_urls()
for url in urls:
    print(f"{url['url']} -> {url['target_url']} ({url['clicks']} clicks)")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

class URLShortener {
  constructor(apiKey, baseUrl = 'https://api.your-domain.com') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'X-API-KEY': apiKey,
        'Content-Type': 'application/json'
      }
    });
  }

  async shorten(url, customKey = null) {
    const payload = { target_url: url };
    if (customKey) payload.custom_key = customKey;

    const response = await this.client.post('/url', payload);
    return response.data;
  }

  async getUrls() {
    const response = await this.client.get('/user/urls');
    return response.data;
  }

  async deleteUrl(secretKey) {
    const response = await this.client.delete(`/admin/${secretKey}`);
    return response.data;
  }
}

// Usage
const shortener = new URLShortener('your_api_key');

// Shorten URL
shortener.shorten('https://example.com/very/long/url')
  .then(result => console.log(`Short URL: ${result.url}`))
  .catch(err => console.error(err));
```

### cURL

```bash
# Shorten URL
curl -X POST https://api.your-domain.com/url \
  -H "X-API-KEY: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'

# Get all URLs
curl https://api.your-domain.com/user/urls \
  -H "X-API-KEY: your_api_key"

# Delete URL
curl -X DELETE https://api.your-domain.com/admin/abc123_x7k9m2p1 \
  -H "X-API-KEY: your_api_key"

# Check phishing
curl "https://api.your-domain.com/check-phishing/?url=https://suspicious.com"
```

### PHP

```php
<?php

class URLShortener {
    private $apiKey;
    private $baseUrl;

    public function __construct($apiKey, $baseUrl = 'https://api.your-domain.com') {
        $this->apiKey = $apiKey;
        $this->baseUrl = $baseUrl;
    }

    private function request($method, $endpoint, $data = null) {
        $ch = curl_init();

        $url = $this->baseUrl . $endpoint;
        $headers = [
            'X-API-KEY: ' . $this->apiKey,
            'Content-Type: application/json'
        ];

        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

        if ($method === 'POST') {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        } elseif ($method === 'DELETE') {
            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'DELETE');
        }

        $response = curl_exec($ch);
        curl_close($ch);

        return json_decode($response, true);
    }

    public function shorten($url, $customKey = null) {
        $data = ['target_url' => $url];
        if ($customKey) $data['custom_key'] = $customKey;

        return $this->request('POST', '/url', $data);
    }

    public function getUrls() {
        return $this->request('GET', '/user/urls');
    }

    public function deleteUrl($secretKey) {
        return $this->request('DELETE', '/admin/' . $secretKey);
    }
}

// Usage
$shortener = new URLShortener('your_api_key');
$result = $shortener->shorten('https://example.com/long/url');
echo "Short URL: " . $result['url'];
```

---

## SDKs & Libraries

| Language | Package | Installation |
|----------|---------|--------------|
| Python | `url-shortener-sdk` | `pip install url-shortener-sdk` |
| JavaScript | `@your-org/url-shortener` | `npm install @your-org/url-shortener` |
| PHP | `your-org/url-shortener` | `composer require your-org/url-shortener` |

> Note: SDKs coming soon. For now, use the code examples above.

---

## WebSocket API

### Real-time URL Updates

รับ update แบบ real-time เมื่อ URL ถูกคลิกหรือ scan เสร็จ

```
WebSocket: wss://api.your-domain.com/ws/url_update/{secret_key}
```

**Connection Example (JavaScript)**
```javascript
const ws = new WebSocket('wss://api.your-domain.com/ws/url_update/abc123_x7k9m2p1');

ws.onopen = () => {
  // Send API key for authentication
  ws.send(JSON.stringify({ api_key: 'your_api_key' }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
  // { clicks: 43, status: "safe", is_active: true }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

---

## Changelog

### v1.0.0 (Current)
- Initial API release
- URL shortening with QR codes
- Click tracking
- Phishing detection
- Custom aliases (VIP)

---

## Support

- **Documentation**: [docs.your-domain.com](https://docs.your-domain.com)
- **Email**: api-support@your-domain.com
- **GitHub Issues**: [github.com/your-org/url-shortener/issues](https://github.com/your-org/url-shortener/issues)

---

## Terms of Service

- ห้ามใช้สร้าง URL ที่เป็น phishing, malware, หรือ spam
- ห้ามใช้เพื่อกิจกรรมผิดกฎหมาย
- เราขอสงวนสิทธิ์ในการระงับ API Key ที่ละเมิดข้อกำหนด

---

*Last updated: February 2024*
