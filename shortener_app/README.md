# gogoth
## Secure Shortened URL

### Build a URL Shortener With FastAPI and Python

> _Adapted from_ [https://realpython.com/build-a-python-url-shortener-with-fastapi/](https://realpython.com/build-a-python-url-shortener-with-fastapi/)

**Key Updates:**

* **Pydantic V2 Support:** The source code has been enhanced to seamlessly work with pydantic version 2.
* **Additional Settings:** `pydantic-settings` has been integrated for more configuration options.
* **Migration Guide:** For detailed information on the migration process, refer to [https://docs.pydantic.dev/latest/migration/](https://docs.pydantic.dev/latest/migration/)
* **Code Transformation:** The source code has been modified using `bump-pydantic`, with the `config.py` file being the primary target of changes.

**Running the Live Server**

You have two options for launching the live server:

1. **Using uvicorn:**

   ```bash
   uvicorn shortener_app.main:app --reload
   ```

2. **With Python3:**

   ```bash
   python3 -m uvicorn shortener_app.main:app --reload
   ```

Feel free to ask if you have any further questions or modifications!


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

การนำ title, favicon url เพิ่มในฐานข้อมูล

## ความสัมพันธ์ของ 3 ฟังก์ชัน fetch_page_info, fetch_page_info_and_update_sync, fetch_page_info_and_update

ทั้งสามฟังก์ชันนี้ทำงานร่วมกันเพื่อดึงข้อมูล title และ favicon จาก URL ที่กำหนดให้ และอัปเดตข้อมูลเหล่านี้ลงในฐานข้อมูล โดยมีการแบ่งหน้าที่และการทำงานแบบ asynchronous และ synchronous ดังนี้

1. **`fetch_page_info(url: str)`**

* **หน้าที่:** ดึงข้อมูล title และ favicon จาก URL ที่กำหนดให้
* **ลักษณะการทำงาน:** เป็น asynchronous coroutine ที่ใช้ `aiohttp` ในการส่งคำร้องขอ HTTP และ `BeautifulSoup` ในการ parse HTML เพื่อดึงข้อมูล
* **อินพุต:** URL ของหน้าเว็บที่ต้องการดึงข้อมูล
* **เอาต์พุต:** คืนค่า tuple `(title, favicon_url)` หรือ `(None, None)` หากเกิดข้อผิดพลาด

2. **`fetch_page_info_and_update_sync(db_url: models.URL)`**

* **หน้าที่:** ดึงข้อมูล title และ favicon จาก URL ที่อยู่ในออบเจกต์ `db_url` แล้วอัปเดตข้อมูลเหล่านี้ลงในฐานข้อมูล
* **ลักษณะการทำงาน:** เป็น synchronous function ที่เรียกใช้ `fetch_page_info` แบบ asynchronous ภายใน thread pool เพื่อหลีกเลี่ยงการบล็อก event loop หลัก
* **อินพุต:** ออบเจกต์ `db_url` ที่มีข้อมูล URL ที่ต้องการดึงข้อมูลและอัปเดต
* **เอาต์พุต:** ไม่มีการคืนค่าโดยตรง แต่จะทำการอัปเดตข้อมูล title และ favicon ในฐานข้อมูล

3. **`async def fetch_page_info_and_update(db_url: models.URL)`**

* **หน้าที่:** เป็น wrapper สำหรับ `fetch_page_info_and_update_sync` เพื่อให้สามารถเรียกใช้ฟังก์ชัน synchronous ภายใน asynchronous context ได้
* **ลักษณะการทำงาน:** เป็น asynchronous coroutine ที่ใช้ `loop.run_in_executor` เพื่อเรียกใช้ `fetch_page_info_and_update_sync` ใน thread pool แบบ asynchronous
* **อินพุต:** ออบเจกต์ `db_url` ที่มีข้อมูล URL ที่ต้องการดึงข้อมูลและอัปเดต
* **เอาต์พุต:** ไม่มีการคืนค่าโดยตรง แต่จะทำการอัปเดตข้อมูล title และ favicon ในฐานข้อมูลผ่าน `fetch_page_info_and_update_sync`

**สรุปความสัมพันธ์**

* `fetch_page_info` เป็นฟังก์ชันหลักที่ทำหน้าที่ดึงข้อมูล title และ favicon
* `fetch_page_info_and_update_sync` เป็นฟังก์ชัน synchronous ที่เรียกใช้ `fetch_page_info` และอัปเดตฐานข้อมูล
* `fetch_page_info_and_update` เป็น wrapper asynchronous ที่เรียกใช้ `fetch_page_info_and_update_sync` ใน thread pool เพื่อให้สามารถทำงานร่วมกับส่วนอื่นๆ ของแอปพลิเคชันที่เป็น asynchronous ได้

**การทำงานร่วมกัน**

เมื่อมีการสร้าง short URL ใหม่ ฟังก์ชัน `create_url` จะเพิ่ม `fetch_page_info_and_update` ลงใน `BackgroundTasks` ทำให้ FastAPI เรียกใช้ฟังก์ชันนี้ในเบื้องหลังหลังจากส่ง response กลับไปให้ client แล้ว `fetch_page_info_and_update` จะเรียกใช้ `fetch_page_info_and_update_sync` ใน thread pool เพื่อดึงข้อมูล title และ favicon และอัปเดตฐานข้อมูล ทำให้การสร้าง short URL ไม่ถูกบล็อกโดยการดึงข้อมูล และแอปพลิเคชันยังคงตอบสนองต่อผู้ใช้ได้อย่างรวดเร็ว