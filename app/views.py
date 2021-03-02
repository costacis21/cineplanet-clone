from flask import flash, render_template, redirect, url_for, session, request
from flask_login import current_user, login_user, logout_user
from app import app,models,forms,db,admin
from datetime import datetime
from passlib.hash import sha256_crypt
import logging


# FLASK ADMIN setup
# remove before deployment
from flask_admin.contrib.sqla import ModelView
admin.add_view(ModelView(models.User, db.session))
admin.add_view(ModelView(models.Screening, db.session))
admin.add_view(ModelView(models.Booking, db.session))
admin.add_view(ModelView(models.Ticket, db.session))
admin.add_view(ModelView(models.Seat, db.session))
admin.add_view(ModelView(models.Movie, db.session))

from imdbSearch import getMovieInfo

def resetBookingSessionData():
    #Used to reset the session data stored about a booking
    #Prevents previous complete or incomplete bookings from interfering with any new ones
    #Called when the homepage is loaded
    session['bookingProgress'] = 0
    session['movie'] = ''
    session['screening'] = 0
    session['seats'] = []
    session['total'] = 0

@app.route('/', methods=['GET','POST'])
def index():
    resetBookingSessionData()
    if current_user.is_authenticated:
        allScreenings = models.Screening.query.all()
        numScreenings = len(allScreenings)
        theMovies = []
        for screening in allScreenings:
            movie = models.Movie.query.filter_by(MovieID=screening.MovieID).all()
            theMovies.append(movie[0])
        searchForScreening = forms.searchForScreening()
        if request.method == 'POST':
            if request.form.get("Search"):
                filteredMovies = []
                for movie in theMovies:
                    if searchForScreening.searchMovie.data.lower() in movie.Name.lower():
                        filteredMovies.append(movie)
                theMovies = filteredMovies
                numScreenings = len(theMovies)

        return render_template('index.html',
                            title='Homepage', user=current_user.Email,
                            allScreenings = allScreenings,
                            theMovies = theMovies,
                            numScreenings = numScreenings,
                            searchForScreening = searchForScreening
                            )
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if not current_user.is_authenticated:   #checks if user is already logged in
        signinForm = forms.Login()
        if signinForm.validate_on_submit():
            user = models.User.query.filter_by(Email=signinForm.email.data).first() #retrieves user profile
            if user and sha256_crypt.verify(signinForm.password.data, user.Password):   #checks user profile exists and that passwords match
                login_user(user)    #logs user in
                db.session.commit() #commits database changes
                logging.info('User: %s signed in', current_user.UserID)
                flash("Signed in successfully")
                return redirect(url_for('index'))
            else:   #if user details are not correct
                signinForm.email.errors.append('Email or password does not match')
                logging.warning('Anonymous User attempted to login with %s, inputted incorrect sign in details', signinForm.email.data)
        return render_template('login.html',
                    title='Login',
                    signinForm=signinForm
                    )
    else:
        logging.debug('User: %s attempted to access log in page', current_user.UserID)
        return redirect(url_for('index'))


@app.route('/signup', methods=['GET','POST'])
def signup():
    if not current_user.is_authenticated:   #checks if user is already logged in
        signupForm = forms.Signup()
        if signupForm.validate_on_submit():
            if models.User.query.filter_by(Email=signupForm.email.data).first():    #checks if email is already in use
                logging.debug('Anonymous User tried to register with email %s, email already in use', signupForm.email.data)
                signupForm.email.errors.append('This email is already in use')
            else:
                newUser = models.User(Email=signupForm.email.data, Password=sha256_crypt.encrypt(signupForm.password.data), Privilage=2)    #creates new user profile
                db.session.add(newUser) #adds user model to db
                user = models.User.query.filter_by(Email=signupForm.email.data).first() #retrieves user profile
                login_user(user) #logs new user in
                db.session.commit()
                logging.info('New User registered ID: %s', current_user.UserID)
                flash("Signed in successfully")
                return redirect(url_for('index'))
        return render_template('signup.html',
                           title='Signup',
                           signupForm=signupForm
                           )
    else:
        logging.debug('User: %s attempted to access log in page', current_user.UserID)
        return redirect('/login')

