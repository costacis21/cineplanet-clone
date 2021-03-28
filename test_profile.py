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

    # Adding the saved payment methods that are used for these unit tests
    user1 = models.User.query.filter_by(Email='test@gmail.com').first()
    for i in range(3):
        newCard = models.Card(UserID=user1.UserID, CardNo=str(''.join(random.choices(string.digits, k = 16))), Name = str(''.join(random.choices(string.ascii_letters, k = 5))), CVV=str(''.join(random.choices(string.digits, k = 3))), Expiry=datetime.datetime.now())
        db.session.add(newCard)
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
    def test_profile(self):
        with app.test_client() as c:

            # Asserts that if you try and access /profile while not logged in, you will be redirected to the login page
            # Asserts that when this happens, the correct error message is flashed to the user
            r1 = c.get('/profile', follow_redirects=True)
            self.assertEqual(r1.status_code, 200)
            self.assertEqual(request.path, '/login')   
            self.assertTrue('You must be signed in to view profiles' in str(r1.data))
            
            # Logs the user in
            r2 = c.get('/test-login', follow_redirects=True)

            #Gets the UserID of the account just logged in to
            user = models.User.query.filter_by(Email='test@gmail.com').first()

            # Asserts that if you try and access /profile while logged in, you can access the page and you are not redirected
            r3 = c.get('/profile', follow_redirects=True)
            self.assertEqual(r3.status_code, 200)
            self.assertEqual(request.path, '/profile')

            user1 = models.User.query.filter_by(Email='test@gmail.com').first()
            cards = models.Card.query.filter_by(UserID=user1.UserID).all()
            for card in cards:
                # Asserts that the card number is printed
                self.assertTrue('xxxx-xxxx-xxxx-'+ str(card.CardNo)[12:] in str(r3.data))

                # Asserts that there is a link on the page to remove each card
                self.assertTrue('a href="/remove-card/'+ str(card.CardID)+'"' in str(r3.data))

                # Asserts that the link works correctly and card is removed
                r4 = c.get('/remove-card/'+str(card.CardID), follow_redirects=True)
                self.assertEqual(r4.status_code, 200)
                self.assertEqual(request.path, '/profile')
                self.assertFalse('xxxx-xxxx-xxxx-'+ str(card.CardNo)[12:] in str(r4.data))

                cards2 = models.Card.query.filter_by(UserID=models.User.query.filter_by(Email='test@gmail.com').first().UserID).all()
                self.assertNotIn(card, cards2)

if __name__ == "__main__":
    unittest.main()
