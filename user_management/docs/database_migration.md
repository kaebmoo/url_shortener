หากคุณต้องการย้ายข้อมูลจาก SQLite ไปยัง PostgreSQL พร้อมกับการเปลี่ยนแปลงการตั้งค่า Alembic เพื่อใช้กับ PostgreSQL คุณสามารถทำตามขั้นตอนต่อไปนี้:

### 1. **ตั้งค่าการเชื่อมต่อฐานข้อมูลใหม่ใน Alembic**

ในไฟล์ `alembic.ini` คุณควรตั้งค่า `sqlalchemy.url` ให้ชี้ไปยัง PostgreSQL:

```ini
sqlalchemy.url = postgresql+psycopg2://username:password@127.0.0.1/dbname
```

### 2. **ย้ายข้อมูลจาก SQLite ไปยัง PostgreSQL**

การย้ายข้อมูลจาก SQLite ไปยัง PostgreSQL สามารถทำได้โดยใช้เครื่องมือหลายตัว เช่น:

- **ใช้ `pgloader`**: เป็นเครื่องมือยอดนิยมที่ใช้ย้ายข้อมูลจาก SQLite ไปยัง PostgreSQL.
  
  ```bash
  pgloader sqlite:///path/to/sqlite.db postgresql://username:password@127.0.0.1/dbname
  ```

- **ใช้ `sqlalchemy` สำหรับการย้ายข้อมูลด้วยตนเอง**: คุณสามารถเขียนสคริปต์ Python เพื่อดึงข้อมูลจาก SQLite แล้วใส่ลงใน PostgreSQL.

  ตัวอย่าง:
  ```python
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker
  from your_app import models  # import SQLAlchemy models

  # สร้าง engine และ session สำหรับ SQLite
  sqlite_engine = create_engine("sqlite:///path/to/sqlite.db")
  SQLiteSessionLocal = sessionmaker(bind=sqlite_engine)

  # สร้าง engine และ session สำหรับ PostgreSQL
  postgres_engine = create_engine("postgresql+psycopg2://username:password@127.0.0.1/dbname")
  PostgresSessionLocal = sessionmaker(bind=postgres_engine)

  # ดึงข้อมูลจาก SQLite แล้วเพิ่มใน PostgreSQL
  with SQLiteSessionLocal() as sqlite_session, PostgresSessionLocal() as postgres_session:
      for instance in sqlite_session.query(models.YourModel).all():
          postgres_session.add(instance)
      postgres_session.commit()
  ```

### 3. **ปรับ Alembic ให้ใช้งานกับ PostgreSQL**

ถ้าคุณยังมีไฟล์ Migration เดิมที่สร้างจาก SQLite และคุณต้องการให้ Alembic ทำงานกับ PostgreSQL โดยไม่สร้างปัญหา คุณอาจต้อง:

- **ตั้งสถานะการ Migration ใน PostgreSQL**: หากมี Migration เดิมใน SQLite ที่คุณต้องการใช้กับ PostgreSQL คุณสามารถตั้งสถานะให้ PostgreSQL รู้ว่าได้ใช้ Migration เหล่านั้นแล้ว โดยใช้คำสั่งนี้หลังจากย้ายข้อมูล:

  ```bash
  alembic stamp head
  ```

  คำสั่งนี้จะตั้งสถานะของ Alembic ใน PostgreSQL ให้เท่ากับสถานะล่าสุดที่ใช้ใน SQLite โดยไม่ต้องรัน Migration ใหม่อีกครั้ง.

### 4. **รัน Alembic กับ PostgreSQL**

เมื่อคุณได้ย้ายข้อมูลแล้วและตั้งสถานะการ Migration ใน PostgreSQL:

- ตรวจสอบว่าไฟล์ Migration ใดๆ ที่สร้างใหม่หลังจากนี้จะถูกใช้กับ PostgreSQL โดยไม่มีปัญหาใด ๆ:

  ```bash
  alembic upgrade head
  ```

### 5. **ตรวจสอบและทดสอบ**

- ตรวจสอบว่า PostgreSQL มีโครงสร้างฐานข้อมูลและข้อมูลที่ถูกย้ายมาอย่างถูกต้อง.
- ทดสอบแอปพลิเคชันของคุณเพื่อให้แน่ใจว่าการเชื่อมต่อกับ PostgreSQL ทำงานได้อย่างถูกต้อง.

### สรุป:

1. ตั้งค่า Alembic ให้ชี้ไปที่ PostgreSQL ใน `alembic.ini`.
2. ย้ายข้อมูลจาก SQLite ไปยัง PostgreSQL โดยใช้ `pgloader` หรือเขียนสคริปต์ Python.
3. ตั้งสถานะการ Migration ใน PostgreSQL ให้ตรงกับสถานะล่าสุดที่ใช้ใน SQLite.
4. รัน Alembic เพื่ออัปเดตฐานข้อมูล PostgreSQL และทำให้แน่ใจว่าการตั้งค่าทั้งหมดถูกต้อง.
5. ทดสอบแอปพลิเคชันของคุณกับ PostgreSQL.


```
pgloader sqlite:////GitHub/url_shortener/user_management/data-dev.sqlite postgresql://seal:xxx@127.0.0.1/user

pgloader sqlite:////GitHub/url_shortener/shortener.db postgresql://seal:xxx@127.0.0.1/shortener

pgloader sqlite:////GitHub/url_shortener/apikey.db postgresql://seal:xxx@127.0.0.1/apikey

pgloader sqlite:////GitHub/short_url_tools/tools/web_scan/url_blacklist/blacklist.db postgresql://seal:xxx@127.0.0.1/blacklist
```