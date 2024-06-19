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
