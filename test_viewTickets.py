import unittest, os
from app import app,models,forms,db,admin
from flask import request, session, logging, g
from passlib.hash import sha256_crypt
from flask_login import current_user, login_user, logout_user
from werkzeug.local import LocalProxy
import fitz
from pyzbar.pyzbar import decode
from PIL import Image

def get_db():
    if 'db' not in g:
        g.db = connect_to_database()
    return g.db

@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def SignUpLogIn(): #tests that users can be added to db and logged in
    newUser = models.User(Email='pearce05@ntlworld.com', Password=sha256_crypt.encrypt('password'), Privilage=2)
    db.session.add(newUser)
    login_user(newUser)
    db.session.commit()

class BasicTests(unittest.TestCase):
    # executed prior to each test
    def setUp(self):
        #PRESERVE_CONTEXT_ON_EXCEPTION = False
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = True
        app.config['DEBUG'] = False
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app/test.db')
        self.app = app.test_client()
        db = LocalProxy(get_db)

        # Creates the user account that is used for most of these tests if it doesn't already exist
        if not models.User.query.filter_by(Email='test@gmail.com').first():
            newUser = models.User(Email='test@gmail.com', Password=sha256_crypt.encrypt('password'), Privilage=2)
            db.session.add(newUser)
            db.session.commit()
 
    # executed after each test
    def tearDown(self):
        pass

    # Tests the /view-ticekts page of the application
    def test_viewTickets(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess['testing'] = True
            
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
