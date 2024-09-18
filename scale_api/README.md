This program is a web application developed with FastAPI, using PostgreSQL and Redis to manage shortened URLs. It utilizes asynchronous programming to enhance performance and data handling. Here's how it works:

### 1. Connection Setup
- **PostgreSQL:** Uses SQLAlchemy with `asyncpg` as an asynchronous database engine to connect to PostgreSQL, where it stores URL data.
- **Redis:** Uses `aioredis` to connect to Redis asynchronously, acting as a cache for URL data.

### 2. Data Model (`URL`)
- Creates a `URL` model using SQLAlchemy to store shortened URL information in PostgreSQL. It includes fields such as `key`, `target_url`, `is_active`, `clicks`, and others to store necessary details about each URL.

### 3. Main Functions and Operations
- **`sync_to_redis(url: URL)`**: Synchronizes URL data from PostgreSQL to Redis by storing the URL data as JSON in Redis.
- **`get_db()`**: Creates an asynchronous connection to PostgreSQL to be used in request handlers.
- **`update_db(key: str)`**: Updates the URL information in PostgreSQL, such as increasing the click count and updating the `updated_at` timestamp.
- **`get_url(key: str, background_tasks: BackgroundTasks)`**: Retrieves URL data by the given key.
  - Checks Redis for the data first. If found, it updates the click count and timestamp in Redis and schedules an update in PostgreSQL as a background task.
  - If not found in Redis, it retrieves the data from PostgreSQL and synchronizes it to Redis.
- **`create_url(url: dict, background_tasks: BackgroundTasks)`**: Creates a new URL and stores it in PostgreSQL.
  - After saving to PostgreSQL, if the URL is active, it synchronizes the data to Redis as a background task.

### 4. Initialization Functions
- **`create_tables()`**: Creates database tables in PostgreSQL based on the `URL` model definition.
- **`startup_sync()`**: Synchronizes all active URL data from PostgreSQL to Redis during application startup. Before syncing, it deletes existing URL keys from Redis.

### 5. Application Workflow
- **The Application:** Sets up a FastAPI app with a lifecycle (`lifespan`) to perform `create_tables()` and `startup_sync()` at startup.
- **Running the Server:** Uses `uvicorn` to run the application on `localhost` at port 9000.

### How the Application Works
1. **Creating a New URL:** Accepts URL data from the user, saves it to PostgreSQL, and synchronizes it to Redis if the URL is active.
2. **Retrieving URL Data:** When a user requests URL data using a `key`, the app first attempts to fetch the data from Redis to improve speed. If not found, it retrieves the data from PostgreSQL and synchronizes it to Redis.
3. **Data Synchronization:** During startup, the app synchronizes all active URLs from PostgreSQL to Redis to reduce direct database calls.

### Key Features
- **High Performance:** Uses Redis to cache URL data, reducing the need to directly access PostgreSQL on every request.
- **Asynchronous Operations:** Enhances the efficiency of handling requests and processing data.
- **Automatic Synchronization:** URL data is automatically synchronized between PostgreSQL and Redis both at startup and when URLs are created or updated.

This program manages shortened URLs by storing them in PostgreSQL and using Redis as a cache to enhance performance. It reduces the load on the main database and handles URL access efficiently through automatic data synchronization.

โปรแกรมนี้เป็นเว็บแอปพลิเคชันที่พัฒนาด้วย FastAPI และใช้ฐานข้อมูล PostgreSQL และ Redis เพื่อจัดการข้อมูลของ URL ที่ถูกย่อ (shortened URLs) โดยมีการใช้การทำงานแบบอะซิงโครนัส (asynchronous) เพื่อเพิ่มประสิทธิภาพในการประมวลผลและการจัดการข้อมูล มีการทำงานดังนี้:

### 1. การตั้งค่าการเชื่อมต่อ
- **PostgreSQL:** ใช้ SQLAlchemy และ `asyncpg` เป็น asynchronous database engine เพื่อเชื่อมต่อกับฐานข้อมูล PostgreSQL ซึ่งเก็บข้อมูล URL ต่างๆ
- **Redis:** ใช้ `aioredis` เป็นไลบรารีสำหรับการเชื่อมต่อกับ Redis แบบอะซิงโครนัสเพื่อใช้เป็น cache สำหรับการเก็บข้อมูล URL

### 2. โมเดลข้อมูล (`URL`)
- สร้างโมเดล `URL` ด้วย SQLAlchemy เพื่อเก็บข้อมูล URL ที่ย่อแล้วในฐานข้อมูล PostgreSQL มีฟิลด์ต่าง ๆ เช่น `key`, `target_url`, `is_active`, `clicks` และอื่น ๆ เพื่อเก็บข้อมูลที่จำเป็นของ URL แต่ละรายการ

### 3. ฟังก์ชันและการทำงานหลัก
- **`sync_to_redis(url: URL)`**: ซิงค์ข้อมูลจาก PostgreSQL ไปยัง Redis โดยเก็บข้อมูลของ URL เป็น JSON และบันทึกใน Redis
- **`get_db()`**: สร้างการเชื่อมต่อแบบอะซิงโครนัสกับฐานข้อมูล PostgreSQL สำหรับการใช้งานในแต่ละคำขอ (request)
- **`update_db(key: str)`**: อัพเดตข้อมูล URL ใน PostgreSQL เช่นการเพิ่มจำนวนครั้งของการคลิกและการปรับปรุง `updated_at`
- **`get_url(key: str, background_tasks: BackgroundTasks)`**: ดึงข้อมูล URL ตาม key ที่กำหนด
  - ค้นหาข้อมูลใน Redis ก่อน หากพบจะอัพเดตจำนวนคลิกและเวลาใน Redis และเพิ่มงานให้อัพเดตข้อมูลใน PostgreSQL ในเบื้องหลัง
  - หากไม่พบใน Redis จะดึงข้อมูลจาก PostgreSQL และซิงค์ข้อมูลไปยัง Redis
- **`create_url(url: dict, background_tasks: BackgroundTasks)`**: สร้าง URL ใหม่และบันทึกลง PostgreSQL
  - หลังจากบันทึกลง PostgreSQL แล้ว หาก URL เป็น `active` จะซิงค์ไปยัง Redis ในเบื้องหลัง

### 4. ฟังก์ชันเริ่มต้น
- **`create_tables()`**: สร้างตารางในฐานข้อมูล PostgreSQL ตามโมเดล `URL` ที่กำหนด
- **`startup_sync()`**: ซิงค์ข้อมูล URL ที่ `is_active` เป็น `True` ทั้งหมดจาก PostgreSQL ไปยัง Redis ระหว่างการเริ่มต้นแอปพลิเคชัน โดยก่อนการซิงค์จะลบ keys ที่เกี่ยวข้องกับ URL ออกจาก Redis

### 5. การทำงานของแอปพลิเคชัน
- **แอปพลิเคชัน**: สร้างแอป FastAPI ที่มี lifecycle (`lifespan`) เพื่อทำงาน `create_tables()` และ `startup_sync()` เมื่อเริ่มต้นแอป
- **รันเซิร์ฟเวอร์**: ใช้ `uvicorn` เพื่อรันแอปพลิเคชันบน `localhost` พอร์ต 9000

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