from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, IPAddress

class AddNodeForm(FlaskForm):
    ip = StringField('IP Address', validators=[DataRequired(), IPAddress()])
    submit = SubmitField('Add Node')

class RemoveNodeForm(FlaskForm):
    ip = StringField('IP Address', validators=[DataRequired(), IPAddress()])
    submit = SubmitField('Remove Node')

class AddAreaForm(FlaskForm):
    name = StringField('Area Name', validators=[DataRequired()])
    submit = SubmitField('Add Area')

class RemoveAreaForm(FlaskForm):
    name = StringField('Area Name', validators=[DataRequired()])
    submit = SubmitField('Remove Area')