from flask import url_for, current_app
from wtforms.fields import Field
from wtforms.widgets import HiddenInput
import sys
import random

import base64
from PIL import Image
from qrcodegen import QrCode
from io import BytesIO

from datetime import datetime
import pytz

# from wtforms.compat import text_type
if sys.version_info[0] >= 3:
    text_type = str
    string_types = (str,)
    izip = zip

def register_template_utils(app):
    """Register Jinja 2 helpers (called from __init__.py)."""

    @app.template_test()
    def equalto(value, other):
        return value == other

    @app.template_global()
    def is_hidden_field(field):
        from wtforms.fields import HiddenField
        return isinstance(field, HiddenField)

    app.add_template_global(index_for_role)


def index_for_role(role):
    return url_for(role.index)


class CustomSelectField(Field):
    widget = HiddenInput()

    def __init__(self, label='', validators=None, multiple=False,
                 choices=[], allow_custom=True, **kwargs):
        super(CustomSelectField, self).__init__(label, validators, **kwargs)
        self.multiple = multiple
        self.choices = choices
        self.allow_custom = allow_custom

    def _value(self):
        return text_type(self.data) if self.data is not None else ''

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist[1]
            self.raw_data = [valuelist[1]]
        else:
            self.data = ''

def generate_otp():
    return random.randint(1000, 9999)

def generate_qr_code(data):
    qr = QrCode.encode_text(data, QrCode.Ecc.MEDIUM)
    size = qr.get_size()
    scale = 5
    img_size = size * scale
    img = Image.new('1', (img_size, img_size), 'white')

    for y in range(size):
        for x in range(size):
            if qr.get_module(x, y):
                for dy in range(scale):
                    for dx in range(scale):
                        img.putpixel((x * scale + dx, y * scale + dy), 0)

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def convert_to_localtime(utc_timestamp):
    if utc_timestamp is None:
        return ''  # or return a default value like an empty string or a specific date
    try:
        timezone_str = current_app.config.get('TIMEZONE', 'Asia/Bangkok')
        utc_time = datetime.strptime(utc_timestamp, '%Y-%m-%dT%H:%M:%S')
        utc_time = utc_time.replace(tzinfo=pytz.utc)
        local_timezone = pytz.timezone(timezone_str)
        local_time = utc_time.astimezone(local_timezone)
        return local_time.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error converting time: {e}")
        return utc_timestamp  # return the original timestamp if there's an error
    
from urllib.parse import urlparse
from playwright.async_api import async_playwright
import logging 
import asyncio
import aiohttp
from aiohttp.client_exceptions import ClientConnectorError
import os

def validate_and_correct_url(url: str) -> str:
    if not urlparse(url).scheme:
        # ถ้าไม่มี schema เพิ่ม "http://"
        url = f"http://{url}"
    return url

def validate_url(url):
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return False
    return True


async def fetch_content_type(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url) as response:
                return response.headers.get('Content-Type')
    except ClientConnectorError as e:
        print(f"Connection error: {e}")
        return None
        
async def capture_screenshot(url: str):
    '''content_type = await fetch_content_type(url)
    if 'text/html' not in content_type:
        print(f"URL is not an HTML page, content type: {content_type}")
        return None
    '''    
    async with async_playwright() as playwright:
        parsed_url = urlparse(url)
        # Replace '/' with '_' to create a valid file name
        file_name = f"{parsed_url.netloc}{parsed_url.path.replace('/', '_')}.png"
        # Save the screenshot in the 'static' folder
        # output_path = f"user_management/app/static/screenshots/{file_name}"
        output_path = os.path.join(current_app.root_path, "static", "screenshots", file_name)

        # chromium = playwright.chromium
        # browser = await chromium.launch(headless=True)
        firefox = playwright.firefox
        browser = await firefox.launch(headless=True)

        # page = await browser.new_page(viewport={'width': 1280, 'height': 720})

        # สร้าง context ใหม่พร้อมกำหนด User-Agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.4472.124 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()

        try:
            response = await page.goto(url, timeout=30000, wait_until="load") # , wait_until="domcontentloaded"
            status = response.status
            destination_url = response.url
        except Exception as e:
            print("The page took too long to load or cannot be accessed.")
            logging.error(f"Error: {e}")
            return None

        
        await page.screenshot(path=output_path, full_page=False)
        await browser.close()

        return file_name, destination_url, status  # Return just the file name, not the full path
