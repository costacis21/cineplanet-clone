import unittest, os
from app import app,models,forms,db,admin,CreatePDF,SendEmail
from flask import request, session, logging, g
from passlib.hash import sha256_crypt
from flask_login import current_user, login_user, logout_user
from werkzeug.local import LocalProxy
import datetime
import uuid
import pyqrcode

def get_db():
    if 'db' not in g:
        g.db = connect_to_database()
    return g.db

@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def makeTickets(users):
    print("You called?")
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
    print(app.config['SQLALCHEMY_DATABASE_URI'])
    bookings = models.Booking.query.order_by(models.Booking.BookingID.desc()).all()
    for booking in bookings:
        db.session.delete(booking)

    tickets = models.Ticket.query.order_by(models.Ticket.TicketID.desc()).all()
    for ticket in tickets:
        db.session.delete(ticket)

    users = models.User.query.order_by(models.User.UserID.desc()).all()
    for user in users:
        db.session.delete(user)

    cards = models.Card.query.order_by(models.Card.CardID.desc()).all()
    for card in cards:
        db.session.delete(card)

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
    if not models.User.query.filter_by(Email='admin@admin.com').first():
        print("made admin user")
        newUser = models.User(Email='admin@admin.com', Password=sha256_crypt.encrypt('password'), Privilage=0)
        db.session.add(newUser)
        db.session.commit()

        user2 = models.User.query.filter_by(Email='admin@admin.com').first()
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
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = True
        app.config['DEBUG'] = False
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app/app.db')
        self.app = app.test_client()
        db = LocalProxy(get_db)
        #delete_all()
        addRecords()
 
    # executed after each test
    def tearDown(self):
        pass

    # Tests the /validate-ticket page of the application
    def test_validateTicket(self):
        with app.test_client() as c:
            
            # Asserts that if you try and access /validate-ticket while not logged in, you will be redirected to the login page
            # Asserts that when this happens, the correct error message is flashed to the user
            r1 = c.get('/validate-ticket/a', follow_redirects=True)
            self.assertEqual(r1.status_code, 200)
            self.assertEqual(request.path, '/login')   
            self.assertTrue('You must be signed in to validate tickets' in str(r1.data))

            # Logs the user in to a customer account
            r2 = c.get('/test-login', follow_redirects=True)

            # Asserts that if you try and access /validate-ticket while logged in to a customer account, you will be redirected to the home page
            # Asserts that when this happens, the correct error message is flashed to the user
            r3 = c.get('/validate-ticket/a', follow_redirects=True)
            self.assertEqual(r3.status_code, 200)
            self.assertEqual(request.path, '/')
            self.assertTrue('You do not have the required permissions to validate tickets' in str(r3.data))

            # Asserts that if you try and access /validate-ticekt while logged in to an admin account, you won't be redirected
            # Logs the user out of the current account and into an admin account
            r4 = c.get('/logout', follow_redirects=True)
            r5 = c.get('/test-admin-login', follow_redirects=True)

            # Asserts that the /validate-ticket page can be accessed correctly w
            r6 = c.get('/validate-ticket/a', follow_redirects=True)
            self.assertEqual(r3.status_code, 200)
            self.assertEqual(request.path, '/validate-ticket/a')

            # Asserts that when an invalid uuid is given for a ticket, then the user is informed of this correctly
            self.assertTrue('Invalid ticket' in str(r6.data))
            self.assertTrue('cross.jpg' in str(r6.data))

            # Gets the QR field of a ticket from the database
            valid_uuid = models.Ticket.query.order_by(models.Ticket.TicketID.desc()).first().QR

            # Asserts that the /validate-ticket page can be accessed correctly when given a valid ticket uuid
            r7 = c.get('/validate-ticket/'+str(valid_uuid), follow_redirects=True)
            self.assertEqual(r3.status_code, 200)
            self.assertEqual(request.path, '/validate-ticket/'+str(valid_uuid))

            # Asserts that when an valid uuid is given for a ticket, then the user is informed of this correctly
            self.assertTrue('Ticket validated successfully' in str(r7.data))
            self.assertTrue('tick.jpg' in str(r7.data))

if __name__ == "__main__":
    unittest.main()
