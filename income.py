import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from datetime import timedelta
import datetime

from app import app,models

def createWeeklyGraph():
    """
    
    saves weekly income graph from begining of year until today. png file of graph is at app/static/graphs/currWeeklyGraph.png 
    
    
    """





    starts=[]
    ends=[]
    final =datetime.date.today()
    start = datetime.date(datetime.date.today().year, 1, 1)
    # create arrays with dates for each week up until today 
    while((final>start )):
        end = start + datetime.timedelta(days=7)
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

    plt.plot(weeks,incomes, color = 'red')

    # naming the y-axis
    plt.ylabel('Income (£)')
    # naming the x-axis
    plt.xlabel('Week commencing at')
    # plot title
    plt.title('Weekly incomes of {year}'.format(year =datetime.date.today().year ))

    filename = 'app/static/graphs/currWeeklyGraph.png'
    plt.tight_layout()

    plt.savefig(filename)
    plt.close()


def getWeeklyIncomes():

    """
        returns list where: 
            [0] contains list of dictionaries with:
                'name' for movie title, 'ticketsSold' for number of tickets sold and 'total' for total income of movie'

            [1] contains total income of all movies combined

            [2] contains week in the format of "{start}-{end}"
        

    """


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


def compareMovies(start: datetime.date, end: datetime.date):
    """

        arguments= 
            start : date object for start of interval
            end : date object for end of interval

        saves png file of bar chart under app/static/graphs/{week}.png where week = start-end


        returns list of dictionaries with 'name' as movie title and 'ticketsSold' number of tickets sold within given dates



    """



    movies = models.Movie.query.all()
    ticketsSold = []

    ticketsSoldPerMovie=[]
    movieNames=[]

    week = str(start)+'-'+str(end)
    for movie in movies:
        ticketCount=0
        totalPrice=0
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
        ticketsSoldPerMovie.append(ticketCount)
        movieNames.append(movie.Name)
        ticketsSold.append({'name': movie.Name, 'ticketsSold':ticketCount})



    movieNamesPos = [i for i, _ in enumerate(movieNames)]

    plt.barh(movieNamesPos, ticketsSoldPerMovie, color = 'red')


    # naming the y-axis
    plt.xlabel('Tickets sold')
    # naming the x-axis
    plt.ylabel('Movie Title')
    # plot title
    plt.title('Weekly incomes of {week}'.format(week = week))

    plt.yticks(movieNamesPos,movieNames)
    filename = 'app/static/graphs/{week}.png'.format(week = week)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return ticketsSold

    