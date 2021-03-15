from flask import flash, render_template, redirect, url_for, session, request
from flask_login import current_user, login_user, logout_user
from app import app,models,forms,db,admin
import datetime
from passlib.hash import sha256_crypt
import logging
from app import CreatePDF
from app import SendEmail
import pyqrcode
from PIL import Image

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
    allMovies = models.Movie.query.all()
    quickBookForm = forms.addMovieScreening.new()
    movie = None
    if request.method == 'POST':
        if request.form.get("Search"):
            movie = quickBookForm.movie.data
            date = request.form['screeningDateFilter']
            if date == "": #if no data is entered for the date
                flash('Please enter a date')
            else:
                flash("Searching for " + movie + " on " + date)
        if request.form.get("showModal"):
            print("hello")
    return render_template('index.html',
                            title='Home',
                            allMovies = allMovies,
                            quickBookForm = quickBookForm,
                            movie = movie)

@app.route('/screenings', methods=['GET','POST'])
def screeningsRedirect():
    date = datetime.date.today()
    return redirect('/screenings/' + str(date))

@app.route('/screenings/<date>', methods=['GET','POST'])
def datedScreenings(date):
    resetBookingSessionData()
    if date < str(datetime.date.today()):
        return redirect("/")
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
                return redirect('/')
            else:
                return redirect('/screenings/' + str(date))
        elif request.form.get("viewInfo"):
            foundMovieInfo = request.form.get("viewInfo")
        else: # Clicked to buy tickets
            foundScreeningID = request.form.get("buy")
            # Needs here to be replaced with a redirect to the specific ticket booking of that screening
            return redirect('/seats/' + str(foundScreeningID))
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
                            foundMovieInfo = int(foundMovieInfo)
                            )
    else:
        return render_template('index.html',
                        title='Homepage',
                        allMovies = moviesWithScreenings,
                        moviesLength = len(moviesWithScreenings),
                        date = date,
                        dailyScreenings = dailyScreenings,
                        searchForScreening = searchForScreening,
                        everyMovie = everyMovie,
                        foundMovieInfo = foundMovieInfo
                        )

