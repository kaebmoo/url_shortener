from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL

class URLShortenForm(FlaskForm):
    original_url = StringField('Enter URL', validators=[DataRequired(), URL()])
    submit = SubmitField('Shorten URL')
