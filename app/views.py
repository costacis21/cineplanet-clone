from flask import flash, render_template, redirect, url_for, session
from flask_login import current_user, login_user, logout_user
from app import app,models,forms,db,admin
from datetime import datetime
from passlib.hash import sha256_crypt
import logging



@app.route('/', methods=['GET','POST'])
def index():

    return render_template('index.html',
                           title='Homepage'
                           )

@app.route('/login', methods=['GET','POST'])
def login():
    if not('key_userID' in session):
        signinForm = forms.Login()

        if signinForm.validate_on_submit():
            qry=[]
            if(len(qry)!=1):
                now = datetime.now()

                timestamp = datetime.timestamp(now)
                logging.warning(str(timestamp) + ":: Failed login attempt with email " + signinForm.email.data)

                flash("User not found. Please check your email and password")
            else:
                session['key_userID'] = qry[0].id
                session['key_name'] = qry[0].name

                now = datetime.now()

                timestamp = datetime.timestamp(now)
                logging.warning(str(timestamp) + ":: User logged in with email " + qry[0].email)

                return redirect(url_for('index'))



        return render_template('login.html',
                            title='Login',
                            signinForm=signinForm
                            )
    else:
        return redirect(url_for('index'))


    return render_template('index.html')

@app.route('/signup', methods=['GET','POST'])
def signup():

    signupForm = forms.Signup()


    if signupForm.validate_on_submit():

        now = datetime.now()

        timestamp = datetime.timestamp(now)
        logging.info(str(timestamp) + ":: New user added with email " + signupForm.email.data)

        flash("Excelent! Now you can login with your new account")
        return redirect(url_for('login'))

    return render_template('signup.html',
                           title='Signup',
                           signupForm=signupForm
                           )





@app.route('/logout')
def logout():

    now = datetime.now()

    timestamp = datetime.timestamp(now)
    logging.info(str(timestamp) + ":: user with userID " + str(session['key_userID']) + " logged out")

    session.pop('key_userID',None)
    session.pop('key_name',None)
    return render_template('logout.html',
                           title='Loging out',
                           )







@app.route('/addMovieScreening')
def addMovieScreening():
    addScreeningForm = forms.addMovieScreening()
    return render_template('add-movie-screening.html',
                           title='Add Movie Screening',
                           addScreeningForm = addScreeningForm
                           )
