from flask import Blueprint, flash, redirect, render_template, request, url_for, session, current_app
from flask_login import current_user, login_required, login_user, logout_user

from rq import Queue
# from flask_rq import get_queue <-- deprecated

from app import db
from app.account.forms import (
    ChangeEmailForm, ChangePhoneForm, ChangePasswordForm, 
    CreatePasswordForm, LoginForm, RegistrationFormSelect, 
    RegistrationForm, PhoneNumberForm, RequestResetPasswordForm, 
    ResetPasswordForm, OTPForm, 
)
from app.email import send_email
from app.models import User
from app.utils import generate_otp
from app.sms import send_otp
from app.apicall import register_api_key, create_jwt_token, create_refresh_token

from werkzeug.security import check_password_hash, generate_password_hash
import uuid
from email_validator import validate_email, EmailNotValidError
import phonenumbers

from redis import Redis

account = Blueprint('account', __name__)


# Create a Redis connection (adjust the parameters accordingly) RQ_DEFAULT_HOST RQ_DEFAULT_PORT
redis_connection = Redis(host='127.0.0.1', port=6379, db=0)

# Create a queue using the Redis connection
queue = Queue(connection=redis_connection)


# get_queue() is deprecated use queue instead.

# Configure the connection to the queue (e.g., Redis)
## queue = Queue(connection='redis://localhost:6379')  # Replace with your actual connection details

@account.route('/login', methods=['GET', 'POST'])
def login():
    """Log in an existing user."""
    form = LoginForm()
    if form.validate_on_submit():
        login_method = request.form.get('login_method')
        if login_method == 'email':
            user = User.query.filter_by(email=form.email.data).first()
        else:
            user = User.query.filter_by(phone_number=form.phone_number.data).first()

        if user is not None and user.password_hash is not None and \
                user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            flash('You are now logged in. Welcome back!', 'success')
            # เก็บค่า uid, email, phone, หรืออื่น อื่น ใน session
            session['uid'] = user.uid
            access_token = create_jwt_token()
            session['access_token'] = access_token

            return redirect(request.args.get('next') or url_for('main.index'))
        else:
            flash('Invalid email, phone or password.', 'error')
    return render_template('account/login.html', form=form)

@account.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationFormSelect()
    if form.validate_on_submit():
        registration_type = form.registration_type.data
        if registration_type == 'email':
            return redirect(url_for('account.register_email'))
        else:
            return redirect(url_for('account.register_phone'))
    return render_template('account/register_select.html', form=form)

@account.route('/register_email', methods=['GET', 'POST'])
def register_email():
    """Register a new user, and send them a confirmation email."""
    form = RegistrationForm()
    if form.validate_on_submit():
        uid = uuid.uuid4().hex
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone_number = '',
            email=form.email.data,
            uid = uid,
            password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        confirm_link = url_for('account.confirm', token=token, _external=True)

        queue.enqueue(
            send_email,
            recipient=user.email,
            subject='Confirm Your Account',
            template='account/email/confirm',
            user=user,
            confirm_link=confirm_link)
        flash('A confirmation link has been sent to {}.'.format(user.email),
              'warning')
        return redirect(url_for('main.index'))
    return render_template('account/register.html', form=form)

@account.route('/register_phone', methods=['GET', 'POST'])
def register_phone():
    form = PhoneNumberForm()
    if form.validate_on_submit():
        otp = generate_otp()
        queue.enqueue(send_otp, phone_number=form.phone_number.data, otp=otp)
        # send_otp(phone_number, otp)
        
        session['otp'] = otp
        session['first_name'] = form.first_name.data
        session['last_name'] = form.last_name.data
        session['phone_number'] = form.phone_number.data
        session['password'] = form.password.data  # You should hash the password
        
        return redirect(url_for('account.verify_otp'))
    return render_template('account/register_phone.html', form=form)



