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
