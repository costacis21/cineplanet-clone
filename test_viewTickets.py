import unittest, os
from app import app,models,forms,db,admin,CreatePDF,SendEmail
from flask import request, session, logging, g
from passlib.hash import sha256_crypt
from flask_login import current_user, login_user, logout_user
from werkzeug.local import LocalProxy
import fitz
from pyzbar.pyzbar import decode
from PIL import Image
import datetime
import uuid
import pyqrcode
import logging as log

pil_logger = log.getLogger('PIL')
pil_logger.setLevel(log.INFO)

def get_db():
    with app.app_context():
        if 'db' not in g:
            g.db = connect_to_database()
        return g.db

@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def makeTickets(users):
    # Adding the tickets that are used for these unit tests
    c = 1
    tickets=[]
    QRs=[]
    Seats=[]
    Categories=[]
    Types=[]
    for user in [users]:
        bookings = models.Booking.query.filter_by(UserID=user.UserID).all()
        for booking in bookings:
            for i in range(0,6):
                newTicket = models.Ticket(BookingID=booking.BookingID, SeatID=c, Category=(i+1)%3, QR=str(uuid.uuid4()))
                db.session.add(newTicket)
                db.session.commit()
                c += 1

                tickets.append(models.Ticket.query.order_by(models.Ticket.TicketID.desc()).first())
            
            screening=models.Screening.query.filter_by(ScreeningID=booking.ScreeningID).first()
            movie = models.Movie.query.filter_by(MovieID=screening.MovieID).first().Name
            for ticket in tickets:
                qr_filename = os.getcwd() + '/app/static/ticket/qr/qr'+str(ticket.TicketID)+'.png'
                qr = pyqrcode.create('http://127.0.0.1:5000/'+ticket.QR) # Needs to be changed to not have the port hardcoded into it
                #qr = pyqrcode.create(ticket.QR)
                qr.png(qr_filename, scale=6)

                seat = models.Seat.query.filter_by(SeatID=ticket.SeatID).first()

                if seat.Type == 0:
                    seatType = "Standard"
                elif seat.Type == 1:
                    seatType = "Premium"

                if ticket.Category == 1:
                    ticketCategory = "Adult"
                elif ticket.Category == 2:
                    ticketCategory = "Child"
                elif ticket.Category == 3:
                    ticketCategory = "Senior"

                QRs.append(qr_filename)
                Seats.append(seat.code)
                Categories.append(ticketCategory)
                Types.append(seatType)

            filename = os.getcwd() + '/app/static/ticket/tickets/booking'+str(ticket.BookingID)+'.pdf'
            CreatePDF.MakePDF(filename, QRs, movie, Seats, Categories, str(screening.ScreenID), str(screening.StartTimestamp.date().strftime('%d/%m/%y')), str(screening.StartTimestamp.time().strftime('%H:%M')), Types)

def delete_all():
    users = [models.User.query.filter_by(Email='test@gmail.com').first(), models.User.query.filter_by(Email='test2@admin.com').order_by(models.User.UserID.desc()).first()]
    for user in users:
        if user is not None:
            bookings = models.Booking.query.filter_by(UserID=user.UserID).all()
            for booking in bookings:
                tickets = models.Ticket.query.filter_by(BookingID=booking.BookingID).all()
                for ticket in tickets:
                    db.session.delete(ticket)
                
                db.session.delete(booking)

            cards = models.Card.query.filter_by(UserID=user.UserID).all()
            for card in cards:
                db.session.delete(card)

            db.session.delete(user)

    db.session.commit()
    db.session.close()

