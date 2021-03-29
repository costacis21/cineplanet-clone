import unittest, os
from app import app,models,forms,db,admin
from flask import request, session, logging, g
from passlib.hash import sha256_crypt
from flask_login import current_user, login_user, logout_user
from werkzeug.local import LocalProxy
import datetime
import uuid
import string
import random

def get_db():
    if 'db' not in g:
        g.db = connect_to_database()
    return g.db

@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def addRecords():

    # Creates the customer account that is used for most of these tests if it doesn't already exist
    if not models.User.query.filter_by(Email='test@gmail.com').first():
        newUser = models.User(Email='test@gmail.com', Password=sha256_crypt.encrypt('password'), Privilage=2)
        db.session.add(newUser)
        db.session.commit()

    # Creates the admin account that is used for most of these tests if it doesn't already exist
    if not models.User.query.filter_by(Email='admin@admin.com').first():
        newUser = models.User(Email='admnin@admin.com', Password=sha256_crypt.encrypt('password'), Privilage=0)
        db.session.add(newUser)
        db.session.commit()


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
        addRecords()
 
    # executed after each test
    def tearDown(self):
        pass
    
    # Tests the /profile page of the application
    def test_management(self):
        with app.test_client() as c:

            # Asserts that if you try and access /manage-staff while not logged in, you will be redirected to the login page
            # Asserts that when this happens, the correct error message is flashed to the user
            r1 = c.get('/manage-staff', follow_redirects=True)
            self.assertEqual(r1.status_code, 200)
            self.assertEqual(request.path, '/login')   
            self.assertTrue('You must be signed in to access to this functionality' in str(r1.data))

            # Logs the user in to a customer account
            r2 = c.get('/test-login', follow_redirects=True)

            # Asserts that if you try and access /manage-staff while logged in to a customer account, you will be redirected to the home page
            # Asserts that when this happens, the correct error message is flashed to the user
            r3 = c.get('/manage-staff', follow_redirects=True)
            self.assertEqual(r3.status_code, 200)
            self.assertEqual(request.path, '/')
            self.assertTrue('Your account does not have access to this functionality' in str(r3.data))

            # Asserts that if you try and access /manage-staff while logged in to an admin account, you won't be redirected
            # Logs the user out of the current account and into an admin account
            r4 = c.get('/logout', follow_redirects=True)
            r5 = c.get('/test-admin-login', follow_redirects=True)

            # Asserts that if you try and access /manage-staff while logged in, you can access the page and you are not redirected
            r3 = c.get('/manage-staff', follow_redirects=True)
            self.assertEqual(r3.status_code, 200)
            self.assertEqual(request.path, '/manage-staff')

            staff = models.User.query.filter(models.User.Privilage <= 1).order_by(models.User.Privilage.asc()).all() #get all staff members
            self.assertGreater(len(staff), 0)
            for member in staff:

                # Asserts that the card number is printed
                self.assertTrue(str(member.Email) in str(r3.data))
            

if __name__ == "__main__":
    unittest.main()
