### English Explanation:

This code defines a FastAPI application that provides functionality for creating, retrieving, and redirecting shortened URLs. It utilizes an asynchronous PostgreSQL database for storing URL information and Redis for caching and quick lookups.

#### Key Components:

1. **Environment Loading and Configuration**: 
   - The environment variables are loaded using `dotenv`, which includes the database connection URL and API key for authentication.

2. **Database Setup**:
   - The SQLAlchemy ORM is used to define the `URL` model, which includes fields such as `key`, `secret_key`, `target_url`, `clicks`, and timestamps.
   - An asynchronous PostgreSQL engine is created for interacting with the database.
   - Redis is used for caching URL data to speed up retrieval.

3. **PostgreSQL Notification Listener**:
   - A `PostgresListener` class is defined to listen for changes in the PostgreSQL database.
   - It uses the `url_change_handler` to handle notifications from PostgreSQL, adding the payload to a queue for processing.
   - The `process_notification` function processes these notifications, syncing data to Redis.

4. **FastAPI Lifespan Management**:
   - The `lifespan` function runs on startup to sync data from PostgreSQL to Redis and start listening for database changes.
   - It also manages shutting down tasks cleanly when the application stops.

5. **API Endpoints**:
   - `/url/{key}`: Retrieves URL data by `key`. It first checks Redis and then falls back to the database if the data is not found in Redis.
   - `/url`: Creates a new shortened URL, storing it in PostgreSQL and syncing it to Redis if active. Protected by an API key.
   - `/` + `{key}`: Redirects to the target URL by the `key`, incrementing the click count and updating timestamps in both Redis and the database.

6. **Background Tasks and Syncing**:
   - The `sync_to_redis` function syncs URL data from PostgreSQL to Redis.
   - The `update_db` function updates the click count and timestamp in PostgreSQL asynchronously.

7. **Security**:
   - The `create_url` endpoint is protected by an API key to restrict access.

### Thai Explanation:

โค้ดนี้กำหนดแอปพลิเคชัน FastAPI ที่ให้ฟังก์ชันในการสร้าง ดึงข้อมูล และเปลี่ยนเส้นทาง URL ที่ถูกย่อ ส่วนนี้ใช้ฐานข้อมูล PostgreSQL แบบอะซิงโครนัสสำหรับการเก็บข้อมูล URL และ Redis สำหรับการแคชและการดึงข้อมูลที่รวดเร็ว

#### ส่วนประกอบหลัก:

1. **การโหลดและกำหนดค่าของสิ่งแวดล้อม**: 
   - ใช้ `dotenv` เพื่อโหลดตัวแปรสภาพแวดล้อม รวมถึง URL ของการเชื่อมต่อฐานข้อมูลและ API key สำหรับการยืนยันตัวตน

2. **การตั้งค่าฐานข้อมูล**:
   - ใช้ SQLAlchemy ORM เพื่อกำหนดโมเดล `URL` ซึ่งประกอบด้วยฟิลด์ต่าง ๆ เช่น `key`, `secret_key`, `target_url`, `clicks` และ timestamps
   - สร้าง PostgreSQL engine แบบอะซิงโครนัสเพื่อใช้งานกับฐานข้อมูล
   - ใช้ Redis สำหรับแคชข้อมูล URL เพื่อเพิ่มความเร็วในการดึงข้อมูล

3. **PostgreSQL Notification Listener**:
   - คลาส `PostgresListener` ถูกกำหนดให้ฟังการเปลี่ยนแปลงในฐานข้อมูล PostgreSQL
   - ใช้ `url_change_handler` เพื่อจัดการการแจ้งเตือนจาก PostgreSQL และเพิ่มข้อมูลใน queue สำหรับการประมวลผล
   - ฟังก์ชัน `process_notification` ประมวลผลการแจ้งเตือนเหล่านี้และซิงค์ข้อมูลกับ Redis

