from flask_wtf import Form
from wtforms import TextField,PasswordField,HiddenField,IntegerField,RadioField,SelectField,DateTimeField,StringField, validators, BooleanField
from wtforms.validators import DataRequired, Email, email_validator
from wtforms.fields.html5 import EmailField
from wtforms.widgets import CheckboxInput
from app import app,models

def fetchAllMovieTitles():
    allMovies = models.Movie.query.all()
    fetchAllMovieTitles = [movie.Name for movie in allMovies]
    return fetchAllMovieTitles

class Login(Form):
    email = EmailField('Email', [DataRequired(), Email()])
    password = PasswordField('Password',validators=[DataRequired()])


class Signup(Form):
    email = EmailField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired(), validators.length(min=8, max=25, message='Passwords must be between 8 and 25 characters long')])
    passwordCheck = PasswordField('Confirm Password', [validators.EqualTo('password', message='Passwords must match')])

class addMovieScreening(Form):
    movie = SelectField('movie', choices=fetchAllMovieTitles(), validators=[DataRequired()])
    screen = SelectField('screen', choices=['Screen 1', 'Screen 2', 'Screen 3', 'Screen 4', 'Screen 5', 'Screen 6'], validators=[DataRequired()])
    start = DateTimeField('start', validators=[DataRequired()], format='%d-%m-%Y %H:%M')
    end = DateTimeField('end', validators=[DataRequired()], format='%d-%m-%Y %H:%M')

    @classmethod
    def new(cls):
        # Instantiate the form
        form = cls()
        # Update the choices for the agency field
        form.movie.choices = fetchAllMovieTitles()
        return form

class enterMovie(Form):
    movietitle = StringField('Movie Name')

class selectNewMovie(Form):
    tmdbID = HiddenField('movieID')

class selectScreening(Form):
    screeningnumber = IntegerField('Screening Number', validators=[DataRequired()])

class addSeats(Form):
    seatnumber = IntegerField('Seat Number', validators=[DataRequired()])
    seatcategory = SelectField('Seat Category', choices=['Adult','Child','Senior'])

class UseCard(Form):
    CardID = IntegerField('Card ID')

class Paid(Form):
    Total = IntegerField('Total cost')

class searchForScreening(Form):
    searchMovie = StringField('Movie', validators=[DataRequired()])

class quickBook(Form):
    movie = SelectField('movie', choices=fetchAllMovieTitles(), validators=[DataRequired()])

    @classmethod
    def new(cls):
        # Instantiate the form
        form = cls()
        # Update the choices for the agency field
        form.movie.choices = fetchAllMovieTitles()
        return form

class changePasswordForm(Form):
    currentPassword = PasswordField('Current Password', [validators.DataRequired()])
    newPassword = PasswordField('New Password', [validators.DataRequired(), validators.length(min=8, max=25, message='Passwords must be between 8 and 25 characters long')])
    newPasswordCheck = PasswordField('Confirm New Password', [validators.EqualTo('newPassword', message='Passwords must match')])

class PaymentDetailsForm(Form):
    CardNo = StringField('Card Number', [validators.DataRequired(), validators.length(min=15, max=16, message='Card number should be 15 or 16 digits')], render_kw={"placeholder": "---- ---- ---- ----"})
    Name = StringField('Name on card', [validators.DataRequired(), validators.length(min=1, max=50, message='Please enter your name as it appears on your card')])
    Expiry = StringField('Expiry', render_kw={"placeholder": "MM-YY"}, validators=[DataRequired()])
    CVV = StringField('CVV', [validators.DataRequired(), validators.length(min=3, max=3, message='Security code should be 3 digits')], render_kw={"placeholder": "---"})
    Save = BooleanField('Save this card for next time', widget=CheckboxInput())

class SetUserPrivilage(Form):
    Username = StringField('Username', [validators.DataRequired()])
    Privilage = SelectField('Privilage', choices=['Admin', 'Staff', 'Basic'])