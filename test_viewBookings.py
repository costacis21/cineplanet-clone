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

            # Asserts that if you try and access /view-bookings while logged in, you can access the page and you are not redirected
            r3 = c.get('/view-bookings', follow_redirects=True)
            self.assertEqual(r3.status_code, 200)
            self.assertEqual(request.path, '/view-bookings')

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