@account.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@account.route('/manage', methods=['GET', 'POST'])
@account.route('/manage/info', methods=['GET', 'POST'])
@login_required
def manage():
    """Display a user's account information."""
    try:
        validate_email(current_user.email, check_deliverability=False)
        email_or_phone = current_user.email
        is_email = True
    except EmailNotValidError:
        # Handle invalid email
        # It is the UID in the email, it is the user who registered with the phone number. 
        # bring phone number information to display instead.
        phone_number = phonenumbers.parse(current_user.phone_number, "TH")
        phone_number = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.NATIONAL)
        email_or_phone = phone_number
        is_email = False
    return render_template('account/manage.html', user=current_user, email_or_phone=email_or_phone, is_email=is_email, form=None)


@account.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Respond to existing user's request to reset their password."""
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = RequestResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_password_reset_token()
            reset_link = url_for(
                'account.reset_password', token=token, _external=True)
            queue.enqueue(
                send_email,
                recipient=user.email,
                subject='Reset Your Password',
                template='account/email/reset_password',
                user=user,
                reset_link=reset_link,
                next=request.args.get('next'))
        flash('A password reset link has been sent to {}.'.format(
            form.email.data), 'warning')
        return redirect(url_for('account.login'))
    return render_template('account/reset_password.html', form=form)


@account.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset an existing user's password."""
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('Invalid email address.', 'form-error')
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.new_password.data):
            flash('Your password has been updated.', 'form-success')
            return redirect(url_for('account.login'))
        else:
            flash('The password reset link is invalid or has expired.',
                  'form-error')
            return redirect(url_for('main.index'))
    return render_template('account/reset_password.html', form=form)


@account.route('/manage/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change an existing user's password."""
    form = ChangePasswordForm()
    try:
        validate_email(current_user.email, check_deliverability=False)
        is_email = True
    except EmailNotValidError:
        # Handle invalid email
        # It is the UID in the email, it is the user who registered with the phone number. 
        # bring phone number information to display instead.
        is_email = False
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.new_password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.', 'form-success')
            return redirect(url_for('main.index'))
        else:
            flash('Original password is invalid.', 'form-error')
    return render_template('account/manage.html', form=form, is_email=is_email)


@account.route('/manage/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    """Respond to existing user's request to change their email."""
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            change_email_link = url_for(
                'account.change_email', token=token, _external=True)
            queue.enqueue(
                send_email,
                recipient=new_email,
                subject='Confirm Your New Email',
                template='account/email/change_email',
                # current_user is a LocalProxy, we want the underlying user
                # object
                user=current_user._get_current_object(),
                change_email_link=change_email_link)
            flash('A confirmation link has been sent to {}.'.format(new_email),
                  'warning')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.', 'form-error')
    return render_template('account/manage.html', form=form, is_email=True)

@account.route('/manage/change-phone', methods=['GET', 'POST'])
@login_required
def change_phone_request():
    """Respond to existing user's request to change their email."""
    form = ChangePhoneForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            session['user_id'] = current_user.id
            new_phone = form.phone_number.data
            session['phone_number'] = new_phone
            # send otp to confirm new phone number
            otp = generate_otp()
            session['otp'] = otp
            queue.enqueue(send_otp, phone_number=new_phone, otp=otp)
            
            flash('A confirmation otp has been sent to {}.'.format(new_phone),
                  'warning')
            return redirect(url_for('account.confirm_otp'))
        else:
            flash('Invalid email or password.', 'form-error')
    return render_template('account/manage.html', form=form, is_email=False)

@account.route('/manage/change-email/<token>', methods=['GET', 'POST'])
@login_required
def change_email(token):
    """Change existing user's email with provided token."""
    if current_user.change_email(token):
        flash('Your email address has been updated.', 'success')
    else:
        flash('The confirmation link is invalid or has expired.', 'error')
    return redirect(url_for('main.index'))


@account.route('/confirm-account')
@login_required
def confirm_request():
    """Respond to new user's request to confirm their account."""
    token = current_user.generate_confirmation_token()
    confirm_link = url_for('account.confirm', token=token, _external=True)
    queue.enqueue(
        send_email,
        recipient=current_user.email,
        subject='Confirm Your Account',
        template='account/email/confirm',
        # current_user is a LocalProxy, we want the underlying user object
        user=current_user._get_current_object(),
        confirm_link=confirm_link)
    flash('A new confirmation link has been sent to {}.'.format(
        current_user.email), 'warning')
    return redirect(url_for('main.index'))


@account.route('/confirm-account/<token>')
@login_required
def confirm(token):
    """Confirm new user's account with provided token."""
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm_account(token):
        flash('Your account has been confirmed.', 'success')
        # send uid as api_key to fastapi here. email register confirmed.
        register_api_key(current_user.uid, current_user.role_id)
    else:
        flash('The confirmation link is invalid or has expired.', 'error')
    return redirect(url_for('main.index'))

# for confirm when user change phone number
@account.route('/confirm_phone', methods=['GET', 'POST'])
def confirm_otp():
    form = OTPForm()
    if form.validate_on_submit():
        entered_otp = form.otp.data
        if entered_otp == str(session.get('otp')):
            user_id = session.get('user_id')
            phone_number = session.get('phone_number')
            
            user = db.session.query(User).filter_by(id=user_id).first()
            current_user.phone_number = phone_number

            db.session.add(user)
            db.session.commit()
            # login_user(user)
            
            session.pop('otp', None)
            session.pop('phone_number', None)
            flash('Your phone number has been successfully verified and changed.', 'success')
            return redirect(url_for('account.manage'))  # Adjust to your dashboard route
        else:
            flash('Invalid OTP.', 'error')
    return render_template('account/verify_otp.html', form=form)

# for register user by phone
@account.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    form = OTPForm()
    if form.validate_on_submit():
        entered_otp = form.otp.data
        if entered_otp == str(session.get('otp')):
            first_name = session.get('first_name')
            last_name = session.get('last_name')
            phone_number = session.get('phone_number')
            password = session.get('password')
            uid = uuid.uuid4().hex
            session['uid'] = uid
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=uid, # Assuming email is not used for phone registration
                uid = uid,
                phone_number=phone_number, 
                password=password, 
                confirmed=True)  # You should hash the password
            db.session.add(user)
            db.session.commit()
            login_user(user)
            session.pop('otp', None)
            session.pop('phone_number', None)
            session.pop('password', None)
            flash('Phone number verified and registered successfully!', 'success')
            # send uid as api_key to fastapi here. phone register confirmed.
            register_api_key(uid, 1)

            return redirect(url_for('main.index'))  # Adjust to your dashboard route
        else:
            flash('Invalid OTP.', 'error')
    return render_template('account/verify_otp.html', form=form)


