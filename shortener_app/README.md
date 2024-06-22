# gogoth
 Secure Shortened URL

Build a URL Shortener With FastAPI and Python
from https://realpython.com/build-a-python-url-shortener-with-fastapi/

The source code has been updated to support pydantic version 2 and additional pydantic-settings have been installed.
for more information https://docs.pydantic.dev/latest/migration/
I have used bump-pydantic to transform the source code.
The modified file is the config.py file.

Run the live server using uvicorn:
 uvicorn shortener_app.main:app --reload
 or python3 -m uvicorn shortener_app.main:app --reload

### โค้ดใน `main.py`

โค้ดใน `main.py` ของคุณมีการจัดการฟังก์ชันหลักของ API ไว้อย่างดี โดยมีการทำงานดังนี้:

- **`get_admin_info`**: สร้าง URL ที่เป็นมิตรสำหรับการจัดการข้อมูลลิงค์
- **`raise_not_found`**: ยกเว้นข้อผิดพลาด 404 เมื่อ URL ไม่พบ
- **`raise_bad_request`**: ยกเว้นข้อผิดพลาด 400 เมื่อมีการร้องขอที่ไม่ถูกต้อง
- **`raise_api_key`**: ยกเว้นข้อผิดพลาด 401 เมื่อ API key ไม่ถูกต้องหรือหายไป
- **`get_db`**: ฟังก์ชันสำหรับการสร้าง session ฐานข้อมูล
- **`read_root`**: ฟังก์ชันต้อนรับที่ `/` route
- **`forward_to_target_url`**: ฟังก์ชันสำหรับการเปลี่ยนเส้นทางจาก URL ที่ย่อไปยัง URL เป้าหมาย
- **`create_url`**: ฟังก์ชันสำหรับสร้าง URL ใหม่
- **`get_url_info`**: ฟังก์ชันสำหรับดึงข้อมูลการจัดการ URL
- **`delete_url`**: ฟังก์ชันสำหรับลบ URL
