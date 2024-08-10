# gogoth
## Secure Shortened URL

### Build a URL Shortener With FastAPI and Python

> _Adapted from_ [https://realpython.com/build-a-python-url-shortener-with-fastapi/](https://realpython.com/build-a-python-url-shortener-with-fastapi/)

**Key Updates:**

*   **Pydantic V2 Support:** The source code has been enhanced to seamlessly work with pydantic version 2.
*   **Additional Settings:** `pydantic-settings` has been integrated for more configuration options.
*   **Migration Guide:** For detailed information on the migration process, refer to [https://docs.pydantic.dev/latest/migration/](https://docs.pydantic.dev/latest/migration/)
*   **Code Transformation:** The source code has been modified using `bump-pydantic`, with the `config.py` file being the primary target of changes.
*   **Websocket Integration:** Real-time URL updates are now supported through websockets.
*   **Asynchronous Page Info Retrieval:** Title and favicon extraction from target URLs is performed asynchronously using `asyncio` and `aiohttp` to improve responsiveness.
*   **API Key Management:** A new endpoint for registering API keys has been added, along with enhanced API key verification and role-based access control.
*   **Blacklisting:** URLs can now be blacklisted to prevent shortening of undesired content.
*   **Custom Key Support:** Users with appropriate permissions can now create short URLs with custom keys.
*   **User Information:** Endpoints for retrieving the count of shortened URLs and a list of shortened URLs for a specific user have been added.
*   **Enhanced Error Handling:** Improved HTTP exception handling and informative error messages.

**Running the Live Server**

You have two options for launching the live server:

1.  **Using uvicorn:**

    ```bash
    uvicorn shortener_app.main:app --reload
    ```

2.  **With Python3:**

    ```bash
    python3 -m uvicorn shortener_app.main:app --reload


### Key Functions and Endpoints in `main.py`

The `main.py` file serves as the core of your URL shortening API, housing essential functions and endpoints to handle various aspects of the application. Here's a breakdown of its key components:

**Helper Functions**

*   **`get_admin_info`:** Constructs user-friendly URLs for managing shortened link data, incorporating QR code generation.
*   **`raise_*` functions:** Define custom HTTP exceptions for common error scenarios like 404 (Not Found), 400 (Bad Request), 401 (Unauthorized), and others, enhancing error handling and user experience.
*   **`get_db`, `get_api_db`, `get_blacklist_db`:** Establish database connections for the main URL data, API keys, and blacklisted URLs, respectively, ensuring proper database interaction.
*   **`verify_jwt_token`, `create_access_token`, `refresh_token`:** Implement JWT-based authentication and token management for secure user access control.
*   **`verify_api_key`:** Validates API keys against the database, ensuring only authorized requests are processed.
*   **`fetch_page_info`, `fetch_page_info_and_update_sync`, `fetch_page_info_and_update`:** Asynchronously retrieve title and favicon information from target URLs using `asyncio` and `aiohttp`, improving application responsiveness.
*   `normalize_url`: Standardizes URLs by handling trailing slashes consistently.
*   `generate_qr_code`: Generates QR codes for shortened URLs, enhancing user experience and sharing capabilities.
*   `custom_openapi`: Customizes the OpenAPI schema for improved documentation and clarity.

**API Endpoints**

*   **`/`:** A simple welcome message endpoint.
*   **`/about`:** An HTML page providing information about the URL shortener.
*   **`/api/register_api_key`:** Registers new API keys, enabling secure access to the API.
*   **`/{url_key}`:** Redirects users from shortened URLs to their original targets, handling potential errors gracefully.
*   **`/url`:** Creates new shortened URLs, optionally with custom keys (for authorized users), and initiates background tasks to fetch page information.
*   **`/user/info`:** Provides user-specific information like the count of shortened URLs.
*   **`/user/urls`:** Retrieves a list of shortened URLs created by a specific user.
*   **`/admin/{secret_key}`:** Fetches detailed information and management options for a shortened URL based on its secret key.
*   **`/admin/{secret_key}` (DELETE):** Deletes a shortened URL based on its secret key.
*   **`/ws/url_update/{secret_key}`:** A websocket endpoint for real-time updates on URL information.

This enhanced description provides a more comprehensive overview of the key functions and endpoints within `main.py`, highlighting their roles in URL shortening, user management, asynchronous operations, and overall API functionality.


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