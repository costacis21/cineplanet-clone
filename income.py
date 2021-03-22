import matplotlib.pyplot as plt
from datetime import timedelta
import datetime

from app import app,models

def createWeeklyGraph():
    starts=[]
    ends=[]
    final =datetime.date.today()
    start = datetime.date(datetime.date.today().year, 1, 1)
    # create arrays with dates for each week up until today 
    while((final>start )):
        end = start + datetime.timedelta(days=6)
        ends.append(end)
        starts.append(start)
        start = end

    incomes = []
    weeks=[]
    movies = models.Movie.query.all()
    totalTotal =0

    # for each week generated in the arrays above, query incomes and append it to list
    for i in range(len(ends)):
        totalTotal=0
        for movie in movies:
            totalPrice=0
            ticketCount=0
            screenings = models.Screening.query.filter_by(MovieID = movie.MovieID).all()

            for screening in screenings:
                if (screening.StartTimestamp.date() >= starts[i]) and (screening.StartTimestamp.date() <=ends[i]):
                    bookings = models.Booking.query.filter_by(ScreeningID=screening.ScreeningID).all()
                    for booking in bookings:
                        totalPrice+=booking.TotalPrice
                else:
                    continue
            totalTotal+=totalPrice
            if totalPrice==0:
                continue
            
        incomes.append(totalTotal)
        
   
    # parse date with only month and day
    for start in starts:
        weeks.append(str(start.day) + "-" + str(start.month))

    plt.plot(weeks,incomes)

    # naming the y-axis
    plt.ylabel('Income (£)')
    # naming the x-axis
    plt.xlabel('Week commencing at')
    # plot title
    plt.title('Weekly incomes of {year}'.format(year =datetime.date.today().year ))

    filename = 'app/static/graphs/currWeeklyGraph.png'
    plt.savefig(filename)


def getWeeklyIncomes():
    today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday())
    end = start + datetime.timedelta(days=6)
    incomes = [{}]
    movies = models.Movie.query.all()
    totalTotal =0
    week = "{start}-{end}".format(start = start, end = end)
    for movie in movies:
        totalPrice=0
        ticketCount=0
        screenings = models.Screening.query.filter_by(MovieID = movie.MovieID).all()

        for screening in screenings:
            if (screening.StartTimestamp.date() >= start) and (screening.StartTimestamp.date() <=end):
                bookings = models.Booking.query.filter_by(ScreeningID=screening.ScreeningID).all()
                for booking in bookings:
                    tickets = models.Ticket.query.filter_by(BookingID=booking.BookingID).all()
                    ticketCount +=len(tickets)
                    totalPrice+=booking.TotalPrice
            else:
                continue
        if totalPrice==0:
            continue
        incomes.append({'name': movie.Name, 'ticketsSold':ticketCount, 'total':round(totalPrice, 2)})
        totalTotal+=totalPrice
    totalTotal=round(totalTotal, 2)
    return incomes,totalTotal,week