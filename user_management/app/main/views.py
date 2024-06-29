from flask import Blueprint, render_template, redirect, session, url_for, flash, request
from flask_wtf.csrf import CSRFError

from app.models import EditableHTML

main = Blueprint('main', __name__)

# Custom error handler for CSRF token expiration
@main.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('errors/400.html'), 400
    # return render_template('errors/403.html', reason=e.description), 400


@main.route('/')
def index():
    return render_template('main/index.html')


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template(
        'main/about.html', editable_html_obj=editable_html_obj)
