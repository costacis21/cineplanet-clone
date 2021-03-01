import unittest, os
from app import app,models,forms,db,admin
from flask import request, session, logging
from passlib.hash import sha256_crypt
from flask_login import current_user, login_user, logout_user

class BasicTests(unittest.TestCase):
    # executed prior to each test
    def setUp(self):
        #PRESERVE_CONTEXT_ON_EXCEPTION = False
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app/test.db')
        self.app = app.test_client()
        db.drop_all()
        db.create_all()

    # executed after each test
    def tearDown(self):
        pass

    # Ensure webpage is set up correctly
    def test_addtaskroute(self):
        tester = app.test_client(self)
        home = tester.get('/addMovieScreening',follow_redirects=True)
        self.assertEqual(home.status_code, 200)


    def test_unsuccessful_add_screening(self):
        tester = app.test_client(self)
        response = self.app.post('/addMovieScreening',
                                data={'movie': 'an example movie', 'screen': 'none', 'start': 'not correct', 'end': 'shouldnt be here'},
                                follow_redirects=True)
        added = models.Movie.query.filter_by(Name='an example movie').all()
        self.assertEqual(len(added), 0)

if __name__ == "__main__":
    unittest.main()