@app.route('/logout')
def logout():
    if current_user.is_authenticated:   #checks if user is signed in
        logging.info('User: %s signed out', current_user.UserID)
        logout_user()   #signs user out
        db.session.commit()
    return redirect(url_for('login'))

@app.route('/addMovieScreening', methods=['GET','POST'])
def addMovieScreening():
    if current_user.is_authenticated:   #checks user is signed in
        if (current_user.Privilage <= 1):   #checks user has required permission
            addScreeningForm = forms.addMovieScreening.new()
            if request.method == 'POST':
                if request.form.get("Add Screening"):
                    if addScreeningForm.start.data == None or addScreeningForm.end.data == None: #If not correctly formatted.
                        flash("Not completed, please ensure both the start and end time are in the correct format")
                    else:
                        findMovie = models.Movie.query.filter_by(Name=addScreeningForm.movie.data).first()
                        newScreening = models.Screening(MovieID=findMovie.MovieID, ScreenID = int(addScreeningForm.screen.data[7]),
                                                        StartTimestamp = addScreeningForm.start.data, EndTimestamp = addScreeningForm.end.data)
                        db.session.add(newScreening)
                        db.session.commit()
                        flash("Screening successfully added")
                        return redirect(url_for('index'))
            return render_template('add-movie-screening.html',
                                title='Add Movie Screening',
                                addScreeningForm = addScreeningForm,
                                )
        else:
            flash("You lack the required permission")
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route('/addNewMovie', methods=['GET','POST'])
def addNewMovie():
    if current_user.is_authenticated:   #checks user is signed in
        if (current_user.Privilage <= 1):   #checks user has required permission
            enterMovie = forms.enterMovie()
            fetchedMovie = {} #Blank dictionary
            fetchedMovieCheck = -1 #Flag variable to ensure an actual movie is fetched
            if request.method == 'POST':
                if request.form.get("Search"):
                    fetchedMovie = getMovieInfo(enterMovie.movietitle.data)
                    if fetchedMovie != None: #If a movie was found
                        fetchedMovieCheck = 1
                        session['fetchedMovie'] = fetchedMovie
                    else: #If no movie was found
                        fetchedMovieCheck = 0
                elif request.form.get("Confirm"):
                    currentMovies = models.Movie.query.filter_by(Description=session['fetchedMovie']['Description']).all() # Find current movies
                    if len(currentMovies) > 0: # If a movie with a matching description was found, don't add the movie
                        flash("Movie already added and available.")
                    else: # ELse, add as new movie
                        newMovie = models.Movie(Name = session['fetchedMovie']['Title'], Age = session['fetchedMovie']['Age_Rating'], Description = session['fetchedMovie']['Description'],
                                                RunningTime = session['fetchedMovie']['Duration'], PosterURL = session['fetchedMovie']['PosterURL'])
                        db.session.add(newMovie)
                        db.session.commit()
                    return redirect(url_for('addMovieScreening'))

            return render_template('add-new-movie.html',
                                title='Add New Movie',
                                enterMovie = enterMovie,
                                fetchedMovie = fetchedMovie,
                                fetchedMovieCheck = fetchedMovieCheck
                                )
        else:
            flash("You lack the required permission")
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))



@app.route('/bookTickets', methods=['GET','POST'])
def bookTickets():
    if current_user.is_authenticated:
        session['bookingProgress'] = 1 #Keeps track of where the user is in the booking process, 1 means that they have not selected a movie yet
        enterMovieForm = forms.enterMovie()
        if enterMovieForm.validate_on_submit():
            if models.Movie.query.filter_by(Name=enterMovieForm.movietitle.data).first(): # if the given movie title is valid (the movie is in the database)
                session['movie'] = enterMovieForm.movietitle.data
                session['bookingProgress'] = 2 #2 means that they have selected a movie, allows them to access bookTickets/2 without being redirected back to here
                return redirect(url_for('selectScreening'))
            else:
                enterMovieForm.movietitle.errors.append('Movie not found')

        return render_template('book-tickets.html',
                            title='Book Tickets',
                            enterMovieForm = enterMovieForm,
                            page=1
                            )
    else:
        flash("You must be signed in to book tickets")
        return redirect(url_for('login'))

