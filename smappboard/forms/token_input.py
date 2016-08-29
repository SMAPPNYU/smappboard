from flask.ext.wtf import Form
from wtforms.fields import StringField, SubmitField
from wtforms.validators import DataRequired

class CreateUser(Form):
    consumer_key = StringField('consumer_key', validators=[DataRequired()], render_kw={"placeholder": "your username"})
    consumer_secret = StringField('consumer_secret', validators=[DataRequired()], render_kw={"placeholder": "your username"})
    access_token = StringField('access_token', validators=[DataRequired()], render_kw={"placeholder": "your username"})
    access_token_secret = StringField('access_token_secret', validators=[DataRequired()], render_kw={"placeholder": "your username"})
'''
author @yvan
'''