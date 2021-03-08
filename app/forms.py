from flask_wtf import Form
from wtforms import TextField,PasswordField,HiddenField,IntegerField,RadioField,SelectField,DateTimeField,StringField, validators
from wtforms.validators import DataRequired, Email, email_validator
from wtforms.fields.html5 import EmailField

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
    password = PasswordField('Password',validators=[DataRequired(), validators.length(min=8, max=25, message='Passwords must be 8 and 25 characters long')])
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

class enterPaymentDetails(Form):
    cardnumber = IntegerField('Card Number', validators=[DataRequired()])
    securitynumber = IntegerField('Security Number', validators=[DataRequired()])

class searchForScreening(Form):
    searchMovie = StringField('Movie', validators=[DataRequired()])
