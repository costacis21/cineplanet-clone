import unittest, os
from app import app,models,forms,db,admin
from flask import request, session
from passlib.hash import sha256_crypt
from flask_login import current_user, login_user, logout_user

class BasicTests(unittest.TestCase):
    # executed prior to each test
    def setUp(self):
        #PRESERVE_CONTEXT_ON_EXCEPTION = False
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = True#If this is false you get lots of errors, idk if it needs to be false though
        app.config['DEBUG'] = False
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app/app.db')
        self.app = app.test_client()
        db.drop_all()
        db.create_all()
 
    # executed after each test
    def tearDown(self):
        pass

    def signUpLogin(self):
        newUser = models.User(Email='sc19ap@leeds.ac.uk', Password=sha256_crypt.encrypt('pass'), Privilage=2)
        db.session.add(newUser)
        login_user(newUser)
        db.session.commit()

    #Tests that if you are not logged in and you try to access any part of the booking process, you are redirected to the login page
    def testRedirectionIfNotLoggedIn(self):
        with app.test_client() as c:
            #with app.test_request_context():
            tester = app.test_client(self)
            
            #Attempting to access /bookTickets
            response = c.post('/bookTickets',
                                    data ={'movietitle':'up'},
                                    follow_redirects=True)
                
            #Checks that the request reached a webpage
            self.assertEqual(response.status_code, 200)

            #Checks that you are redirected to the login page if not logged in
            self.assertEqual(request.path, '/login')

            # ---------------------------------

            #Attempting to access /bookTickets/2
            response = c.post('/bookTickets/2',
                                    data ={'screeningnumber':1},
                                    follow_redirects=True)
                
            #Checks that the request reached a webpage
            self.assertEqual(response.status_code, 200)

            #Checks that you are redirected to the login page if not logged in
            self.assertEqual(request.path, '/login')  

            # ---------------------------------

            #Attempting to access /bookTickets/3
            response = c.post('/bookTickets/3',
                                    data ={'seatnumber':1, 'seatcategory':'Adult'},
                                    follow_redirects=True)
                
            #Checks that the request reached a webpage
            self.assertEqual(response.status_code, 200)

            #Checks that you are redirected to the login page if not logged in
            self.assertEqual(request.path, '/login')

            # ---------------------------------
            
            #Attempting to access /bookTickets/4
            response = c.post('/bookTickets/4',
                                    data ={'cardnumber':1, 'securitynumber':1},
                                    follow_redirects=True)
                
            #Checks that the request reached a webpage
            self.assertEqual(response.status_code, 200)

            #Checks that you are redirected to the login page if not logged in
            self.assertEqual(request.path, '/login')

    #Tests the test page
    def testTest(self):
        with app.test_client() as c:
            response = c.post('/test', data={'movietitle':'up'}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(forms.enterMovie().is_submitted(),True)
            self.assertEqual(session, 'up')
            self.assertEqual(request.path, '/')
    """
    #Tests the /bookTickets page
    def testBookTickets1(self):
        with app.test_client() as c:
            self.signUpLogin()
    """
    """
    def testSignupLogin(self):
        with app.test_client() as c:
            signup_response = c.post('/signup',
                                    data ={'email':'sc19ap@leeds.ac.uk', 'password':'pass', 'passwordCheck':'pass'},
                                    follow_redirects=True)

            #Checks that the request reached a webpage
            self.assertEqual(signup_response.status_code, 200)

            newUser = models.User(Email='sc19ap@leeds.ac.uk', Password=sha256_crypt.encrypt('pass'), Privilage=2)
            db.session.add(newUser)
            login_user(newUser)
            db.session.commit()

            user = models.User.query.filter_by(Email='sc19ap@leeds.ac.uk').first()
            #self.assertEqual(user, True)
            self.assertEqual(sha256_crypt.verify('pass', user.Password), True)

            #self.assertEqual(request.path, '/login')

            login_response = c.post('/login',
                                    data ={'email':'sc19ap@leeds.ac.uk', 'password':'pass'},
                                    follow_redirects=True)

            #checks that the request reached a webpage
            self.assertEqual(login_response.status_code, 200)

            #checks that the user is redirected to the homepage (which only happens on a successful login)
            self.assertEqual(request.path, '/')
    """


if __name__ == "__main__":
    unittest.main()