from flask_wtf import Form
from wtforms.fields import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired

#{"value": "#JointSession", "date_added": "Tue Feb 28 15:27:01 +0000 2017", "date_removed": null, "filter_type": "track", "turnoff_date": null, "active": true}
class AddTerm(Form):
    value = StringField('value', validators=[DataRequired()], render_kw={"placeholder": "value"})
    filter_type = StringField('filter_type', validators=[DataRequired()], render_kw={"placeholder": "type of filter"})