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
            with c.session_transaction() as sess:
                sess['testing'] = True
            
            r1 = c.get('/test-login', follow_redirects=True)
            self.assertEqual(r1.status_code, 200)
            self.assertEqual(request.path, '/profile')

    # Tests the /view-bookings page of the application
    def test_viewBookings(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess['testing'] = True
            
            # Asserts that if you try and access /validate-ticket while not logged in, you will be redirected to the login page
            # Asserts that when this happens, the correct error message is flashed to the user
            r1 = c.get('/validate-ticket/a', follow_redirects=True)
            self.assertEqual(r1.status_code, 200)
            self.assertEqual(request.path, '/login')   
            self.assertTrue('You must be signed in to validate tickets' in str(r1.data))

            # Logs the user in to a customer account
            r2 = c.get('/test-login', follow_redirects=True)

            #Gets the UserID of the account just logged in to
            user = models.User.query.filter_by(Email='test@gmail.com').first()

            # Asserts that if you try and access /validate-ticket while logged in to a customer account, you will be redirected to the home page
            # Asserts that when this happens, the correct error message is flashed to the user
            r3 = c.get('/validate-ticket/a', follow_redirects=True)
            self.assertEqual(r3.status_code, 200)
            self.assertEqual(request.path, '/')
            self.assertTrue('You do not have the required permissions to validate tickets' in str(r3.data))

            # Asserts that if you try and access /validate-ticekt while logged in to an admin account, you won't be redirected
            # Logs the user out of the current account and into an admin account
            r4 = c.get('/logout', follow_redirects=True)
            with c.session_transaction() as sess:
                sess['testing'] = True
            r5 = c.get('/test-admin-login', follow_redirects=True)

            # Asserts that the /validate-ticket page can be accessed correctly
            r6 = c.get('/validate-ticket/a', follow_redirects=True)
            self.assertEqual(r3.status_code, 200)
            self.assertEqual(request.path, '/validate-ticket/a')

            # Asserts that when an invalid uuid is given for a ticket, then the user is informed of this correctly
            self.assertTrue('Invalid ticket' in str(r6.data))
            self.assertTrue('cross.jpg' in str(r6.data))

            # Gets the QR field of a ticket from the database
            valid_uuid = models.Ticket.query.order_by(models.Ticket.TicketID.desc()).first().QR

            # Asserts that the /validate-ticket page can be accessed correctly
            r7 = c.get('/validate-ticket/'+str(valid_uuid), follow_redirects=True)
            self.assertEqual(r3.status_code, 200)
            self.assertEqual(request.path, '/validate-ticket/'+str(valid_uuid))

            # Asserts that when an invalid uuid is given for a ticket, then the user is informed of this correctly
            self.assertTrue('Ticket validated successfully' in str(r7.data))
            self.assertTrue('tick.jpg' in str(r7.data))

if __name__ == "__main__":
    unittest.main()
