from flask_wtf import Form
from wtforms import TextField,PasswordField,HiddenField,IntegerField,RadioField,DateTimeField
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

class addMovieScreening(Form):
    # movieid =
    startTime = DateTimeField('start', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    # endTime =
    screen = RadioField('screen', choices=['Screen 1', 'Screen 2', 'Screen 3', 'Screen 4'], validators=[DataRequired()])