def addRecords():
    # Adding the screenings that are used for these unit tests
    if not (len(models.Screening.query.order_by(models.Screening.ScreeningID.desc()).all()) >= 2):
        print("made screening")
        for i in range(0,2):
            movies = models.Movie.query.order_by(models.Movie.MovieID.desc()).all()
            screens = models.Movie.query.order_by(models.Screen.ScreenID.desc()).all()
            newScreening = models.Screening(MovieID=movies[i].MovieID, ScreenID=screens[i].ScreenID, StartTimestamp=datetime.datetime.now() + timedelta(days=i), EndTimestamp=datetime.datetime.now() + timedelta(days=i) + timedelta(hours=i))
            db.session.add(newScreening)
            db.session.commit()

    # Creates the customer account that is used for most of these tests if it doesn't already exist
    if not models.User.query.filter_by(Email='test@gmail.com').first():
        print("made test user")
        newUser = models.User(Email='test@gmail.com', Password=sha256_crypt.encrypt('password'), Privilage=2)
        db.session.add(newUser)
        db.session.commit()

        # Adding the bookings that are used for these unit tests
        user1 = models.User.query.filter_by(Email='test@gmail.com').first()
        screening1 = models.Screening.query.order_by(models.Screening.ScreeningID.desc()).first()
        for i in range(0,2):
            newBooking = models.Booking(UserID=user1.UserID, ScreeningID=screening1.ScreeningID, Timestamp=datetime.datetime.now(), TotalPrice=i*5)
            db.session.add(newBooking)
            db.session.commit()

        makeTickets(user1)

    # Creates the admin account that is used for most of these tests if it doesn't already exist
    if not models.User.query.filter_by(Email='test2@admin.com').first():
        print("made second test user")
        newUser = models.User(Email='test2@admin.com', Password=sha256_crypt.encrypt('password'), Privilage=0)
        db.session.add(newUser)
        db.session.commit()

        user2 = models.User.query.filter_by(Email='test2@admin.com').first()
        screening2 = models.Screening.query.order_by(models.Screening.ScreeningID.asc()).first()
        for i in range(0,2):
            newBooking = models.Booking(UserID=user2.UserID, ScreeningID=screening2.ScreeningID, Timestamp=datetime.datetime.now(), TotalPrice=i*4)
            db.session.add(newBooking)
            db.session.commit()

        makeTickets(user2)

    db.session.close()

