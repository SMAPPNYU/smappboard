from flask_wtf import Form
from wtforms.fields import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired

class ChangePermission(Form):
    dataset = StringField('dataset', validators=[DataRequired()], render_kw={"placeholder": "dataset"})
    permission = StringField('permission', validators=[DataRequired()], render_kw={"placeholder": "permission"})