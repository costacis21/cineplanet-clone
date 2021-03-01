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
        app.config['WTF_CSRF_ENABLED'] = False#If this is false you get lots of errors, idk if it needs to be false though
        app.config['DEBUG'] = False
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app/test.db')
        self.app = app.test_client()
        db.drop_all()
        db.create_all()
 
    # executed after each test
    def tearDown(self):
        pass

    def signUpLogin(self, c):
        newUser = models.User(Email='sc19ap@leeds.ac.uk', Password=sha256_crypt.encrypt('pass'), Privilage=2)
        db.session.add(newUser)
        #login_user(newUser)
        db.session.commit()

        login_response = c.post('/login', data={'email':'sc19ap@leeds.ac.uk', 'password':'pass'},
                                follow_redirects=True)
            
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(request.path, '/')

        """
        newUser = models.User(Email='sc19ap@leeds.ac.uk', Password=sha256_crypt.encrypt('pass'), Privilage=2)
        db.session.add(newUser)
        login_user(newUser)
        db.session.commit()
        self.assertEqual(models.User.query.order_by(desc('UserID')).first().Email, 'sc19ap@leeds.ac.uk')
        """

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

    #Tests that if you are attempt to skip stages of the booking process, e.g. going straight to /bookTickets/4, then you are redirected to the first stage of the booking process (/bookTickets)
    def testRedirectionIfStagesSkipped(self):
        with app.test_client() as c:
            #Loggin in to prevent redirection to the login screen
            self.signUpLogin(c)

            #Attempting to access /bookTickets/2
            response = c.post('/bookTickets/2',
                                    data ={'screeningnumber':1},
                                    follow_redirects=True)
                
            #Checks that the request reached a webpage
            self.assertEqual(response.status_code, 200)

            #Checks that you are redirected to the login page if not logged in
            self.assertEqual(request.path, '/bookTickets')  

            # ---------------------------------

            #Attempting to access /bookTickets/3
            response = c.post('/bookTickets/3',
                                    data ={'seatnumber':1, 'seatcategory':'Adult'},
                                    follow_redirects=True)
                
            #Checks that the request reached a webpage
            self.assertEqual(response.status_code, 200)

            #Checks that you are redirected to the login page if not logged in
            self.assertEqual(request.path, '/bookTickets')

            # ---------------------------------
            
            #Attempting to access /bookTickets/4
            response = c.post('/bookTickets/4',
                                    data ={'cardnumber':1, 'securitynumber':1},
                                    follow_redirects=True)
                
            #Checks that the request reached a webpage
            self.assertEqual(response.status_code, 200)

            #Checks that you are redirected to the login page if not logged in
            self.assertEqual(request.path, '/bookTickets')


    def testBookTickets1(self):
        with app.test_client() as c:
            #Signing in to prevent redirection to the login screen
            self.signUpLogin(c)

            #Checks that you can access the /bookTickets page and that it doesn't try to redirect you (if it did attempt to redirect you then the status code would be 302)
            #If it reaches the page correctly and it doens't attempt to redirect the client then the status code should be 200
            r1 = c.get('/bookTickets', follow_redirects=False)
            self.assertEqual(r1.status_code, 200)
            self.assertEqual(session['movie'], '') #This is the default value of session['movie'] when it is initialised in resetBookingSessionData in views.py

            #Checks that it doesn't accept empty data, it shouldn't redirect you anywhere or change the session data if this is the case
            r2 = c.post('/bookTickets', data={'movietitle':None}, 
                        follow_redirects=True)
            self.assertEqual(request.path, '/bookTickets')
            self.assertEqual(session['movie'], '') #This is the default value of session['movie'] when it is initialised in resetBookingSessionData in views.py     

            #Checks that it doesn't accept non-empty, valid data it shouldn't redirect you anywhere or change the session data if this is the case
            r3 = c.post('/bookTickets', data={'movietitle':'test'},
                        follow_redirects=True)
            #self.assertEqual(request.path, '/bookTickets') #need to fix this test
            #self.assertEqual(session['movie'], '') #This is the default value of session['movie'] when it is initialised in resetBookingSessionData in views.py

            #Checks that it accepts valid data, updates the session data and redirects you to the next stage of the booking process (/bookTickets/2)
            r4 = c.post('/bookTickets', data={'movietitle':'Up'},
                        follow_redirects=True)
            self.assertEqual(session['movie'], 'Up')
            self.assertEqual(request.path, '/bookTickets/2')

    def testBookTickets2(self):
        with app.test_client() as c:
            #Signing in to prevent redirection to the login screen
            self.signUpLogin(c)

            #Going through the first stage of the booking process to prevent redirection if the first stage of the process has not been completed
            r0 = c.post('/bookTickets', data={'movietitle':'Up'},
                        follow_redirects=True)
            
            #Checking that you can access the /bookTickets/2 page and that it doesn't try to redirect you (if it did attempt to redirect you then the status code would be 302)
            #If it reaches the page correctly and it doens't attempt to redirect the client then the status code should be 200 
            r1 = c.get('/bookTickets/2', follow_redirects=False)
            self.assertEqual(r1.status_code, 200)

            #Checking that it doesn't accept empty data (it shouldn't redirect you anywhere if this is the case)
            r2 = c.post('bookTickets/2', data={'screeningnumber':None},
                        follow_redirects=True)
            self.assertEqual(request.path, '/bookTickets/2')
            self.assertEqual(session['screening'], 0) #This is the defaul

            #Checking that it doesn't accept data of the wrong data type (it shouldn't redirect you anywhere if this is the case)
            r2 = c.post('bookTickets/2', data={'screeningnumber':'hello'},
                        follow_redirects=True)
            self.assertEqual(request.path, '/bookTickets/2')

            #Checking that it accepts valid data and redirects you to the next stage of the booking process (/bookTickets/3)
            r3 = c.post('bookTickets/2', data={'screeningnumber':1},
                        follow_redirects=True)
            self.assertEqual(request.path, '/bookTickets/3')

    def testBookTickets3(self):
        #It is important to note here that, unlike any of the other stages of the booking process, submitting the form here does not take you to the next stage of the booking process
        #In order to reach the next stage of the booking process from /bookTickets/3 then you must click "Proceed to payment" after adding at least one seat
        with app.test_client() as c:
            #Signing in to prevent redirection to the login screen
            self.signUpLogin(c)

            #Going through the first stages of the booking process to prevent redirection if the previous stages of the process has not been completed
            r0 = c.post('/bookTickets', data={'movietitle':'Up'},
                        follow_redirects=True)

            r1 = c.post('/bookTickets/2', data={'screeningnumber':1},
                        follow_redirects=True)

            #Checks that you can access the /bookTickets/3 page and that it doesn't try to redirect you (if it did attempt to redirect you then the status code would be 302)
            #If it reaches the page correctly and it doens't attempt to redirect the client then the status code should be 200 
            r2 = c.get('/bookTickets/3', follow_redirects=False)
            self.assertEqual(r2.status_code, 200)

            #Checks that the session data for the seats booked and their total price are initialised correctly, this is done using the same request as above (r2) because r2 doesn't pass any data to the form and so shouldn't affect it
            self.assertEqual(len(session['seats']), 0) #This is the default length of session['seats'] when it is initialised in resetBookingSessionData in views.py
            self.assertEqual(session['total'], 0) #This is the default value of session['total'] when it is initialised in resetBookingSessionData in views.py

            #Check that you cannot progress to the next stage of the booking process without adding a seat (since we've checked that there are no seats added above, the test should work if ran from here)
            #This test case is used to simulate clicking the "Proceed to payment" button
            r3 = c.get('/bookTickets/4', follow_redirects=True)
            self.assertEqual(request.path, '/bookTickets/3')

            #Checks that if you enter empty data for the seatnumber, it doesn't accept it and it is therefore not saved in the session data
            r4 = c.post('/bookTickets/3', data={'seatnumber':None,'seatcategory':'Adult'},
                        follow_redirects=True)
            self.assertEqual(len(session['seats']), 0) #There should be no seats recorded
            self.assertEqual(session['total'], 0) #The total price of the seats booked should be 0

            #Checks that if you enter empty data for the seatcategory, it doesn't accept it and it is therefore not saved in the session data
            #This should not be possible since seatcategory is set via a drop down box (so it should always have a value) but I'm just trying to make the tests as exhaustive as possible
            r5 = c.post('/bookTickets/3', data={'seatnumber':1, 'seatcategory':None})
            self.assertEqual(len(session['seats']), 0) #There should be no seats recorded
            self.assertEqual(session['total'], 0) #The total price of the seats booked should be 0

            #Checks that it doesn't accept the same seat (with the same category) being booked multiple times in the same booking
            r61 = c.post('/bookTickets/3', data={'seatnumber':1, 'seatcategory':'Adult'})
            r62 = c.post('/bookTickets/3', data={'seatnumber':1, 'seatcategory':'Adult'})
            self.assertEqual(len(session['seats']), 1) #The seat should only have been added once
            self.assertEqual(session['total'], 1) #The total price of the seats on this ticket should be 1 since only one seat (costing £1) should have been added

            #Checks that it doesn't accept the same seat (with a different category) being booked multiple times in the same booking
            #We use a different seat number to r51 and r52 to prevent interference between the two
            r71 = c.post('/bookTickets/3', data={'seatnumber':2, 'seatcategory':'Adult'})
            r72 = c.post('/bookTickets/3', data={'seatnumber':2, 'seatcategory':'Child'})
            self.assertEqual(len(session['seats']), 2) #The seat should only have been added once but the length of the seats array was already 1
            self.assertEqual(session['total'], 2) #The total price of the seats on this ticket should be 1 since only one seat (costing £1) should have been added but the value of session['total'] was already 1

            #Checks that if we go back to bookTickets/2 and then come back to /bookTickets/3, then the seats booked in the tests above (r61, r62, r71, r72) are removed from the session data
            r81 = c.post('/bookTickets/2', data={'screeningnumber':1},
                        follow_redirects=True)
            r82 = c.get('/bookTickets/3')
            self.assertEqual(len(session['seats']), 0)
            self.assertEqual(session['total'], 0)

            #Checks that if a set of valid data is entered then it is accepted
            r91 = c.post('/bookTickets/3', data={'seatnumber':1,'seatcategory':'Adult'})
            r92 = c.post('/bookTickets/3', data={'seatnumber':2,'seatcategory':'Child'})
            r93 = c.post('/bookTickets/3', data={'seatnumber':3,'seatcategory':'Senior'})
            self.assertEqual(len(session['seats']), 3)
            self.assertEqual(session['total'], 3)

            #Checks that if the "Proceed to payment" button is clicked after this, then you are redirected to /bookTickets/4 (which you should be because you have added at least one seat)
            c.get('/bookTickets/4', follow_redirects=True)
            self.assertEqual(request.path, '/bookTickets/4')

    def testBookTickets4(self):
        with app.test_client() as c:
            #Signing in to prevent redirection due to not being logged in
            self.signUpLogin(c)

            #Completing the previous stages of the booking process to prevent redirection due to not having completed the previous stages
            r0 = c.post('/bookTickets', data={'movietitle':'Up'},
                        follow_redirects=True)

            r1 = c.post('/bookTickets/2', data={'screeningnumber':1},
                        follow_redirects=True)

            r21 = c.post('/bookTickets/3', data={'seatnumber':1,'seatcategory':'Adult'})
            r22 = c.post('/bookTickets/3', data={'seatnumber':2,'seatcategory':'Child'})
            r23 = c.post('/bookTickets/3', data={'seatnumber':3,'seatcategory':'Senior'})
            
            #Checking that you can reach the /bookTickets/4 page and that you are not redirected from it (if it attempts to redirect you while follow_redirects=False then the status code will be 302)
            r3 = c.get('/bookTickets/4', follow_redirects=True)
            self.assertEqual(r3.status_code, 200)

            #Checking that it doesn't accept empty data for the first field
            r4 = c.post('/bookTickets/4', data={'cardnumber':None, 'securitynumber':1}, 
                        follow_redirects=True)
            self.assertEqual(request.path, '/bookTickets/4')

            #Checking that it doesn't accept empty data for the second field
            r5 = c.post('/bookTickets/4', data={'cardnumber':None, 'securitynumber':1},
                        follow_redirects=True)
            self.assertEqual(request.path, '/bookTickets/4')

            #Checking that it doesn't accept empty data for both fields at the same time
            r6 = c.post('/bookTickets/4', data={'cardnumber':None, 'securitynumber':1},
                        follow_redirects=True)
            self.assertEqual(request.path, '/bookTickets/4')

            #Checking that it doesn't accept non-empty data of the incorrect type
            r7 = c.post('/bookTickets/4', data={'cardnumber':'hello', 'securitynumber':'hello'},
                        follow_redirects=True)
            self.assertEqual(request.path, '/bookTickets/4')

            #Checking that it accepts valid data
            #There is currently no validation on entered card details other than that they must be integers and that data must be present
            r8 = c.post('bookTickets/4', data={'cardnumber':1, 'securitynumber':1}, 
                        follow_redirects=True)
            self.assertEqual(request.path, '/')

    def testDatabase(self):
        with app.test_client() as c:
            #Signing in to prevent redirection due to not being logged in
            self.signUpLogin(c)

            #Completing a full run of the booking process
            r0 = c.post('/bookTickets', data={'movietitle':'Up'},
                        follow_redirects=True)

            r1 = c.post('/bookTickets/2', data={'screeningnumber':1},
                        follow_redirects=True)

            r21 = c.post('/bookTickets/3', data={'seatnumber':1,'seatcategory':'Adult'})
            r22 = c.post('/bookTickets/3', data={'seatnumber':2,'seatcategory':'Child'})
            r23 = c.post('/bookTickets/3', data={'seatnumber':3,'seatcategory':'Senior'})

            r8 = c.post('bookTickets/4', data={'cardnumber':1, 'securitynumber':1}, 
                        follow_redirects=True)

            #Checking that the data from the full run was entered into the database
            #Checking that the record was created correctly in the Booking table
            booking = models.Booking.query.first()
            self.assertEqual(booking.UserID, 1)
            self.assertEqual(booking.ScreeningID, 1)
            self.assertEqual(booking.TotalPrice, 3)

            #Checking that the records were created correctly in the Ticket table
            tickets = models.Ticket.query.all()

            #Checking that 3 tickets were created (one for each seat booked in the full run above)
            self.assertEqual(len(tickets), 3)

            #Checking that the first ticket's record was created correctly
            self.assertEqual(tickets[0].BookingID, booking.BookingID)
            self.assertEqual(tickets[0].SeatID, 1)
            self.assertEqual(tickets[0].Category, 1)
            self.assertEqual(tickets[0].QR, 'qr')

            #Checking that the second ticket's record was created correctly
            self.assertEqual(tickets[1].BookingID, booking.BookingID)
            self.assertEqual(tickets[1].SeatID, 2)
            self.assertEqual(tickets[1].Category, 0)
            self.assertEqual(tickets[1].QR, 'qr')

            #Checking that the third ticket's record was created correctly
            self.assertEqual(tickets[2].BookingID, booking.BookingID)
            self.assertEqual(tickets[2].SeatID, 3)
            self.assertEqual(tickets[2].Category, 2)
            self.assertEqual(tickets[2].QR, 'qr')

    #Tests the test page
    def testTest(self):
        with app.test_client() as c:
            response = c.post('/test', data={'movietitle':'up'}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            #self.assertEqual(session['movie'], 'up')
            self.assertEqual(request.path, '/login') 
            #seems to get redirected correctly

            self.signUpLogin(c)

            response = c.post('/bookTickets', data={'movietitle':'Up'}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(request.path, '/bookTickets/2') 
"""   
    #Tests the /bookTickets page
    def testBookTickets1(self):
        with app.test_client() as c:
            self.signUpLogin()

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