@app.route('/bookTickets/2', methods=['GET','POST'])
def selectScreening():
    if current_user.is_authenticated:
        if session['bookingProgress'] >= 2:#if the user has selected a movie (i.e. has completed stage 1 of the booking process and have reached stage 2)
            selectScreeningForm = forms.selectScreening()
            if selectScreeningForm.validate_on_submit():
                session['screening'] = selectScreeningForm.screeningnumber.data #Record the given screening number in the session
                #Reset the seats and total ticket price session variables in case they were already set, since they may select a different screening with different seats and prices
                session['seats'] = []
                session['total'] = 0
                session['bookingProgress'] = 3 #Allows the user to access bookTickets/3 without being redirected back to the start of the process
                return redirect(url_for('addSeats'))

            return render_template('book-tickets.html',
                                title='Select Screening',
                                selectScreeningForm = selectScreeningForm,
                                page=2)
        else:
            flash('You must select a movie first')
            return redirect(url_for('bookTickets'))
    else:
        flash('You must be signed in to book tickets')
        return redirect(url_for('login'))

@app.route('/bookTickets/3', methods=['GET','POST'])
def addSeats():
    if current_user.is_authenticated:
        if session['bookingProgress'] >= 3:#if the user has selected a movie (i.e. has completed stage 1 of the booking process)
            addSeatsForm = forms.addSeats()
            if addSeatsForm.validate_on_submit():
                validSeatNumber = True
                for seat in session['seats']:
                    if seat[0] == addSeatsForm.seatnumber.data: #prevents the user booking the same seat multiple times
                        flash('That seat is not available')
                        validSeatNumber = False
                if validSeatNumber:
                    flash('Seat added')
                    price = 1 # Placeholder - change to calculate actual price
                    session['total'] += price
                    session['seats'].append([addSeatsForm.seatnumber.data, 'Standard', addSeatsForm.seatcategory.data, price])
                    session['bookingProgress'] = 4

            return render_template('book-tickets.html',
                                title='Add seats',
                                addSeatsForm = addSeatsForm,
                                seats=session['seats'],
                                total=session['total'],
                                page=3)
        else:
            flash('You must select a movie and screening first')
            return redirect(url_for('bookTickets'))
    else:
        flash('You must be signed in to book tickets')
        return redirect(url_for('login'))

@app.route('/bookTickets/4', methods=['GET','POST'])
def enterPaymentDetails():
    if current_user.is_authenticated:
        if session['bookingProgress'] >= 4:
            enterPaymentDetailsForm = forms.enterPaymentDetails()
            if enterPaymentDetailsForm.validate_on_submit():
                newBooking = models.Booking(UserID=current_user.UserID, ScreeningID=session['screening'], Timestamp=datetime.now(), TotalPrice=session['total'])
                db.session.add(newBooking)
                db.session.commit()
                for seat in session['seats']:
                    if seat[2] == 'Adult':
                        Category = 1
                    elif seat[2] == 'Child':
                        Category = 0
                    elif seat[2] == 'Senior':
                        Category = 2
                    newTicket = models.Ticket(BookingID=newBooking.BookingID, SeatID=seat[0], Category=Category, QR='qr') #seat[0] and 'qr' are placeholders
                    db.session.add(newTicket)
                db.session.commit()
                return redirect(url_for('index'))

            return render_template('book-tickets.html',
                                title='Checkout',
                                enterPaymentDetailsForm = enterPaymentDetailsForm,
                                page=4)
        else:
            flash('You must complete the booking process first')
            return redirect(url_for('addSeats'))
    else:
        flash('You must be signed in to book tickets')
        return redirect(url_for('login'))

@app.route('/test', methods=['GET','POST'])
def t():
    enterMovieForm = forms.enterMovie()
    if enterMovieForm.validate_on_submit():
                session['movie'] = enterMovieForm.movietitle.data
                return redirect(url_for('index'))

    return render_template('book-tickets.html',
                            title='Book Tickets',
                            enterMovieForm = enterMovieForm,
                            page=1
                            )

@app.route('/seats')
def seats():

    return render_template('seating-auto-layout.html',
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'], 
    vip=['D', 'E', 'F'], 
    reserved = ['A1', 'C14', 'E10', 'E11']) # need to collect actual reserved seats