class BasicTests(unittest.TestCase):
    # executed prior to each test
    def setUp(self):
        #PRESERVE_CONTEXT_ON_EXCEPTION = False
        #app.config['SQLALCHEMY_ECHO'] = True
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = True
        app.config['DEBUG'] = False
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app\\app.db')
        self.app = app.test_client()
        #db = LocalProxy(get_db())
        delete_all()
        addRecords()
 
    # executed after each test
    def tearDown(self):
        pass

    # Tests the /view-ticekts page of the application
    def test_viewTickets(self):
        with app.test_client() as c:

            # Asserts that if you try and access /view-tickets while not logged in, you will be redirected to the login page
            # Asserts that when this happens, the correct error message is flashed to the user
            r1 = c.get('/view-tickets/0', follow_redirects=True)
            self.assertEqual(r1.status_code, 200, "The page could not be reached")
            self.assertEqual(request.path, '/login', "The user should be redirected to the login page, they weren't")
            self.assertTrue('You must be signed in to view tickets' in str(r1.data), "The correct error message was not displayed to the user")

            # Logs the user in to a customer account
            r2 = c.get('/test-login', follow_redirects=True)

            #Gets the UserID of the account just logged in to
            user = models.User.query.filter_by(Email='test@gmail.com').first()

            # Asserts that if you try and access /view-tickets while logged in but you attempt to view tickets that don't exist then you are redirected to the home page
            # Asserts that when this happens, the correct error message is flashed to the user
            r3 = c.get('/view-tickets/0', follow_redirects=True)
            self.assertEqual(r3.status_code, 200, "The page could not be reached")
            self.assertEqual(request.path, '/', "The user should be redirected to the home page, they weren't")
            self.assertTrue('Tickets not found' in str(r3.data), "The correct error message was not displayed to the user")

            # Gets a booking made by a different user account
            admin = models.User.query.filter_by(Email='admin@admin.com').first()
            invalid_booking = models.Booking.query.filter_by(UserID=admin.UserID).first()

            # Asserts that if you try and access /view-tickets while logged in but you attempt to view tickets that exist but are attached to a different user account then you are redirected to the home page
            # Asserts that when this happens, the correct error message is flashed to the user
            r4 = c.get('/view-tickets/'+str(invalid_booking.BookingID), follow_redirects=True)
            self.assertEqual(r4.status_code, 200, "The page could not be reached")
            self.assertEqual(request.path, '/', "The user should be redirected to the home page, they weren't")
            self.assertTrue("You cannot view another user&#39;s bookings" in str(r4.data), "The correct error message was not displayed to the user")
            # Have to replace ' with &#39; here due to the way HTML encodes things

            # Gets a booking made by the current user account
            valid_booking = models.Booking.query.filter_by(UserID=user.UserID).first()

            # Asserts that if you try and access /view-tickets while logged in and you attempt to view tickets that exist and are attached to your user account then you are not redirected
            r5 = c.get('/view-tickets/'+str(valid_booking.BookingID), follow_redirects=True)
            self.assertEqual(r5.status_code, 200, "The page could not be reached")
            self.assertEqual(request.path, '/view-tickets/'+str(valid_booking.BookingID), "The user should not be redirected, they were")

            # Asserts that the requested ticket pdf is displayed
            self.assertTrue('booking'+str(valid_booking.BookingID)+'.pdf' in str(r5.data), "The requested pdf ticket was not displayed")

            # Asserts that only the requested pdf is displayed
            # Does this by checking that the number of pdfs displayed is 1
            # This, in combination with the above test the requested pdf is displayed, assert the statement
            occurrences = [i for i in range(len(str(r3.data))) if str(r3.data).startswith('.pdf', i)]

            # Opens the requested ticket pdf
            with fitz.open('app/static/ticket/tickets/booking'+str(valid_booking.BookingID)+'.pdf') as document:
                text = ""
                for page in document:
                    text += page.getText()

            # Gets all ticket records corresponding to the BookingID of the ticket pdf requested 
            tickets = models.Ticket.query.filter_by(BookingID=valid_booking.BookingID).all()
            screening = models.Screening.query.filter_by(ScreeningID=valid_booking.ScreeningID).first()
            for ticket in tickets:
                movie = models.Movie.query.filter_by(MovieID=screening.MovieID).first()
                seat = models.Seat.query.filter_by(SeatID=ticket.SeatID).first()

                if seat.Type == 0:
                    seatType = "Standard"
                elif seat.Type == 1:
                    seatType = "Premium"

                if ticket.Category == 1:
                    ticketCategory = "Adult"
                elif ticket.Category == 2:
                    ticketCategory = "Child"
                elif ticket.Category == 3:
                    ticketCategory = "Senior"

                # Asserts that the information on each ticket on the booking pdf is correct
                # Does this by checking that all the information for one ticket is included together in the same section
                self.assertTrue('Movie Name: '+movie.Name+'\n'+'Seat: '+seat.code+'\n'+'Seat Type: '+seatType+'\n'+'Seat Category: '+ticketCategory in text)

                # Asserts that the QR code used for each ticket has the correct information
                qr = decode(Image.open('app/static/ticket/qr/qr'+str(ticket.TicketID)+'.png'))
                self.assertEqual(str(qr[0][0].decode("utf-8")),'http://127.0.0.1:5000/'+ticket.QR)

            # Asserts that there is only the relevant information on the ticket (i.e. only the information for the relevant tickets)
            # Does this by checking that the number of sets of ticket information on the ticket is the same as the number of tickets on the booking
            # This, in combination with the above test that all relevant information is on the ticket, asserts the statement
            occurrences = [i for i in range(len(str(text))) if str(text).startswith('Movie Name:', i)]
            self.assertEqual(len(occurrences), len(tickets))
            occurrences = [i for i in range(len(str(text))) if str(text).startswith('Seat:', i)]
            self.assertEqual(len(occurrences), len(tickets))
            occurrences = [i for i in range(len(str(text))) if str(text).startswith('Seat Type:', i)]
            self.assertEqual(len(occurrences), len(tickets))
            occurrences = [i for i in range(len(str(text))) if str(text).startswith('Seat Category:', i)]
            self.assertEqual(len(occurrences), len(tickets))

if __name__ == "__main__":
    unittest.main()
