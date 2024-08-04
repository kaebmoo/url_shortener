# user_management/app/main/forms.py

from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField

class DeleteURLForm(FlaskForm):
    url_secret_key = HiddenField()
    submit = SubmitField('Delete')

