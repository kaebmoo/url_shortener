from flask import Blueprint, render_template, redirect, session, url_for, flash, request
from app.url.forms import URLShortenForm
import requests
from flask_wtf.csrf import CSRFError
from qrcodegen import QrCode
from PIL import Image
import io
import base64


from app.models import EditableHTML

shorten = Blueprint('shorten', __name__)

# Custom error handler for CSRF token expiration
@shorten.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('errors/400.html'), 400
    # return render_template('errors/403.html', reason=e.description), 400

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

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

@shorten.route('/shorten', methods=['GET', 'POST'])
def shorten_url():
    message = None  # กำหนดค่าเริ่มต้น
    short_url = None  # กำหนดค่าเริ่มต้น
    qr_code_base64 = None

    form = URLShortenForm()
    if form.validate_on_submit():
        original_url = form.original_url.data
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'X-API-KEY': session.get('uid')  # ใส่ API key ของคุณ
        }
        data = {
            'target_url': original_url
        }
        try:
            response = requests.post('http://127.0.0.1:8000/url', headers=headers, json=data)
            data = response.json()
            if response.status_code == 200:
                short_url = data.get('url', 'No URL returned')
                message = data.get('message', 'Successfully created')
                flash(f'{message}', 'success')
                qr_code_base64 = generate_qr_code(short_url)

                # if 'persistent_messages' not in session:
                #     session['persistent_messages'] = []
                # session['persistent_messages'] = message
                # session.modified = True  # เพื่อให้แน่ใจว่า session ถูกบันทึก
            elif response.status_code == 400:
                message = data.get('detail', '')
                flash('Error 400 Bad Request', 'error')
            else:
                message = data.get('detail', '')
                flash('Failed to shorten URL.', 'danger')
        except requests.exceptions.ConnectionError:
            flash('Failed to connect to the server. Please try again later.', 'error')
        except requests.exceptions.HTTPError as http_err:
            flash(f'HTTP error occurred: {http_err}', 'error')
        except requests.exceptions.RequestException as req_err:
            flash(f'An error occurred: {req_err}', 'error')
        except Exception as e:
            flash(f'An unexpected error occurred: {e}', 'error')
        ## return redirect(url_for('main.shorten'))
    # persistent_messages = session.get('persistent_messages', [])
    return render_template('url/shorten.html', form=form, message=message, short_url=short_url, qr_code_base64=qr_code_base64)
    
    
