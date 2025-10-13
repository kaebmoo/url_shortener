user_management/app/account/views.py

```
@account.route('/login', methods=['GET', 'POST'])
def login():
    """Log in an existing user."""
    form = LoginForm()
    if form.validate_on_submit():
        # แบบเดิม - รองรับทั้ง email และ phone
        
        # login_method = request.form.get('login_method')
        # if login_method == 'email':
        #     user = User.query.filter_by(email=form.email.data).first()
        # else:
        #     user = User.query.filter_by(phone_number=form.phone_number.data).first()
        
        # แบบใหม่ - รองรับแค่ email
        user = User.query.filter_by(email=form.email.data).first()

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
    return render_template('account/login_email.html', form=form)

@account.route('/register', methods=['GET', 'POST'])
def register():
    # แบบเดิม - เลือกระหว่าง email หรือ phone
    # form = RegistrationFormSelect()
    # if form.validate_on_submit():
    #     registration_type = form.registration_type.data
    #     if registration_type == 'email':
    #         return redirect(url_for('account.register_email'))
    #     else:
    #         return redirect(url_for('account.register_phone'))
    # return render_template('account/register_select.html', form=form)
    
    # แบบใหม่ - ไปที่ register_email ตรง ๆ
    return redirect(url_for('account.register_email'))
```
