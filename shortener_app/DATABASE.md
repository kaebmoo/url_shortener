```
-- urls definition

CREATE TABLE urls (
	id INTEGER NOT NULL, 
	"key" VARCHAR, 
	secret_key VARCHAR, 
	target_url VARCHAR, 
	is_active BOOLEAN, 
	clicks INTEGER, 
	api_key VARCHAR, 
	created_at DATETIME DEFAULT (CURRENT_TIMESTAMP), 
	updated_at DATETIME, 
	is_checked BOOLEAN, 
	status VARCHAR, 
	title VARCHAR(255), 
	favicon_url VARCHAR(255), 
	PRIMARY KEY (id)
);

CREATE INDEX ix_urls_api_key ON urls (api_key);
CREATE UNIQUE INDEX ix_urls_key ON urls ("key");
CREATE UNIQUE INDEX ix_urls_secret_key ON urls (secret_key);
CREATE INDEX ix_urls_target_url ON urls (target_url);

shortener_app/models.py

class URL(Base):
    __tablename__ = "urls"  # ชื่อ table ใน sqlite

    id = Column(Integer, primary_key=True)                  # primary key
    key = Column(String, unique=True, index=True)           # shorten 
    secret_key = Column(String, unique=True, index=True)    # a secret key to the user to manage their shortened URL and see statistics.
    target_url = Column(String, index=True)                 # to store the URL strings for which your app provides shortened URLs.
    is_active = Column(Boolean, default=True)               # false is delete
    clicks = Column(Integer, default=0)     # this field will increase the integer each time someone clicks the shortened link.
    api_key = Column(String, index=True)  # เพิ่มฟิลด์นี้เพื่อเก็บ API key
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # เพิ่มฟิลด์วันที่และเวลาในการสร้าง
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())       # เพิ่มฟิลด์วันที่และเวลาในการอัปเดต
    is_checked = Column(Boolean, default=False, nullable=True)
    status = Column(String) # เก็บสถานะว่าเป็น url อันตรายหรือไม่ เช่น safe, danger, no info
    title = Column(String(255)) # title page
    favicon_url = Column(String(255)) # favicon url

```

ในกรณีของ FastAPI การสร้างฐานข้อมูลจาก models.py ที่คุณให้มาสามารถทำได้โดยใช้ Alembic ซึ่งเป็นเครื่องมือสำหรับจัดการ migration ของ SQLAlchemy

**ขั้นตอน:**

1. **ติดตั้ง Alembic:**

   ```bash
   pip install alembic
   ```

2. **กำหนดค่า Alembic:**

   * สร้างไฟล์ `alembic.ini` ใน root directory ของโปรเจ็กต์ของคุณ โดยมีเนื้อหาดังนี้ (ปรับแต่งตามการตั้งค่าฐานข้อมูลของคุณ):

   ```ini
   [alembic]
   script_location = alembic
   sqlalchemy.url = sqlite:///./shortener.db 
   ```

3. **เริ่มต้น Alembic:**

   ```bash
   alembic init alembic
   ```

   คำสั่งนี้จะสร้างโฟลเดอร์ `alembic` ที่มีไฟล์สำหรับจัดการ migration

4. **สร้าง migration แรก:**

   ```bash
   alembic revision --autogenerate -m "create initial tables"
   ```

   Alembic จะตรวจสอบ models.py ของคุณ และสร้างไฟล์ migration ในโฟลเดอร์ `alembic/versions` ที่มีคำสั่ง SQL สำหรับสร้างตารางต่างๆ

5. **ปรับใช้ migration:**

   ```bash
   alembic upgrade head
   ```

   คำสั่งนี้จะดำเนินการ migration และสร้างตารางในฐานข้อมูลของคุณ

**ตัวอย่างการใช้งานใน FastAPI:**

```python
from fastapi import FastAPI
from database import engine  # Assuming you have an engine defined in database.py

app = FastAPI()

# ... other FastAPI code ...

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # ตรวจสอบว่าตารางมีอยู่หรือไม่ (อาจใช้ metadata.tables.contains() หรือวิธีอื่น)
        if not engine.dialect.has_table(conn, "urls"): 
            await conn.run_sync(Base.metadata.create_all) 
```

**คำอธิบายเพิ่มเติม:**

* **Alembic** ช่วยให้คุณสามารถจัดการการเปลี่ยนแปลงโครงสร้างฐานข้อมูลได้อย่างมีระบบ โดยสร้างไฟล์ migration ที่บันทึกการเปลี่ยนแปลงแต่ละครั้ง ทำให้คุณสามารถย้อนกลับหรือปรับใช้การเปลี่ยนแปลงได้ง่าย
* ในตัวอย่าง FastAPI เราใช้ `app.on_event("startup")` เพื่อตรวจสอบและสร้างตารางเมื่อแอปพลิเคชันเริ่มทำงาน ถ้าตารางยังไม่มีอยู่ ก็จะสร้างตารางทั้งหมดจาก models ที่กำหนดไว้ใน `Base.metadata`

**ข้อควรระวัง:**

* ตรวจสอบให้แน่ใจว่าการตั้งค่าฐานข้อมูลใน `alembic.ini` และ `database.py` ถูกต้อง
* ระมัดระวังในการปรับใช้ migration ในสภาพแวดล้อม production เพราะอาจส่งผลกระทบต่อข้อมูลที่มีอยู่
* พิจารณาใช้ `--run-syncdb` ในกรณีที่คุณต้องการสร้างฐานข้อมูลใหม่ทั้งหมด แต่ควรใช้ด้วยความระมัดระวังเพราะจะลบข้อมูลที่มีอยู่ทั้งหมด

**เพิ่มเติม:**

* คุณสามารถเรียนรู้เพิ่มเติมเกี่ยวกับ Alembic ได้จากเอกสารอย่างเป็นทางการ: [https://alembic.sqlalchemy.org/](https://alembic.sqlalchemy.org/)
* หากคุณต้องการปรับแต่งวิธีการสร้างตารางหรือมี logic เพิ่มเติม คุณสามารถแก้ไขไฟล์ migration ที่ Alembic สร้างขึ้นได้
