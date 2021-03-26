import unittest, os
from app import app,models,forms,db,admin
from flask import request, session, logging, g
from passlib.hash import sha256_crypt
from flask_login import current_user, login_user, logout_user
from werkzeug.local import LocalProxy

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

        if not models.User.query.filter_by(Email='test@gmail.com').first():
            newUser = models.User(Email='test@gmail.com', Password=sha256_crypt.encrypt('password'), Privilage=2)
            db.session.add(newUser)
            db.session.commit()
 
    # executed after each test
    def tearDown(self):
        pass
    
    def test_attempt(self):
        with app.test_client() as c:
            r1 = c.get('/test-login', follow_redirects=True)
            self.assertEqual(r1.status_code, 200)
            self.assertEqual(request.path, '/profile')

    # Tests the /view-bookings page of the application
    def test_viewBookings(self):
        with app.test_client() as c:
            # Asserts that if you try and access /view-bookings while not logged in, you will be redirected to the login page
            r1 = c.get('/view-bookings', follow_redirects=True)
            self.assertEqual(r1.status_code, 200)
            self.assertEqual(request.path, '/login')   
            
            # Logs the user in
            r2 = c.get('/test-login', follow_redirects=True)

            #Gets the UserID of the account just logged in to
            user = models.User.query.filter_by(Email='test@gmail.com').first()

            # Asserts that if you try and access /view-bookings while logged in, you can access the page and you are not redirected
            r3 = c.get('/view-bookings', follow_redirects=True)
            self.assertEqual(r3.status_code, 200)
            self.assertEqual(request.path, '/view-bookings')

            # Asserts that there is a link on the page to all bookings that are made by the logged in user
            # Asserts that the links all work corrrectly
            bookings = models.Booking.query.filter_by(UserID=user.UserID).all()
            for booking in bookings:
                self.assertTrue('a href=" '+request.url_root+'/view-tickets/'+str(booking.BookingID)+'"' in str(r3.data))

                r4 = c.get(request.url_root+'/view-tickets/'+str(booking.BookingID), follow_redirects=True)
                self.assertEqual(r4.status_code, 200)
                self.assertEqual(request.path, '/view-tickets/'+str(booking.BookingID))

            # Asserts that there are no links on the page to bookings that are not made by the logged in user
            # Does this by checking that the number of links to bookings is the same as the number of bookings made by the logged in user
            # This, in combination with the above test that all links to bookings are to ones that are made by the logged in user, assert the statement
            occurrences = [i for i in range(len(str(r3.data))) if str(r3.data).startswith('a href=" '+request.url_root+'/view-tickets/', i)]
            self.assertEqual(len(occurrences), len(bookings))

    """
    def signUpLogin(self, c):
        newUser = models.User(Email='johnsmith@gmail.com', Password=sha256_crypt.encrypt('password'), Privilage=2)
        db.session.add(newUser)
        #login_user(newUser)
        db.session.commit()

        login_response = c.post('/login', data={'Email':'johnsmith@gmail.com', 'Password':'password'},
                                follow_redirects=True)
            
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(request.path, '/')

    def testSignUpLogin(self):
        with app.test_request_context() as c:
            SignUpLogIn()
            self.assertEqual(models.User.query.order_by(models.User.UserID.desc()).first().Email, 'pearce05@ntlworld.com')
            self.assertEqual(current_user.Email, 'pearce05@ntlworld.com')

    def testViewBookings(self):
        with app.test_request_context() as r:
            #current_user only exists withing app.test_request_context()
            #print("current user's email is ", current_user.Email)
            SignUpLogIn()
            with app.test_client(current_user) as c:
                #self.signUpLogin(c)
                response = c.get('/view-bookings',
                                follow_redirects=True)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(request.path, '/')
    """

if __name__ == "__main__":
    unittest.main()
