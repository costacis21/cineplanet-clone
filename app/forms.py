from flask_wtf import Form
from wtforms import TextField,PasswordField,HiddenField,IntegerField,RadioField,SelectField,DateTimeField,StringField, validators
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
    movie = screen = SelectField('movie', choices=['James Bond: Casino Royale', 'movie2', 'movie3'], validators=[DataRequired()])
    screen = SelectField('screen', choices=['Screen 1', 'Screen 2', 'Screen 3', 'Screen 4', 'Screen 5', 'Screen 6'], validators=[DataRequired()])
    starthours = SelectField('starthours', choices=['00', '01', '02', '03', '04', '05', '06', '07', '08', '09',
                                                    '10', '11', '12', '13', '14', '15', '16', '17', '18',
                                                    '19', '20', '21', '22', '23'],
                                    validators=[DataRequired()])
    startminutes = SelectField('startminutes', choices=['00', '01', '02', '03', '04', '05', '06', '07', '08', '09',
                                                    '10', '11', '12', '13', '14', '15', '16', '17', '18',
                                                    '19', '20', '21', '22', '23', '24', '25', '26', '27',
                                                    '28', '29', '30', '31', '32', '33', '34', '35', '36',
                                                    '37', '38', '39', '40', '41', '42', '43', '44', '45',
                                                    '46', '47', '48', '49', '50', '51', '52', '53', '54',
                                                    '55', '56', '57', '58', '59'],
                                    validators=[DataRequired()])
    endhours = SelectField('endhours', choices=['00', '01', '02', '03', '04', '05', '06', '07', '08', '09',
                                                    '10', '11', '12', '13', '14', '15', '16', '17', '18',
                                                    '19', '20', '21', '22', '23'],
                                    validators=[DataRequired()])
    endminutes = SelectField('endminutes', choices=['00', '01', '02', '03', '04', '05', '06', '07', '08', '09',
                                                    '10', '11', '12', '13', '14', '15', '16', '17', '18',
                                                    '19', '20', '21', '22', '23', '24', '25', '26', '27',
                                                    '28', '29', '30', '31', '32', '33', '34', '35', '36',
                                                    '37', '38', '39', '40', '41', '42', '43', '44', '45',
                                                    '46', '47', '48', '49', '50', '51', '52', '53', '54',
                                                    '55', '56', '57', '58', '59'],
                                    validators=[DataRequired()])

class enterMovie(Form):
    movietitle = StringField('Movie Name', validators=[DataRequired()])

class selectScreening(Form):
    screeningnumber = IntegerField('Screening Number', validators=[DataRequired()])

class addSeats(Form):
    seatnumber = IntegerField('Seat Number', validators=[DataRequired()])
    seatcategory = SelectField('Seat Category', choices=['Adult','Child','Senior'])

class enterPaymentDetails(Form):
    cardnumber = IntegerField('Card Number', validators=[DataRequired()])
    securitynumber = IntegerField('Security Number', validators=[DataRequired()])
