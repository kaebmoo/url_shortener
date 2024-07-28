from flask import (
    Flask,
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    jsonify, send_file, make_response, current_app
)

from flask_login import current_user, login_required, LoginManager, UserMixin, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm

import csv
import json
from io import StringIO, BytesIO
import os
from sqlalchemy.exc import IntegrityError
from dateutil.parser import parse as parse_date

from rq import Queue
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


from app import db
from app.admin.forms import (
    ChangeAccountTypeForm,
    ChangeUserEmailForm,
    InviteUserForm,
    NewUserForm,
    AddURLForm,
    ImportForm,
)
from app.decorators import admin_required
from app.email import send_email
from app.models import EditableHTML, Role, User, URL


admin = Blueprint('admin', __name__)

from redis import Redis
# Create a Redis connection (adjust the parameters accordingly)
redis_connection = Redis(host='localhost', port=6379, db=0)
# Create a queue using the Redis connection
queue = Queue(connection=redis_connection)

current_dir = os.path.dirname(os.path.abspath(__file__))

@admin.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard page."""
    return render_template('admin/index.html')

@admin.route('/blacklist', methods=['GET', 'POST'])
@login_required
@admin_required
def blacklist():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    urls = URL.query.paginate(page=page, per_page=per_page)
    form = AddURLForm()
    import_form = ImportForm()
    return render_template('admin/blacklist.html', urls=urls, form=form, import_form=import_form)

@admin.route('/blacklist/add', methods=['POST'])
@login_required
@admin_required
def blacklist_add_url():
    form = AddURLForm()
    if form.validate_on_submit():
        url = form.url.data
        category = form.category.data
        reason = form.reason.data
        source = form.source.data

        existing_url = URL.query.filter_by(url=url).first()
        if existing_url:
            return jsonify({'status': 'error', 'message': 'URL already exists'}), 400
        
        new_url = URL(url=url, category=category, reason=reason, source=source, date_added=db.func.current_date())
        db.session.add(new_url)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'URL added successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid input'}), 400


@admin.route('/blacklist/remove/<int:id>')
@login_required
@admin_required
def blacklist_remove_url(id):
    url = db.session.get(URL, id)
    if url is None:
        abort(404)
    db.session.delete(url)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'URL removed successfully'})

@admin.route('/blacklist/toggle/<int:id>')
@login_required
@admin_required
def blacklist_toggle_status(id):
    url = db.session.get(URL, id)
    if url is None:
        abort(404)
    url.status = not url.status
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Status updated successfully'})

@admin.route('/blacklist/search', methods=['GET'])
@login_required
@admin_required
def blacklist_search():
    query = request.args.get('query', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    urls = URL.query.filter(
        (URL.url.like(f'%{query}%')) |
        (URL.category.like(f'%{query}%')) |
        (URL.reason.like(f'%{query}%')) |
        (URL.source.like(f'%{query}%'))
    ).paginate(page=page, per_page=per_page)
    form = AddURLForm()
    import_form = ImportForm()
    return render_template('admin/blacklist.html', urls=urls, query=query, form=form, import_form=import_form)

@admin.route('/blacklist/export/<format>', methods=['GET'])
@login_required
@admin_required
def blacklist_export_data(format):
    urls = URL.query.all()
    if format == 'csv':
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['url', 'category', 'date_added', 'reason', 'source', 'status'])
        for url in urls:
            cw.writerow([url.url, url.category, url.date_added, url.reason, url.source, url.status])
            current_app.socketio.emit('export_progress', {'status': 'Exporting data...', 'url': url.url})
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=urls.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    elif format == 'json':
        data = [{'url': url.url, 'category': url.category, 'date_added': str(url.date_added), 
                 'reason': url.reason, 'source': url.source, 'status': url.status} for url in urls]
        output = BytesIO(json.dumps(data, indent=2).encode('utf-8'))
        current_app.socketio.emit('export_progress', {'status': 'Exporting data...', 'total': len(data)})
        return send_file(output, mimetype='application/json', as_attachment=True, download_name='urls.json')
    else:
        return jsonify({'error': 'Invalid format'}), 400

@admin.route('/blacklist/import', methods=['POST'])
@login_required
@admin_required
def blacklist_import_data():
    form = ImportForm()
    if form.validate_on_submit():
        if 'file' not in request.files:
            flash('No file part', 'error')
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return jsonify({'error': 'No selected file'}), 400
        
        try:
            count = 0
            if file and file.filename.endswith('.csv'):
                stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_reader = csv.DictReader(stream)
                total_rows = sum(1 for row in csv_reader)
                stream.seek(0)
                csv_reader = csv.DictReader(stream)
                
                for row in csv_reader:
                    existing_url = URL.query.filter_by(url=row['url']).first()
                    if existing_url:
                        continue
                    url = URL(url=row['url'], category=row['category'], 
                            date_added=parse_date(row['date_added']).date(), 
                            reason=row['reason'], source=row['source'], status=row['status'] in ['1', 'True'])
                    db.session.add(url)
                    count += 1
                    if count % 100 == 0:
                        current_app.socketio.emit('import_progress', {'status': 'Importing data...', 'count': count, 'total': total_rows})
                db.session.commit()
                return jsonify({'message': 'CSV imported successfully'}), 200
            elif file and file.filename.endswith('.json'):
                data = json.load(file)
                total_rows = len(data)
                for index, item in enumerate(data):
                    existing_url = URL.query.filter_by(url=item['url']).first()
                    if existing_url:
                        continue
                    url = URL(url=item['url'], category=item['category'], 
                            date_added=parse_date(item['date_added']).date(), 
                            reason=item['reason'], source=item['source'], status=item['status'])
                    db.session.add(url)
                    count += 1
                    if count % 100 == 0:
                        current_app.socketio.emit('import_progress', {'status': 'Importing data...', 'count': count, 'total': total_rows})
                db.session.commit()
                return jsonify({'message': 'JSON imported successfully'}), 200
            else:
                return jsonify({'error': 'Invalid file format'}), 400
        except IntegrityError:
            db.session.rollback()
            return jsonify({'error': 'An error occurred while importing data'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'CSRF token missing or incorrect'}), 400

@admin.route('/new-user', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    """Create a new user."""
    form = NewUserForm()
    if form.validate_on_submit():
        user = User(
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User {} successfully created'.format(user.full_name()),
              'form-success')
    return render_template('admin/new_user.html', form=form)


@admin.route('/invite-user', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_user():
    """Invites a new user to create an account and set their own password."""
    form = InviteUserForm()
    if form.validate_on_submit():
        user = User(
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        invite_link = url_for(
            'account.join_from_invite',
            user_id=user.id,
            token=token,
            _external=True)
        queue.enqueue(
            send_email,
            recipient=user.email,
            subject='You Are Invited To Join',
            template='account/email/invite',
            user=user,
            invite_link=invite_link,
        )
        flash('User {} successfully invited'.format(user.full_name()),
              'form-success')
    return render_template('admin/new_user.html', form=form)


@admin.route('/users')
@login_required
@admin_required
def registered_users():
    """View all registered users."""
    users = User.query.all()
    roles = Role.query.all()
    return render_template(
        'admin/registered_users.html', users=users, roles=roles)


@admin.route('/user/<int:user_id>')
@admin.route('/user/<int:user_id>/info')
@login_required
@admin_required
def user_info(user_id):
    """View a user's profile."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/change-email', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_email(user_id):
    """Change a user's email."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    form = ChangeUserEmailForm()
    if form.validate_on_submit():
        user.email = form.email.data
        db.session.add(user)
        db.session.commit()
        flash('Email for user {} successfully changed to {}.'.format(
            user.full_name(), user.email), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route(
    '/user/<int:user_id>/change-account-type', methods=['GET', 'POST'])
@login_required
@admin_required
def change_account_type(user_id):
    """Change a user's account type."""
    if current_user.id == user_id:
        flash('You cannot change the type of your own account. Please ask '
              'another administrator to do this.', 'error')
        return redirect(url_for('admin.user_info', user_id=user_id))

    user = User.query.get(user_id)
    if user is None:
        abort(404)
    form = ChangeAccountTypeForm()
    if form.validate_on_submit():
        user.role = form.role.data
        db.session.add(user)
        db.session.commit()
        flash('Role for user {} successfully changed to {}.'.format(
            user.full_name(), user.role.name), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route('/user/<int:user_id>/delete')
@login_required
@admin_required
def delete_user_request(user_id):
    """Request deletion of a user's account."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/_delete')
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user's account."""
    if current_user.id == user_id:
        flash('You cannot delete your own account. Please ask another '
              'administrator to do this.', 'error')
    else:
        user = User.query.filter_by(id=user_id).first()
        db.session.delete(user)
        db.session.commit()
        flash('Successfully deleted user %s.' % user.full_name(), 'success')
    return redirect(url_for('admin.registered_users'))


@admin.route('/_update_editor_contents', methods=['POST'])
@login_required
@admin_required
def update_editor_contents():
    """Update the contents of an editor."""

    edit_data = request.form.get('edit_data')
    editor_name = request.form.get('editor_name')

    editor_contents = EditableHTML.query.filter_by(
        editor_name=editor_name).first()
    if editor_contents is None:
        editor_contents = EditableHTML(editor_name=editor_name)
    editor_contents.value = edit_data

    db.session.add(editor_contents)
    db.session.commit()

    return 'OK', 200
