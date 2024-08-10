from flask import Blueprint, render_template, redirect, session, url_for, flash, request, jsonify, current_app
from flask_wtf.csrf import CSRFError
from flask_login import current_user, login_required
import requests
from io import BytesIO
import base64
from PIL import Image
from qrcodegen import QrCode

from app.models import EditableHTML, ShortenedURL
from app.main.forms import DeleteURLForm

main = Blueprint('main', __name__)

# Custom error handler for CSRF token expiration
@main.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('errors/400.html'), 400

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

def get_user_urls():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'X-API-KEY': session.get('uid')
    }

    try:
        shortener_host = current_app.config['SHORTENER_HOST']
        response = requests.get(shortener_host + '/user/urls', headers=headers)
        if response.status_code == 200:
            user_urls = response.json()
            return user_urls
        else:
            return []
    except requests.exceptions.RequestException:
        return []

@main.route('/generate_qr_code')
@login_required
def generate_qr_code_endpoint():
    data = request.args.get('data')
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    qr_code_base64 = generate_qr_code(data)
    return jsonify({'qr_code': qr_code_base64})

@main.route('/')
def index():
    if current_user.is_authenticated:
        # user_urls = ShortenedURL.query.filter(ShortenedURL.api_key == current_user.uid, ShortenedURL.is_active == 1).all()
        user_urls = get_user_urls()
        url_count = len(user_urls)
        # จัดเรียงลิสต์ตาม 'created_at' โดยให้วันที่ใหม่ที่สุดมาก่อน
        sorted_user_urls = sorted(user_urls, key=lambda x: x['created_at'], reverse=True)
        
        shortener_host = current_app.config['SHORTENER_HOST']
        return render_template('main/index.html', user_urls=sorted_user_urls, shortener_host=shortener_host, url_count=url_count)
    return render_template('main/index.html', shortener_host=current_app.config['SHORTENER_HOST'])

@main.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    delete_form = DeleteURLForm()

    print("Form data:", request.form)  # Debug print

    if delete_form.validate_on_submit() and 'url_secret_key' in request.form:
        shortener_host = current_app.config['SHORTENER_HOST']
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'X-API-KEY': session.get('uid')
        }
        response = requests.delete(f'{shortener_host}/admin/{delete_form.url_secret_key.data}', headers=headers)
        if response.status_code == 200:
            flash('URL deleted successfully', 'success')
        else:
            flash('Failed to delete URL', 'danger')
        return redirect(url_for('main.user'))

    # user_urls = ShortenedURL.query.filter(ShortenedURL.api_key == current_user.uid, ShortenedURL.is_active == 1).all()
    user_urls = get_user_urls()
    url_count = len(user_urls)
    # จัดเรียงลิสต์ตาม 'created_at' โดยให้วันที่ใหม่ที่สุดมาก่อน
    sorted_user_urls = sorted(user_urls, key=lambda x: x['created_at'], reverse=True)
    
    shortener_host = current_app.config['SHORTENER_HOST']
    return render_template('main/user.html', user_urls=sorted_user_urls, shortener_host=shortener_host, url_count=url_count, delete_form=delete_form)

@main.route('/vip', methods=['GET', 'POST'])
@login_required
def vip():
    delete_form = DeleteURLForm()

    if delete_form.validate_on_submit() and 'url_secret_key' in request.form:
        shortener_host = current_app.config['SHORTENER_HOST']
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'X-API-KEY': session.get('uid')
        }
        response = requests.delete(f'{shortener_host}/admin/{delete_form.url_secret_key.data}', headers=headers)
        if response.status_code == 200:
            flash('URL deleted successfully', 'success')
        else:
            flash('Failed to delete URL', 'danger')
        return redirect(url_for('main.vip'))

    # user_urls = ShortenedURL.query.filter(ShortenedURL.api_key == current_user.uid, ShortenedURL.is_active == 1).all()
    user_urls = get_user_urls()
    url_count = len(user_urls)
    # จัดเรียงลิสต์ตาม 'created_at' โดยให้วันที่ใหม่ที่สุดมาก่อน
    sorted_user_urls = sorted(user_urls, key=lambda x: x['created_at'], reverse=True)

    shortener_host = current_app.config['SHORTENER_HOST']
    return render_template('main/vip.html', user_urls=sorted_user_urls, shortener_host=shortener_host, url_count=url_count, delete_form=delete_form)

@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template(
        'main/about.html', editable_html_obj=editable_html_obj)
