from app import db, login
import datetime

@login.user_loader
def user_loader(UserID):
    return User.query.get(UserID)

class User(db.Model):
    UserID = db.Column(db.Integer, primary_key=True)
    Authenticated = db.Column(db.Boolean, default=False)
    Password = db.Column(db.String(20))
    Email = db.Column(db.String(50))
    # 0 for admin, 1 for staff and 2 for normal user
    Privilage = db.Column(db.Integer)
    Bookings = db.relationship('Booking', backref='user', lazy='dynamic')

    def is_active(self):
        return True

    def get_id(self):
        return self.UserID

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

class Screening(db.Model):
    ScreeningID = db.Column(db.Integer, primary_key=True)
    MovieID = db.Column(db.Integer, db.ForeignKey('movie.MovieID'))
    ScreenID = db.Column(db.Integer, db.ForeignKey('screen.ScreenID'))
    StartTimestamp = db.Column(db.DateTime)
    EndTimestamp = db.Column(db.DateTime)
    Bookings = db.relationship('Booking', backref='screening', lazy='dynamic')

    def reserved(self):
        reserved = []
        for booking in self.Bookings:  #find all booked seats
            for ticket in booking.Tickets:
                seat = Seat.query.get(ticket.SeatID)
                reserved.append(seat.code)
        return reserved
    
    def seats(self):
        seats = []
        room = Screen.query.get(self.ScreenID)
        for seat in room.Seats:
            seats.append(seat.code)
        return seats

    def title(self):
        movie = Movie.query.get(self.MovieID)
        return movie.Name

class Booking(db.Model):
    BookingID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey('user.UserID'))
    ScreeningID = db.Column(db.Integer, db.ForeignKey('screening.ScreeningID'))
    Timestamp = db.Column(db.DateTime)
    TotalPrice = db.Column(db.Float)
    Tickets = db.relationship('Ticket', backref='booking', lazy='dynamic')

class Ticket(db.Model):
    TicketID = db.Column(db.Integer, primary_key=True)
    BookingID = db.Column(db.Integer, db.ForeignKey('booking.BookingID'))
    SeatID = db.Column(db.Integer, db.ForeignKey('seat.SeatID'))
    # 1 for adult, 2 for child, 3 for senior 
    Category = db.Column(db.Integer)
    QR = db.Column(db.String(4296))
    

class Screen(db.Model):
    ScreenID = db.Column(db.Integer, primary_key=True)
    SeatQuantity = db.Column(db.Integer)
    Seats = db.relationship('Seat', backref='screen', lazy='dynamic')
    Screenings = db.relationship('Screening', backref='screen', lazy='dynamic')

class Seat(db.Model):
    SeatID = db.Column(db.Integer, primary_key=True)
    ScreenID = db.Column(db.Integer, db.ForeignKey('screen.ScreenID'))
    code = db.Column(db.String(5))
    # 0 for standard, 1 for VIP 
    Type = db.Column(db.Integer)
    Tickets = db.relationship('Ticket', backref='seat', lazy='dynamic')

    # Just added - necessary to take into account adverts/trailers

    # POTENTIAL METHOD ......

    # def is_sold_out(self):
    #   return True if 200 seats are sold
    #   otherwise return False

class Movie(db.Model):
    MovieID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50))
    Age = db.Column(db.Integer)
    Description = db.Column(db.String(500))
    # Added this for extra detail
    RunningTime = db.Column(db.Integer)
    PosterURL = db.Column(db.String(100))
    Screenings = db.relationship('Screening', backref='movie', lazy='dynamic')

    def getScreenings(self, date):
        allScreenings = Screening.query.filter_by(MovieID=self.MovieID).all()
        datedScreenings = []
        for screening in allScreenings:
            if str(date) in str(screening.StartTimestamp):
                datedScreenings.append(screening)
        return datedScreenings