4. **การจัดการอายุการใช้งานของ FastAPI**:
   - ฟังก์ชัน `lifespan` ทำงานเมื่อเริ่มต้นโปรแกรมเพื่อซิงค์ข้อมูลจาก PostgreSQL ไปยัง Redis และเริ่มฟังการเปลี่ยนแปลงของฐานข้อมูล
   - จัดการการหยุดทำงานของ task อย่างสะอาดเมื่อแอปพลิเคชันหยุดทำงาน

5. **API Endpoints**:
   - `/url/{key}`: ดึงข้อมูล URL โดย `key` โดยตรวจสอบใน Redis ก่อนและถ้าไม่พบข้อมูลจะดึงจากฐานข้อมูล
   - `/url`: สร้าง URL ที่ถูกย่อใหม่ เก็บไว้ใน PostgreSQL และซิงค์ไปยัง Redis ถ้าเป็น active ป้องกันด้วย API key
   - `/` + `{key}`: เปลี่ยนเส้นทางไปยัง target URL โดยใช้ `key` เพิ่มจำนวนคลิกและอัปเดต timestamp ในทั้ง Redis และฐานข้อมูล

6. **Background Tasks และ Syncing**:
   - ฟังก์ชัน `sync_to_redis` ซิงค์ข้อมูล URL จาก PostgreSQL ไปยัง Redis
   - ฟังก์ชัน `update_db` อัปเดตจำนวนคลิกและ timestamp ใน PostgreSQL แบบอะซิงโครนัส

7. **ความปลอดภัย**:
   - Endpoint `/url` ถูกป้องกันด้วย API key เพื่อจำกัดการเข้าถึง
   
### การทำงานของแอปพลิเคชัน
1. **การสร้าง URL ใหม่**: รับข้อมูล URL จากผู้ใช้และบันทึกใน PostgreSQL จากนั้นซิงค์ข้อมูลไปยัง Redis ถ้า URL เป็น active
2. **การดึงข้อมูล URL**: เมื่อผู้ใช้ขอข้อมูล URL โดยใช้ `key` แอปจะพยายามดึงข้อมูลจาก Redis ก่อนเพื่อเพิ่มความเร็ว หากไม่พบข้อมูลจะดึงจาก PostgreSQL แล้วซิงค์ข้อมูลไปยัง Redis
3. **การซิงค์ข้อมูล**: ในช่วงเริ่มต้นแอปจะซิงค์ข้อมูลทั้งหมดจาก PostgreSQL ไปยัง Redis เพื่อลดการดึงข้อมูลจากฐานข้อมูลโดยตรง

### จุดเด่นของโปรแกรม
- **ประสิทธิภาพสูง**: ใช้ Redis เพื่อ cache ข้อมูล ลดการเรียกใช้ฐานข้อมูล PostgreSQL โดยตรงในทุกคำขอ
- **การทำงานแบบอะซิงโครนัส**: เพิ่มประสิทธิภาพในการจัดการคำขอและการประมวลผลข้อมูล
- **การซิงค์ข้อมูลอัตโนมัติ**: ข้อมูล URL จะถูกซิงค์ระหว่าง PostgreSQL และ Redis อย่างอัตโนมัติทั้งในช่วงเริ่มต้นและเมื่อมีการสร้างหรืออัพเดต URL ใหม่

โปรแกรมนี้มีความสามารถในการจัดการ URL ที่ย่อแล้วด้วยการเก็บข้อมูลใน PostgreSQL และใช้ Redis เป็น cache เพื่อเพิ่มประสิทธิภาพในการดึงข้อมูล, ลดภาระของฐานข้อมูลหลัก, และจัดการการเข้าถึง URL อย่างมีประสิทธิภาพ

```
curl -X POST "http://localhost:9000/url" \
-H "x-api-key: your-secure-api-key" \
-H "Content-Type: application/json" \
-d '{"key": "example-key", "target_url": "https://example.com"}'
```