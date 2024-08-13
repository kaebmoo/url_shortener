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