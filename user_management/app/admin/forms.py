from flask_wtf import FlaskForm
from wtforms import ValidationError
# from wtforms.ext.sqlalchemy.fields import QuerySelectField
# from wtforms.fields import QuerySelectField
from wtforms_sqlalchemy.fields import QuerySelectField

from wtforms.fields import (
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.fields import DateField, EmailField, TelField
# from wtforms.fields.html5 import EmailField
from wtforms.validators import (
    Email,
    EqualTo,
    InputRequired,
    Length,
    DataRequired,
    URL as URLValidator,
)

from wtforms import FileField
from flask_wtf.file import FileAllowed, FileRequired

from app import db
from app.models import Role, User


class ChangeUserEmailForm(FlaskForm):
    email = EmailField(
        'New email', validators=[InputRequired(),
                                 Length(1, 64),
                                 Email()])
    submit = SubmitField('Update email')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class ChangeAccountTypeForm(FlaskForm):
    role = QuerySelectField(
        'New account type',
        validators=[InputRequired()],
        get_label='name',
        query_factory=lambda: db.session.query(Role).order_by('permissions'))
    submit = SubmitField('Update role')


class InviteUserForm(FlaskForm):
    role = QuerySelectField(
        'Account type',
        validators=[InputRequired()],
        get_label='name',
        query_factory=lambda: db.session.query(Role).order_by('permissions'))
    first_name = StringField(
        'First name', validators=[InputRequired(),
                                  Length(1, 64)])
    last_name = StringField(
        'Last name', validators=[InputRequired(),
                                 Length(1, 64)])
    email = EmailField(
        'Email', validators=[InputRequired(),
                             Length(1, 64),
                             Email()])
    submit = SubmitField('Invite')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class NewUserForm(InviteUserForm):
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            EqualTo('password2', 'Passwords must match.')
        ])
    password2 = PasswordField('Confirm password', validators=[InputRequired()])

    submit = SubmitField('Create')

class AddURLForm(FlaskForm):
    url = StringField('URL', validators=[DataRequired(), URLValidator()])
    category = StringField('Category', validators=[DataRequired()])
    reason = StringField('Reason', validators=[DataRequired()])
    source = StringField('Source', validators=[DataRequired()])
    submit = SubmitField('Add URL')

class ImportForm(FlaskForm):
    file = FileField('File', validators=[FileRequired(), FileAllowed(['csv', 'json'], 'CSV and JSON files only!')])
    submit = SubmitField('Import')