@app.route('/movie/<MovieID>', methods=['GET','POST'])
def movieInformation(MovieID):
    resetBookingSessionData()
    lastMovie = models.Movie.query.order_by(models.Movie.MovieID.desc()).first()
    if int(lastMovie.MovieID) < int(MovieID): #If try and get to URL where no movie exists for it
        return redirect('/') # Redirect back to home
    movie = models.Movie.query.filter_by(MovieID=MovieID).first()
    screenings = models.Screening.query.filter_by(MovieID = MovieID).all()
    # Code below removes any screenings that have already happended so you can't direct to buy tickets
    futureScreenings = []
    for screening in screenings:
        if screening.StartTimestamp > datetime.datetime.now():
            futureScreenings.append(screening)
    screenings = futureScreenings
    numScreenings = len(screenings)
    if request.method == 'POST':
        foundScreeningID = request.form.get("buy")
        # Needs here to be replaced with a redirect to the specific ticket booking of that screening
        return redirect('/seats/' + str(foundScreeningID))
    return render_template('movie-information.html',
                    title="Movie Information - " + movie.Name,
                    movie = movie,
                    screenings = screenings,
                    numScreenings = numScreenings
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
                        newScreening = models.Screening(MovieID=findMovie.MovieID, ScreenID = int(addScreeningForm.screen.data[7]),
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

@app.route('/test', methods=['GET','POST'])
def t():
    enterMovieForm = forms.enterMovie()
    if enterMovieForm.validate_on_submit():
                session['movie'] = enterMovieForm.movietitle.data
                return redirect(url_for('index'))

    return render_template('book-tickets.html',
                            title='Book Tickets',
                            enterMovieForm = enterMovieForm,
                            page=1, user=current_user.Email
                            )

@app.route('/seats/<screening>')
def seats(screening):   #seat selection page
    if current_user.is_authenticated:
        screening = models.Screening.query.get(screening) #get screening

        return render_template('seating-auto-layout.html',
        rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
        vip=['D', 'E', 'F'],
        reserved = screening.reserved(),
        screening=screening)
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
        child = child)

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

        if PaymentDetailsForm.validate_on_submit() or UseCard.validate_on_submit():

            if PaymentDetailsForm.Save.data:    #add card to db if use chooses
                card = models.Card(UserID=current_user.UserID, CardNo=PaymentDetailsForm.CardNo.data ,Name=PaymentDetailsForm.Name.data, Expiry=datetime.datetime.strptime(PaymentDetailsForm.Expiry.data, '%m-%y'), CVV=PaymentDetailsForm.CVV.data)
                db.session.add(card)
                db.session.commit()

            newBooking = models.Booking(UserID=current_user.UserID, ScreeningID=screeningID, Timestamp=datetime.datetime.now(), TotalPrice=total)
            db.session.add(newBooking)  #create and add new booking
            db.session.commit()

            for item in order:  #create and add new tickets to booking
                seatID = models.Seat.query.filter(models.Seat.ScreenID==screening.ScreenID).filter(models.Seat.code==item[0]).first().SeatID
                newTicket = models.Ticket(BookingID=newBooking.BookingID, SeatID=seatID, Category=item[1], QR='qr')
                db.session.add(newTicket)
            db.session.commit()

            screening = models.Screening.query.filter_by(ScreeningID=newBooking.ScreeningID).first()
            screen = screening.ScreeningID
            i=0
            filenames=[]
            for ticket in models.Ticket.query.filter_by(BookingID=newBooking.BookingID): # For all of the tickets just purchased
                # Make QR code for ticket
                qr_filename = 'app\static/ticket/qr/qr'+str(ticket.TicketID)+'.png'
                qr = pyqrcode.create(ticket.QR)
                qr.png(qr_filename, scale=6)

                if ticket.Category == 1:
                    Category = "Adult"
                elif ticket.Category == 2:
                    Category = "Child"
                elif ticket.Category == 3:
                    Category = "Senior"
                else:
                    Category = "Unknown"

                #Make a PDF for the ticket
                filename = 'app\static\\ticket\\tickets\\ticket'+str(ticket.TicketID)+'.pdf'
                CreatePDF.MakePDF('app\static\\ticket\\tickets\\ticket'+str(ticket.TicketID)+'.pdf', qr_filename, session['movie'], order[i][0], Category, str(screen), str(newBooking.Timestamp.date()), str(newBooking.Timestamp.time()))
                filenames.append(filename)
                i += 1

            # Send all the PDFs in an email to the user
            # First argument gives the destination email, currently set to email ourselves to prevent one of us receiving lots of emails during testing
            SendEmail.SendMail("leeds.cineplanet.com", filenames)
            # Un-comment the line below to send emails to their actual destination
            #SendEmail.SendMail(current_user.email, filenames)

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

        if Paid.validate_on_submit():

            newBooking = models.Booking(UserID=current_user.UserID, ScreeningID=screeningID, Timestamp=datetime.datetime.now(), TotalPrice=total)
            db.session.add(newBooking)  #create and add new booking
            db.session.commit()

            for item in order:  #create and add new tickets to booking
                seatID = models.Seat.query.filter(models.Seat.ScreenID==screening.ScreenID).filter(models.Seat.code==item[0]).first().SeatID
                newTicket = models.Ticket(BookingID=newBooking.BookingID, SeatID=seatID, Category=item[1], QR='qr')
                db.session.add(newTicket)
            db.session.commit()

            screening = models.Screening.query.filter_by(ScreeningID=newBooking.ScreeningID).first()
            screen = screening.ScreeningID
            i=0
            filenames=[]
            for ticket in models.Ticket.query.filter_by(BookingID=newBooking.BookingID): # For all of the tickets just purchased
                # Make QR code for ticket
                qr_filename = 'app\static/ticket/qr/qr'+str(ticket.TicketID)+'.png'
                qr = pyqrcode.create(ticket.QR)
                qr.png(qr_filename, scale=6)

                if ticket.Category == 1:
                    Category = "Adult"
                elif ticket.Category == 2:
                    Category = "Child"
                elif ticket.Category == 3:
                    Category = "Senior"
                else:
                    Category = "Unknown"

                #Make a PDF for the ticket
                filename = 'app\static\\ticket\\tickets\\ticket'+str(ticket.TicketID)+'.pdf'
                CreatePDF.MakePDF('app\static\\ticket\\tickets\\ticket'+str(ticket.TicketID)+'.pdf', qr_filename, session['movie'], order[i][0], Category, str(screen), str(newBooking.Timestamp.date()), str(newBooking.Timestamp.time()))
                filenames.append(filename)
                i += 1

            # Send all the PDFs in an email to the user
            # First argument gives the destination email, currently set to email ourselves to prevent one of us receiving lots of emails during testing
            SendEmail.SendMail("leeds.cineplanet.com", filenames)
            # Un-comment the line below to send emails to their actual destination
            #SendEmail.SendMail(current_user.email, filenames)

            return redirect(url_for('index'))

        return render_template('cash-payment.html', title='Checkout',
                            total = total,
                            displayOrder = displayOrder,
                            Paid = Paid,
                            cards = current_user.Cards.all()
                            )
    else:
        flash('You must be signed in to book tickets')
        return redirect(url_for('login'))

@app.route('/profile', methods=['GET','POST'])
def settings():
    if current_user.is_authenticated:
        form = forms.changePasswordForm()
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
                            form=form)
    else:
        logging.warning('Anonymous user attempted to access settings page')
        return redirect('/signIn')