@account.route(
    '/join-from-invite/<int:user_id>/<token>', methods=['GET', 'POST'])
def join_from_invite(user_id, token):
    """
    Confirm new user's account with provided token and prompt them to set
    a password.
    """
    if current_user is not None and current_user.is_authenticated:
        flash('You are already logged in.', 'error')
        return redirect(url_for('main.index'))

    new_user = User.query.get(user_id)
    if new_user is None:
        return redirect(404)

    if new_user.password_hash is not None:
        flash('You have already joined.', 'error')
        return redirect(url_for('main.index'))

    if new_user.confirm_account(token):
        form = CreatePasswordForm()
        if form.validate_on_submit():
            new_user.password = form.password.data
            db.session.add(new_user)
            db.session.commit()
            # send api_key, role_id to fastapi
            register_api_key(new_user.uid, new_user.role_id)
            #
            flash('Your password has been set. After you log in, you can '
                  'go to the "Your Account" page to review your account '
                  'information and settings.', 'success')
            return redirect(url_for('account.login'))
        return render_template('account/join_invite.html', form=form)
    else:
        flash('The confirmation link is invalid or has expired. Another '
              'invite email with a new link has been sent to you.', 'error')
        token = new_user.generate_confirmation_token()
        invite_link = url_for(
            'account.join_from_invite',
            user_id=user_id,
            token=token,
            _external=True)
        queue.enqueue(
            send_email,
            recipient=new_user.email,
            subject='You Are Invited To Join',
            template='account/email/invite',
            user=new_user,
            invite_link=invite_link)
    return redirect(url_for('main.index'))


@account.before_app_request
def before_request():
    """Force user to confirm email before accessing login-required routes."""
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint[:8] != 'account.' \
            and request.endpoint != 'static':
        return redirect(url_for('account.unconfirmed'))


@account.route('/unconfirmed')
def unconfirmed():
    """Catch users with unconfirmed emails."""
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('account/unconfirmed.html')
