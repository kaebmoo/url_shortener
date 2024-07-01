from flask import Blueprint, render_template, redirect, session, url_for, flash, request, current_app
from flask_wtf.csrf import CSRFError
from flask_login import current_user, login_required

from app.models import EditableHTML, ShortenedURL

main = Blueprint('main', __name__)

# Custom error handler for CSRF token expiration
@main.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('errors/400.html'), 400
    # return render_template('errors/403.html', reason=e.description), 400


@main.route('/')
def index():
    if current_user.is_authenticated:
        user_urls = ShortenedURL.query.filter_by(api_key=current_user.uid, is_active=1).all()

        shortener_host = current_app.config['SHORTENER_HOST']
        return render_template('main/index.html', user_urls=user_urls, shortener_host=shortener_host)
    return render_template('main/index.html', shortener_host=current_app.config['SHORTENER_HOST'])


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template(
        'main/about.html', editable_html_obj=editable_html_obj)
