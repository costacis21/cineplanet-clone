from flask import flash, render_template, redirect, url_for, session, request, send_from_directory
from flask_login import current_user, login_user, logout_user
from app import app,models,forms,db,admin,CreatePDF,SendEmail
import datetime
from passlib.hash import sha256_crypt
import logging
import pyqrcode
from PIL import Image
import uuid
import os
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

# FLASK ADMIN setup
# remove before deployment
from flask_admin.contrib.sqla import ModelView
admin.add_view(ModelView(models.User, db.session))
admin.add_view(ModelView(models.Screening, db.session))
admin.add_view(ModelView(models.Booking, db.session))
admin.add_view(ModelView(models.Ticket, db.session))
admin.add_view(ModelView(models.Seat, db.session))
admin.add_view(ModelView(models.Movie, db.session))

from imdbSearch import *
from income import *

premium = ['D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12', 'D13', 'D14', 'D15', 'D16',
'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12', 'E13', 'E14', 'E15', 'E16',
'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'F13', 'F14', 'F15', 'F16']

StandardGeneralPrice = 4.99 #Standard geenral ticket price
StandardConcessionPrice = 3.49  #Standard senior price
PremiumGeneralPrice = 6.99  #Premium general ticket price
PremiumConcessionPrice = 5.49   #Premium price

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
    session['testing'] = False
    allMovies = models.Movie.query.all()
    quickBookForm = forms.addMovieScreening.new()
    movie = None
    if request.method == 'POST':
        if request.form.get("Search"):
            date = request.form['screeningDateFilter']
            if date == '':
                return redirect('/screenings')
            else:
                return redirect('/screenings/' + str(date))
    return render_template('index.html',
                            title='Home',
                            allMovies = allMovies,
                            movie = movie,
                            hide=True)

@app.route('/screenings', methods=['GET','POST'])
def screeningsRedirect():
    resetBookingSessionData()
    session['booking_complete'] = False
    date = datetime.date.today()
    return redirect('/screenings/' + str(date))

@app.route('/screenings/<date>', methods=['GET','POST'])
def datedScreenings(date):
    resetBookingSessionData()
    if date < str(datetime.date.today()):
        return redirect("/screenings")
    #Fetch all the movies
    everyMovie = models.Movie.query.all()
    # Variables for the pop up to work
    allMovies = models.Movie.query.all()
    foundMovieInfo = 0
    # --------------------------------
    dailyScreenings = 0
    moviesWithScreenings = []
    for i in allMovies: #Go through all the movies
        if i.getScreenings(date): #Get all the screenings for each movie on that day
            dailyScreenings = dailyScreenings + 1
            moviesWithScreenings.append(i) #add to an array for movies with screenings
    searchForScreening = forms.searchForScreening()
    if request.method == 'POST':
        if request.form.get("Search"):
                filteredMovies = []
                for movie in moviesWithScreenings:
                    if searchForScreening.searchMovie.data.lower() in movie.Name.lower():
                        filteredMovies.append(movie)
                moviesWithScreenings = filteredMovies
                numScreenings = len(moviesWithScreenings)
        elif request.form.get("Filter"):
            date = request.form['screeningDateFilter']
            if date == "": #if no data is entered for the date
                return redirect(request.url)
            else:
                return redirect('/screenings/' + str(date))
        elif request.form.get("viewInfo"):
            foundMovieInfo = request.form.get("viewInfo")
        else: # Clicked to buy tickets
            foundScreeningID = request.form.get("buy")
            # Needs here to be replaced with a redirect to the specific ticket booking of that screening
            return redirect('/seats/' + str(foundScreeningID))
    # Code to get all youtube id's
    movieTrailerIDs = []
    for movie in moviesWithScreenings:
        url_data = urlparse.urlparse(movie.TrailerURL)
        query = urlparse.parse_qs(url_data.query)
        video = query["v"][0]
        movieTrailerIDs.append(video)
    if current_user.is_authenticated:
        return render_template('screenings.html',
                            title='Screenings',
                            allMovies = moviesWithScreenings,
                            moviesLength = len(moviesWithScreenings),
                            date = date,
                            dailyScreenings = dailyScreenings,
                            user=current_user.Email,
                            searchForScreening = searchForScreening,
                            everyMovie = everyMovie,
                            foundMovieInfo = int(foundMovieInfo),
                            movieTrailerIDs = movieTrailerIDs
                            )
    else:
        return render_template('screenings.html',
                            title='Screenings',
                            allMovies = moviesWithScreenings,
                            moviesLength = len(moviesWithScreenings),
                            date = date,
                            dailyScreenings = dailyScreenings,
                            searchForScreening = searchForScreening,
                            everyMovie = everyMovie,
                            foundMovieInfo = int(foundMovieInfo),
                            movieTrailerIDs = movieTrailerIDs
                        )

@app.route('/movie/<MovieID>', methods=['GET','POST'])
def movieInformation(MovieID):
    resetBookingSessionData()
    lastMovie = models.Movie.query.order_by(models.Movie.MovieID.desc()).first()
    if int(lastMovie.MovieID) < int(MovieID): #If try and get to URL where no movie exists for it
        return redirect('/') # Redirect back to home
    movie = models.Movie.query.filter_by(MovieID=MovieID).first()
    screenings = models.Screening.query.filter_by(MovieID = MovieID).order_by(models.Screening.StartTimestamp).all()
    # Code below removes any screenings that have already happended so you can't direct to buy tickets
    futureScreenings = []
    for screening in screenings:
        if screening.StartTimestamp > datetime.datetime.now() - timedelta(days=1):
            futureScreenings.append(screening)
    screenings = futureScreenings
    numScreenings = len(screenings)
    # Get Youtube Video ID
    url_data = urlparse.urlparse(movie.TrailerURL)
    query = urlparse.parse_qs(url_data.query)
    video = query["v"][0]
    if request.method == 'POST':
        foundScreeningID = request.form.get("buy")
        # Needs here to be replaced with a redirect to the specific ticket booking of that screening
        return redirect('/seats/' + str(foundScreeningID))
    return render_template('movie-information.html',
                    title="Movie Information - " + movie.Name,
                    movie = movie,
                    screenings = screenings,
                    numScreenings = numScreenings,
                    video = video
                    )

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
                        for i in range(0,5):
                            newScreening = models.Screening(MovieID=(findMovie.MovieID+i), ScreenID = int(addScreeningForm.screen.data[7]),
                                                            StartTimestamp = addScreeningForm.start.data, EndTimestamp = addScreeningForm.end.data)
                            db.session.add(newScreening)
                            db.session.commit()
                        flash("Screening successfully added")
                        return redirect(url_for('index'))
            return render_template('add-movie-screening.html',
                                title='Add Movie Screening',
                                addScreeningForm = addScreeningForm,
                                user=current_user.Email
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
            fetchedMovies = getUpcomingMovies()
            selectMovie = forms.selectNewMovie()
            if request.method == 'POST':
                if enterMovie.validate_on_submit(): #if search is used and is not empty, search for movies by title
                    if(enterMovie.movietitle.data != ""):
                        fetchedMovies = getMovieInfo(enterMovie.movietitle.data)
                elif selectMovie.is_submitted(): #if movie is selected, get its data and try to add it to db
                    selectedMovie = getMovieInfoFromID(selectMovie.tmdbID.data)
                    selectedMovieDescription = selectedMovie['Description']
                    currentMovies = models.Movie.query.filter_by(Description=selectedMovie['Description']).all() # Find current movies
                    if len(currentMovies) > 0: # If a movie with a matching description was found, don't add the movie
                        flash("Movie already added and available.")
                    else: # ELse, add as new movie
                        newMovie = models.Movie(Name = selectedMovie['Title'], Age = selectedMovie['Age_Rating'], Description = selectedMovie['Description'],
                                                RunningTime = selectedMovie['Duration'], PosterURL = selectedMovie['PosterURL'],Api = selectedMovie['ID'],TrailerURL=selectedMovie['TrailerURL'])
                        db.session.add(newMovie)
                        db.session.commit()
                        return redirect(url_for('addMovieScreening'))



            return render_template('add-new-movie.html',
                                title='Add New Movie',
                                enterMovie = enterMovie,
                                user=current_user.Email,
                                movies = fetchedMovies,
                                selectMovie = selectMovie
                                )
        else:
            flash("You lack the required permission")
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

# Used in testing to log the user in to a customer account
@app.route('/test-login', methods=['GET', 'POST'])
def t2():
    if app.config['TESTING'] == True:
        user = models.User.query.filter_by(Email='test@gmail.com').first() #retrieves user profile
        login_user(user)    #logs user in
        db.session.commit() #commits database changes

        return redirect(url_for('profile'))

    else:
        return redirect(url_for('index'))

# Used in testing to log the user in to an admin account
@app.route('/test-admin-login', methods=['GET', 'POST'])
def t3():
    if app.config['TESTING'] == True:
        user = models.User.query.filter_by(Email='admin@admin.com').first() #retrieves user profile
        login_user(user)    #logs user in
        db.session.commit() #commits database changes

        return redirect(url_for('profile'))

    else:
        return redirect(url_for('index'))

@app.route('/seats/<screening>')
def seats(screening):   #seat selection page
    if current_user.is_authenticated:
        screening = models.Screening.query.get(screening) #get screening

        return render_template('seating-auto-layout.html',
        rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
        vip=['D', 'E', 'F'],
        reserved = screening.reserved(),
        screening=screening,
        title = 'Reserve Seats')
    else:
        flash('You must be signed in to book tickets')
        return redirect(url_for('login'))

@app.route('/confirmBooking/<screening>/<seats>')
def confirmBooking(screening, seats):   # succeed seat selection page
    if current_user.is_authenticated:
        retrieved = seats.split("$") # retrieved seats
        selected = [] # choosen and validated seats
        child = False
        age = models.Movie.query.get(models.Screening.query.get(screening).MovieID).Age
        if age != 'R' and age != 'X':   #decide whether child seats are available
            child = True
        for seat in retrieved:  #validate each retireved seat exists and no repeats
            if seat in models.Screening.query.get(screening).seats() and seat not in selected:
                selected.append(seat)

        return  render_template('confirm-booking.html',
        seats=selected,
        premium=premium,
        StandardGeneralPrice=StandardGeneralPrice,
        StandardConcessionPrice=StandardConcessionPrice,
        PremiumGeneralPrice=PremiumGeneralPrice,
        PremiumConcessionPrice=PremiumConcessionPrice,
        child = child,
        title = 'Confirm booking')

    else:
        flash('You must be signed in to book tickets')
        return redirect(url_for('login'))


@app.route('/payment/<screeningID>/<seats>/<types>', methods=['GET','POST'])
def Payment(screeningID, seats, types): # succeed booking confirmation page
    if current_user.is_authenticated:
        retrieved = seats.split("$") #choosen seats
        concessions = types.split("$") #choosen ticket types
        selected =[] #choosen and validated seats
        screening = models.Screening.query.get(screeningID) #get screening

        if not screening:   #validate screening does exist
            flash("Something went wrong, please try again")
            return redirect(url_for('index'))

        if len(retrieved) != len(concessions):  #validate equal number of seats to tickets
            return redirect("/confirmBooking/"+screeningID+"/"+seats)

        age = models.Movie.query.get(screening.MovieID).Age #gets movie age rating
        if '2' in concessions:  #have child tickets been selected
            if age in ['R', 'X']:   #checks that child tickets are available for the screening
                flash("Something went wrong, please try again")
                return redirect(url_for('index'))

        for seat in retrieved:  #validate seats exist, are not booked and are not repeated
            if seat in screening.seats() and seat not in selected:
                selected.append(seat)
            if seat in screening.reserved():
                return redirect(url_for('seats')+screeningID)

        order = list(zip(selected, concessions))    #create order merging seats with tickets

        total = 0.0
        displayOrder = []
        PaymentDetailsForm = forms.PaymentDetailsForm()
        UseCard = forms.UseCard()
        for item in order:  #calculate total cost
            seatType = models.Seat.query.filter(models.Seat.ScreenID==screening.ScreenID).filter(models.Seat.code==item[0]).first().Type
            if seatType == 0:   #standard seat costing
                if int(item[1]) == 3:   #senior ticket
                    total = total + StandardConcessionPrice
                    displayOrder.append(['Standard Senior Ticket', StandardConcessionPrice])
                elif int(item[1]) == 2:    #child
                    total = total + StandardGeneralPrice
                    displayOrder.append(['Standard Child Ticket', StandardGeneralPrice])
                elif int(item[1]) == 1:     #adult
                    total = total + StandardGeneralPrice
                    displayOrder.append(['Standard Adult Ticket', StandardGeneralPrice])
                else:
                    flash("Something went wrong, please try again")
                    return redirect(url_for('index'))

            elif seatType == 1: #Premium seat costing
                if int(item[1]) == 3:   #senior ticket
                    total = total + PremiumConcessionPrice
                    displayOrder.append(['Premium Senior Ticket', PremiumConcessionPrice])
                elif int(item[1]) == 2:    #child
                    total = total + PremiumGeneralPrice
                    displayOrder.append(['Premium Child Ticket', PremiumGeneralPrice])
                elif int(item[1]) == 1:     #adult
                    total = total + PremiumGeneralPrice
                    displayOrder.append(['Premium Adult Ticket', PremiumGeneralPrice])
                else:
                    flash("Something went wrong, please try again")
                    return redirect(url_for('index'))
            else:
                flash("Something went wrong, please try again")
                return redirect(url_for('index'))
        total = round(total, 2)
        if "details" in request.form and PaymentDetailsForm.validate_on_submit():
            try:
                datetime.datetime.strptime(PaymentDetailsForm.Expiry.data, '%m-%y') #check card can be converted to date
            except:
                PaymentDetailsForm.Expiry.errors.append('Please input dates in the example format: 05-22')

            if datetime.datetime.strptime(PaymentDetailsForm.Expiry.data, '%m-%y') < datetime.datetime.now(): #check card has not expired
                PaymentDetailsForm.Expiry.errors.append('This card is out of date')

            else:
                if PaymentDetailsForm.Save.data:    #add card to db if user chooses
                    card = models.Card(UserID=current_user.UserID, CardNo=PaymentDetailsForm.CardNo.data ,Name=PaymentDetailsForm.Name.data, Expiry=datetime.datetime.strptime(PaymentDetailsForm.Expiry.data, '%m-%y'), CVV=PaymentDetailsForm.CVV.data)
                    db.session.add(card)
                    db.session.commit()

                newBooking = models.Booking(UserID=current_user.UserID, ScreeningID=screeningID, Timestamp=datetime.datetime.now(), TotalPrice=total)
                db.session.add(newBooking)  #create and add new booking
                db.session.commit()

                for item in order:  #create and add new tickets to booking
                    seatID = models.Seat.query.filter(models.Seat.ScreenID==screening.ScreenID).filter(models.Seat.code==item[0]).first().SeatID
                    newTicket = models.Ticket(BookingID=newBooking.BookingID, SeatID=seatID, Category=item[1], QR=str(uuid.uuid4()))
                    db.session.add(newTicket)
                db.session.commit()

                screening = models.Screening.query.filter_by(ScreeningID=newBooking.ScreeningID).first()
                screen = screening.ScreenID
                i=0
                filenames=[]
                QRs = []
                Seats = []
                Categories = []
                Types = []
                for ticket in models.Ticket.query.filter_by(BookingID=newBooking.BookingID): # For all of the tickets just purchased
                    # Make QR code for ticket
                    qr_filename = os.getcwd() + '/app/static/ticket/qr/qr'+str(ticket.TicketID)+'.png'
                    qr = pyqrcode.create(request.url_root+ticket.QR) # Needs to be changed to not have the port hardcoded into it
                    #qr = pyqrcode.create(ticket.QR)
                    qr.png(qr_filename, scale=6)

                    if ticket.Category == 1:
                        Category = "Adult"
                    elif ticket.Category == 2:
                        Category = "Child"
                    elif ticket.Category == 3:
                        Category = "Senior"
                    else:
                        Category = "Unknown"

                    # Converting the numerical value for the seat's type that is stored in the database to the string value that will appear on the ticket
                    #t = models.Seat.query.filter(models.Seat.ScreenID==screening.ScreenID).filter(models.Seat.code==item[0]).first().Type
                    t = models.Seat.query.filter_by(SeatID=ticket.SeatID).first().Type
                    if t == 0:
                        Type = "Standard"
                    else:
                        Type = "Premium"

                    # Appending the values of the properties of the ticket to the relevant arrays
                    QRs.append(qr_filename)
                    Seats.append(order[i][0])
                    Categories.append(Category)
                    Types.append(Type)
                    i += 1

                #Make a PDF for the ticket
                movie = models.Movie.query.filter_by(MovieID=screening.MovieID).first().Name
                filename = os.getcwd() + '/app/static/ticket/tickets/booking'+str(newBooking.BookingID)+'.pdf'
                CreatePDF.MakePDF(filename, QRs, movie, Seats, Categories, str(screen), str(screening.StartTimestamp.date().strftime('%d/%m/%y')), str(screening.StartTimestamp.time().strftime('%H:%M')), Types)
                filenames.append(filename)

                # Send all the PDFs in an email to the user
                # First argument gives the destination email, currently set to email ourselves to prevent one of us receiving lots of emails during testing
                #SendEmail.SendMail("leeds.cineplanet.com", filenames)
                # Un-comment the line below to send emails to their actual destination
                SendEmail.SendMail(current_user.Email, filenames)

                if current_user.Privilage < 2:
                    session['booking_complete'] = True
                    flash("Displaying your tickets now")
                    return redirect('/view-tickets/'+str(newBooking.BookingID))
                else:
                    flash("Your tickets have been sent to "+current_user.Email)
                    return redirect(url_for('index'))

        if "savedCard" in request.form and UseCard.validate_on_submit():

            newBooking = models.Booking(UserID=current_user.UserID, ScreeningID=screeningID, Timestamp=datetime.datetime.now(), TotalPrice=total)
            db.session.add(newBooking)  #create and add new booking
            db.session.commit()

            for item in order:  #create and add new tickets to booking
                seatID = models.Seat.query.filter(models.Seat.ScreenID==screening.ScreenID).filter(models.Seat.code==item[0]).first().SeatID
                newTicket = models.Ticket(BookingID=newBooking.BookingID, SeatID=seatID, Category=item[1], QR=str(uuid.uuid4()))
                db.session.add(newTicket)
            db.session.commit()

            screening = models.Screening.query.filter_by(ScreeningID=newBooking.ScreeningID).first()
            screen = screening.ScreenID
            i=0
            filenames=[]
            QRs = []
            Seats = []
            Categories = []
            Types = []
            for ticket in models.Ticket.query.filter_by(BookingID=newBooking.BookingID): # For all of the tickets just purchased
                # Make QR code for ticket
                qr_filename = os.getcwd() + '/app/static/ticket/qr/qr'+str(ticket.TicketID)+'.png'
                qr = pyqrcode.create(request.url_root+ticket.QR) # Needs to be changed to not have the port hardcoded into it
                #qr = pyqrcode.create(ticket.QR)
                qr.png(qr_filename, scale=6)

                if ticket.Category == 1:
                    Category = "Adult"
                elif ticket.Category == 2:
                    Category = "Child"
                elif ticket.Category == 3:
                    Category = "Senior"
                else:
                    Category = "Unknown"

                # Converting the numerical value for the seat's type that is stored in the database to the string value that will appear on the ticket
                #t = models.Seat.query.filter(models.Seat.ScreenID==screening.ScreenID).filter(models.Seat.code==item[0]).first().Type
                t = models.Seat.query.filter_by(SeatID=ticket.SeatID).first().Type
                if t == 0:
                    Type = "Standard"
                else:
                    Type = "Premium"

                # Appending the values of the properties of the ticket to the relevant arrays
                QRs.append(qr_filename)
                Seats.append(order[i][0])
                Categories.append(Category)
                Types.append(Type)
                i += 1

            #Make a PDF for the ticket
            movie = models.Movie.query.filter_by(MovieID=screening.MovieID).first().Name
            filename = os.getcwd() + '/app/static/ticket/tickets/booking'+str(newBooking.BookingID)+'.pdf'
            CreatePDF.MakePDF(filename, QRs, movie, Seats, Categories, str(screen), str(screening.StartTimestamp.date().strftime('%d/%m/%y')), str(screening.StartTimestamp.time().strftime('%H:%M')), Types)
            filenames.append(filename)

            # Send all the PDFs in an email to the user
            # First argument gives the destination email, currently set to email ourselves to prevent one of us receiving lots of emails during testing
            #SendEmail.SendMail("leeds.cineplanet.com", filenames)
            # Un-comment the line below to send emails to their actual destination
            SendEmail.SendMail(current_user.Email, [filename])

            if current_user.Privilage < 2:
                session['booking_complete'] = True
                flash("Displaying your tickets now")
                return redirect('/view-tickets/'+str(newBooking.BookingID))
            else:
                flash("Your tickets have been sent to "+current_user.Email)
                return redirect(url_for('index'))

        return render_template('payment.html', title='Checkout',
                            total = total,
                            displayOrder = displayOrder,
                            PaymentDetailsForm = PaymentDetailsForm,
                            UseCard = UseCard,
                            cards = current_user.Cards.all()
                            )
    else:
        flash('You must be signed in to book tickets')
        return redirect(url_for('login'))


@app.route('/cashPayment/<screeningID>/<seats>/<types>', methods=['GET','POST'])
def CashPayment(screeningID, seats, types): # succeed booking confirmation page
    if current_user.is_authenticated and  current_user.Privilage < 2:
        retrieved = seats.split("$") #choosen seats
        concessions = types.split("$") #choosen ticket types
        selected =[] #choosen and validated seats
        screening = models.Screening.query.get(screeningID) #get screening

        if not screening:   #validate screening does exist
            flash("Something went wrong, please try again")
            return redirect(url_for('index'))

        if len(retrieved) != len(concessions):  #validate equal number of seats to tickets
            return redirect("/confirmBooking/"+screeningID+"/"+seats)

        age = models.Movie.query.get(screening.MovieID).Age #gets movie age rating
        if '2' in concessions:  #have child tickets been selected
            if age in ['R', 'X']:   #checks that child tickets are available for the screening
                flash("Something went wrong, please try again")
                return redirect(url_for('index'))

        for seat in retrieved:  #validate seats exist, are not booked and are not repeated
            if seat in screening.seats() and seat not in selected:
                selected.append(seat)
            if seat in screening.reserved():
                return redirect(url_for('seats')+screeningID)

        order = list(zip(selected, concessions))    #create order merging seats with tickets

        total = 0.0
        displayOrder = []
        Paid = forms.Paid()
        for item in order:  #calculate total cost
            seatType = models.Seat.query.filter(models.Seat.ScreenID==screening.ScreenID).filter(models.Seat.code==item[0]).first().Type
            if seatType == 0:   #standard seat costing
                if int(item[1]) == 3:   #senior ticket
                    total = total + StandardConcessionPrice
                    displayOrder.append(['Standard Senior Ticket', StandardConcessionPrice])
                elif int(item[1]) == 2:    #child
                    total = total + StandardGeneralPrice
                    displayOrder.append(['Standard Child Ticket', StandardGeneralPrice])
                elif int(item[1]) == 1:     #adult
                    total = total + StandardGeneralPrice
                    displayOrder.append(['Standard Adult Ticket', StandardGeneralPrice])
                else:
                    flash("Something went wrong, please try again")
                    return redirect(url_for('index'))

            elif seatType == 1: #Premium seat costing
                if int(item[1]) == 3:   #senior ticket
                    total = total + PremiumConcessionPrice
                    displayOrder.append(['Premium Senior Ticket', PremiumConcessionPrice])
                elif int(item[1]) == 2:    #child
                    total = total + PremiumGeneralPrice
                    displayOrder.append(['Premium Child Ticket', PremiumGeneralPrice])
                elif int(item[1]) == 1:     #adult
                    total = total + PremiumGeneralPrice
                    displayOrder.append(['Premium Adult Ticket', PremiumGeneralPrice])
                else:
                    flash("Something went wrong, please try again")
                    return redirect(url_for('index'))
            else:
                flash("Something went wrong, please try again")
                return redirect(url_for('index'))
        total = round(total, 2)
        if Paid.validate_on_submit():

            newBooking = models.Booking(UserID=current_user.UserID, ScreeningID=screeningID, Timestamp=datetime.datetime.now(), TotalPrice=total)
            db.session.add(newBooking)  #create and add new booking
            db.session.commit()

            for item in order:  #create and add new tickets to booking
                seatID = models.Seat.query.filter(models.Seat.ScreenID==screening.ScreenID).filter(models.Seat.code==item[0]).first().SeatID
                newTicket = models.Ticket(BookingID=newBooking.BookingID, SeatID=seatID, Category=item[1], QR=str(uuid.uuid4()))
                db.session.add(newTicket)
            db.session.commit()

            screening = models.Screening.query.filter_by(ScreeningID=newBooking.ScreeningID).first()
            screen = screening.ScreeningID
            i=0
            filenames=[]
            QRs = []
            Seats = []
            Categories = []
            Types = []
            for ticket in models.Ticket.query.filter_by(BookingID=newBooking.BookingID): # For all of the tickets just purchased
                # Make QR code for ticket
                qr_filename = os.getcwd() + '/app/static/ticket/qr/qr'+str(ticket.TicketID)+'.png'
                qr = pyqrcode.create(request.url_root+ticket.QR) # Needs to be changed to not have the port hardcoded into it
                #qr = pyqrcode.create(url_for('index')+ticket.QR)
                qr.png(qr_filename, scale=6)

                # Converting the numerical value for the ticket's category that is stored in the database to the string value that will appear on the ticket
                if ticket.Category == 1:
                    Category = "Adult"
                elif ticket.Category == 2:
                    Category = "Child"
                elif ticket.Category == 3:
                    Category = "Senior"
                else:
                    Category = "Unknown"

                # Converting the numerical value for the seat's type that is stored in the database to the string value that will appear on the ticket
                #t = models.Seat.query.filter(models.Seat.ScreenID==screening.ScreenID).filter(models.Seat.code==item[0]).first().Type
                t = models.Seat.query.filter_by(SeatID=ticket.SeatID).first().Type
                if t == 0:
                    Type = "Standard"
                else:
                    Type = "Premium"

                # Appending the values of the properties of the ticket to the relevant arrays
                QRs.append(qr_filename)
                Seats.append(order[i][0])
                Categories.append(Category)
                Types.append(Type)
                i += 1

            #Make a PDF for the ticket
            movie = models.Movie.query.filter_by(MovieID=screening.MovieID).first().Name
            filename = os.getcwd() + '/app/static/ticket/tickets/booking'+str(newBooking.BookingID)+'.pdf'
            CreatePDF.MakePDF(filename, QRs, movie, Seats, Categories, str(screen), str(screening.StartTimestamp.date().strftime('%d/%m/%y')), str(screening.StartTimestamp.time().strftime('%H:%M')), Types)
            filenames.append(filename)

            # Send all the PDFs in an email to the user
            # First argument gives the destination email, currently set to email ourselves to prevent one of us receiving lots of emails during testing
            #SendEmail.SendMail("leeds.cineplanet.com", [filename])
            # Un-comment the line below to send emails to their actual destination
            SendEmail.SendMail(current_user.Email, [filename])

            session['booking_complete'] = True
            flash("Displaying your tickets now")
            return redirect('/view-tickets/'+str(newBooking.BookingID))

        return render_template('cash-payment.html', title='Checkout',
                            total = total,
                            displayOrder = displayOrder,
                            Paid = Paid,
                            cards = current_user.Cards.all()
                            )
    else:
        flash('You must be signed in to book tickets')
        return redirect(url_for('login'))

@app.route('/view-bookings')
def viewBookings():
    if current_user.is_authenticated:
        UserID=current_user.UserID
        booking_records = models.Booking.query.filter_by(UserID=UserID).all() # Returns all bookings made by the current user

        bookings = []
        for booking in booking_records:
            screening = models.Screening.query.filter_by(ScreeningID=booking.ScreeningID).first()
            time = screening.StartTimestamp.time().strftime('%H:%M')
            date = screening.StartTimestamp.date().strftime('%d/%m/%y')
            movie = models.Movie.query.filter_by(MovieID=screening.MovieID).first()
            bookings.append([booking, movie.Name, time, date, movie.PosterURL])

        return render_template('view-bookings.html', bookings=bookings, title="View Bookings")

    else:
        flash("You must be logged in to view bookings")
        return redirect(url_for('login'))

@app.route('/validate-ticket/<uuid>', methods = ['GET', 'POST'])
def validateTicket(uuid):
    if current_user.is_authenticated:
        valid = False
        if current_user.Privilage <= 1: # Checks that the user has the required permissions to validate tickets (customers can't validate tickets)
            if models.Ticket.query.filter_by(QR=uuid).first(): # If the uuid is valid
                valid = True
        else:
            flash("You do not have the required permissions to validate tickets")
            return redirect(url_for('index'))

        return render_template('validate-ticket.html', valid=valid, title="Validate Ticket")

    else:
        flash('You must be signed in to validate tickets')
        return redirect(url_for('login'))

@app.route('/view-tickets/<BookingID>', methods = ['GET', 'POST'])
def viewTickets(BookingID):
    if current_user.is_authenticated:
        # Check that the booking exists
        if models.Booking.query.filter_by(BookingID=BookingID).first():
            # Gets all bookings made by a user
            bookings = models.Booking.query.filter_by(UserID=current_user.UserID).all()
            # Checks that the user has made bookings
            if len(bookings) > 0:
                # Checks that this booking is one made by the current user
                valid = False
                for booking in bookings:
                    if booking.BookingID == int(BookingID):
                        valid = True

                # If the booking was made by the current user
                if valid == True:
                    return render_template('view-tickets.html', BookingID=BookingID, title="View Tickets")
                else:
                    flash("You cannot view another user's bookings")
            else:
                flash("You do not have any tickets linked to your account")
        else:
            flash("Tickets not found")

        return redirect(url_for('index'))

    else:
        flash('You must be signed in to view tickets')
        return redirect(url_for('login'))

@app.route('/profile', methods=['GET','POST'])
def profile():
    if current_user.is_authenticated:
        form = forms.changePasswordForm()
        UseCard = forms.UseCard()
        if form.validate_on_submit():
            if sha256_crypt.verify(form.currentPassword.data, current_user.Password):
                current_user.Password = sha256_crypt.encrypt(form.newPassword.data)
                db.session.commit()
                flash("Password updated")
                logging.info('User: %s updated password', current_user.Email)
            else:
                logging.error('User: %s inputted incorect password on settings page', current_user.Email)
                form.currentPassword.errors.append('Password does not match')
        logging.info('User: %s visited settings page', current_user.Email)
        return render_template('profile.html',
                            title = 'My Profile',
                            cards = current_user.Cards.all(),
                            UseCard = UseCard,
                            form=form)
    else:
        flash('You must be signed in to view profiles')
        return redirect(url_for('login'))


@app.route('/view-incomes', methods=['GET','POST'])
def viewIncomes():
     if current_user.is_authenticated:   #checks user is signed in
        if (current_user.Privilage < 2):
            incomes=getWeeklyIncomes()
            return render_template('view-incomes.html',
                                    incomes = incomes[0],
                                    totalIncome = incomes[1],
                                    week = incomes[2],
                                    title = "Incomes per Movie"
                                    )

     return redirect(url_for('index'))


@app.route('/show-graphs', methods = ['GET','POST'])
def showGraphs():
     if current_user.is_authenticated:   #checks user is signed in
        if (current_user.Privilage < 2):

            createWeeklyGraph()
            return render_template('show-graphs.html', title = "Weekly Income Graph")

     return redirect(url_for('index'))

@app.route('/compare-ticket-sales', methods = ['GET','POST'])
def compareTicketSales():
     week = ""
     tickets=[]
     filename=""
     if current_user.is_authenticated:   #checks user is signed in
        form = forms.CompareTicketSalesForm()

        if (current_user.Privilage < 2):
            if request.method == 'POST':
                if form.validate_on_submit():
                    start = form.start.data
                    end = form.end.data
                    tickets = compareMovies(start.date(), end.date())
                    week= str(start.date()) +' - ' + str(end.date())
                    filename=str(start.date()) +'-' + str(end.date())+'.png'
                    print(tickets)
            return render_template('compare-ticket-sales.html', title = "Compare Ticket Sales", form = form, tickets = tickets, week =week,filename=filename )

     return redirect(url_for('index'))




@app.route('/remove-card/<CardID>', methods = ['GET', 'POST'])
def removeCard(CardID):
    if current_user.is_authenticated:
        # Gets all bookings made by a user

        if (models.Card.query.get(CardID).UserID == current_user.UserID): #if the card is the current users
            card = models.Card.query.get(CardID) #get card
            db.session.delete(card) #remove card
            db.session.commit() #commits database changes

        return redirect(url_for('profile'))

    else:
        flash('You must be signed in to book tickets')
        return redirect(url_for('login'))

@app.route('/manage-staff', methods=['GET','POST'])
def manageStaff():
    if current_user.is_authenticated:
        if current_user.Privilage == 0:
            staff = models.User.query.filter(models.User.Privilage <= 1).order_by(models.User.Privilage.asc()).all() #get all staff members
            PrivilageForm = forms.SetUserPrivilage()
            if PrivilageForm.validate_on_submit():
                user = models.User.query.filter_by(Email=PrivilageForm.Username.data).first() #get selected user
                if user:    #if user exists, update to selected privilage
                    if PrivilageForm.Privilage.data == "Admin":
                        user.Privilage = 0
                    elif PrivilageForm.Privilage.data == "Staff":
                        user.Privilage = 1
                    elif PrivilageForm.Privilage.data == "Basic":
                        user.Privilage = 2
                    else:
                        return redirect(PrivilageForm.Privilage.data)
                    db.session.commit()
                    return redirect('/manage-staff')
                else:
                    PrivilageForm.Username.errors.append('No users with matching Username')

            return render_template('staff-roster.html',
            staff = staff,
            PrivilageForm=PrivilageForm)
        else:
            flash('Your account does not have access to this functionality')
            return redirect(url_for('index'))
    else:
        flash('You must be signed in to access to this functionality')
        return redirect(url_for('login'))
