from flask_wtf import Form
from wtforms import TextField,PasswordField,HiddenField,IntegerField,RadioField,DateTimeField, validators
from wtforms.validators import DataRequired, Email, email_validator
from wtforms.fields.html5 import EmailField



class Login(Form):
    email = EmailField('Email', [DataRequired(), Email()])
    password = PasswordField('Password',validators=[DataRequired()])


class Signup(Form):
    email = EmailField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired()])
    passwordCheck = PasswordField('Confirm Password', [validators.EqualTo('password', message='Passwords must match')])

class addMovieScreening(Form):
    # movieid =
    startTime = DateTimeField('start', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    # endTime =
    screen = RadioField('screen', choices=['Screen 1', 'Screen 2', 'Screen 3', 'Screen 4'], validators=[DataRequired()])
