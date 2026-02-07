# URL Shortener Telegram Bot

Telegram Bot สำหรับย่อ URL ที่เชื่อมต่อกับระบบ User Management

## Features

### สำหรับผู้ใช้ทั่วไป
- ย่อ URL โดยส่งลิงก์มาที่ bot
- ดูรายการ URL ที่เคยย่อ
- ลบ URL ที่ไม่ต้องการ
- อัพเกรดเป็น VIP

### สำหรับ VIP
- ย่อ URL ได้ไม่จำกัด
- ตั้ง custom alias ได้

### สำหรับ Admin
- Approve/Reject คำขออัพเกรด VIP ผ่าน Inline Buttons
- ดูรายการ pending requests
- แจ้งเหตุผลการ reject ให้ผู้ใช้

## Commands

### User Commands
| Command | Description |
|---------|-------------|
| `/start` | เริ่มต้นใช้งาน / ดูสถานะ |
| `/help` | แสดงคำสั่งทั้งหมด |
| `/list` | ดู URL ที่เคยย่อ (10 รายการล่าสุด) |
| `/delete <secret_key>` | ลบ URL |
| `/upgrade` | ดูวิธีอัพเกรดเป็น VIP |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/pending` | ดูรายการรอ approve |
| `/approve <telegram_id>` | Approve ผู้ใช้เป็น VIP |
| `/reject <telegram_id> [reason]` | Reject คำขอ |

## การใช้งาน

### ย่อ URL
```
ส่ง: https://example.com/very/long/url
รับ: ✅ Shortened: https://short.url/abc123
```

### ย่อ URL พร้อม Custom Alias (VIP เท่านั้น)
```
ส่ง: https://example.com myalias
รับ: ✅ Shortened: https://short.url/myalias
```

## Setup

### 1. Environment Variables

เพิ่มใน `config.env`:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_TELEGRAM_ID=your_telegram_id

# VIP Upgrade Info
VIP_PRICE=99 THB/Year
VIP_BANK=ธนาคารกรุงไทย
VIP_ACCOUNT=0011234567
```

### 2. Install Dependencies

```bash
pip install python-telegram-bot python-dotenv validators
```

### 3. Run Bot

```bash
# วิธีที่ 1: ผ่าน Flask CLI
flask run_bot

# วิธีที่ 2: รันตรง
python -m bot_app.run

# วิธีที่ 3: ผ่าน manage.py
python manage.py run_bot
```

## Project Structure

```
bot_app/
├── __init__.py
├── config.py          # Bot configuration
├── run.py             # Entry point
├── core/
│   ├── __init__.py
│   ├── handlers.py    # Telegram command handlers
│   ├── services.py    # Business logic & API calls
│   └── ai.py          # AI/NLP (future development)
└── README.md
```

## Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Telegram   │────▶│    Bot App      │────▶│  User Mgmt DB   │
│    User     │◀────│   (handlers)    │◀────│   (Flask App)   │
└─────────────┘     └─────────────────┘     └─────────────────┘
                            │
                            ▼
                    ┌─────────────────┐
                    │  Shortener API  │
                    │   (FastAPI)     │
                    └─────────────────┘
```

## Admin Workflow

### Approve Flow
```
User ส่ง Slip
      │
      ▼
┌─────────────────────────────┐
│ 💳 New Upgrade Request      │
│ 👤 User ID: 123456          │
│ 📛 Name: John               │
│                             │
│ [✅ Approve] [❌ Reject]    │
└─────────────────────────────┘
      │
      ├── กด Approve ──▶ User ได้รับแจ้ง "🎉 Upgraded to VIP!"
      │
      └── กด Reject ──▶ เลือกเหตุผล
                              │
                              ▼
                        ┌───────────────────┐
                        │ [💳 Invalid slip] │
                        │ [💰 Amount wrong] │
                        │ [🔍 Cannot verify]│
                        │ [❌ Other reason] │
                        └───────────────────┘
                              │
                              ▼
                        User ได้รับแจ้ง "❌ Declined"
```

## Security Features

- Rate limiting (2 seconds per user)
- Admin-only commands verification
- Graceful shutdown handling
- URL validation using `validators` library
- HTML escape for user inputs

## Error Handling

- Retry logic สำหรับ API calls (max 2 attempts)
- Telegram rate limit handling (`RetryAfter`)
- Connection timeout handling
- Graceful error messages for users

## Future Development

- `ai.py` - รองรับภาษาธรรมชาติ (NLP) สำหรับสั่งงาน bot
- Webhook mode สำหรับ production
- Persistent storage สำหรับ pending requests

## License

MIT
