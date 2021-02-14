from flask_wtf import Form
from wtforms import TextField,PasswordField,HiddenField,IntegerField
from wtforms.validators import DataRequired, Email, email_validator
from wtforms.fields.html5 import EmailField



class Login(Form):
    email = EmailField('email', [DataRequired(), Email()])
    password = PasswordField('password',validators=[DataRequired()])


class Signup(Form):
    email = EmailField('username',validators=[DataRequired(),Email()])
    password = PasswordField('password',validators=[DataRequired()])
    name = TextField('name',validators=[DataRequired()])
    address = TextField('address',validators=[DataRequired()])


