import requests



# API key = bd3bccc81b8b90568f58a7d8d3299477
# account on my name and email

def getMovieInfo(movieTitle: str):
    """

    return dictionary containing imdb url with keys= {Title, Rating, Description, PosterURL, InfoURL}


    return None if error




    """


    apiKey="bd3bccc81b8b90568f58a7d8d3299477"


    # create url with formated movie title and create request
    titleFormated = movieTitle.replace(" ","+")
    url = "https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={title_formated}".format(api_key=apiKey,title_formated=titleFormated)
    response = requests.get(url)
    json_response = response.json()


    # check for errors in the request and continue with the first movie from the search
    if response.status_code == 200:
        if not json_response['total_results']>0:
            return None
        else:
            # organize data from response
            movie = json_response['results'][0]
            movieTitle = movie['original_title']
            movieRating = movie['vote_average']
            movieDescription = movie['overview']
            moviePosterURL = "https://image.tmdb.org/t/p/w500{posterUrl}".format(posterUrl = movie['poster_path'])
            movieTMDB_URL = "https://www.themoviedb.org/movie/{movie_id}".format(movie_id=movie['id'])


            # store it to dictionary
            returnDictionary = {"Title": movieTitle, "Rating": movieRating, "Description": movieDescription, "PosterURL": moviePosterURL, "InfoURL": movieTMDB_URL}

            

            print(returnDictionary)
            return returnDictionary


    elif response.status_code == 404:
        print('TMDB page not Found.')
        return None
    
    
    
    return None
    



