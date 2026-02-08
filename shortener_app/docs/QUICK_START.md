# Quick Start Guide

เริ่มต้นใช้งาน URL Shortener API ใน 5 นาที

## Step 1: Get Your API Key

1. ไปที่ [your-domain.com/register](https://your-domain.com/register)
2. สมัครสมาชิกด้วย email
3. ยืนยัน email
4. Login และไปที่ **Settings > API Keys**
5. Copy API Key

## Step 2: Test Your API Key

```bash
curl https://api.your-domain.com/user/url_count \
  -H "X-API-KEY: YOUR_API_KEY"
```

ถ้าได้ response แบบนี้ แสดงว่า API Key ใช้ได้:
```json
{"url_count": 0}
```

## Step 3: Shorten Your First URL

```bash
curl -X POST https://api.your-domain.com/url \
  -H "X-API-KEY: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://github.com"}'
```

Response:
```json
{
  "url": "https://short.url/abc123",
  "qr_code": "data:image/png;base64,..."
}
```

## Step 4: Use in Your App

### Python
```python
import requests

API_KEY = "YOUR_API_KEY"
BASE_URL = "https://api.your-domain.com"

def shorten_url(url):
    response = requests.post(
        f"{BASE_URL}/url",
        json={"target_url": url},
        headers={"X-API-KEY": API_KEY}
    )
    return response.json()

result = shorten_url("https://example.com")
print(result["url"])  # https://short.url/abc123
```

### JavaScript
```javascript
const API_KEY = 'YOUR_API_KEY';
const BASE_URL = 'https://api.your-domain.com';

async function shortenUrl(url) {
  const response = await fetch(`${BASE_URL}/url`, {
    method: 'POST',
    headers: {
      'X-API-KEY': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ target_url: url })
  });
  return response.json();
}

shortenUrl('https://example.com')
  .then(result => console.log(result.url));
```

## Common Use Cases

### 1. Shorten URL and Display QR Code

```python
result = shorten_url("https://example.com")

# Save QR code
import base64
qr_data = result["qr_code"].split(",")[1]
with open("qr.png", "wb") as f:
    f.write(base64.b64decode(qr_data))
```

### 2. Get Click Statistics

```python
urls = requests.get(
    f"{BASE_URL}/user/urls",
    headers={"X-API-KEY": API_KEY}
).json()

for url in urls:
    print(f"{url['url']}: {url['clicks']} clicks")
```

### 3. Delete a URL

```python
secret_key = "abc123_x7k9m2p1"  # จาก admin_url
requests.delete(
    f"{BASE_URL}/admin/{secret_key}",
    headers={"X-API-KEY": API_KEY}
)
```

## API Endpoints Summary

| Action | Method | Endpoint |
|--------|--------|----------|
| Shorten URL | POST | `/url` |
| Get all URLs | GET | `/user/urls` |
| Get URL count | GET | `/user/url_count` |
| Get URL info | GET | `/admin/{secret_key}` |
| Delete URL | DELETE | `/admin/{secret_key}` |
| Check phishing | GET | `/check-phishing/?url=...` |

## Need Help?

- Full documentation: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- Email: api-support@your-domain.com
