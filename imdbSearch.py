import requests

from app import app,models,forms,db,admin


# API key = bd3bccc81b8b90568f58a7d8d3299477
# account on my name and email

def getMovieInfo(movieTitle: str):
    """

    return list of dictionaries containing imdb url with keys= {Title, Rating, Description, PosterURL, InfoURL, Age_Rating, Duration, ID, TrailerLink}


    return None if error




    """


    apiKey="bd3bccc81b8b90568f58a7d8d3299477"




    # create url with formated movie title and create request
    titleFormated = movieTitle.replace(" ","+")
    TMDBurl = "https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={title_formated}".format(api_key=apiKey,title_formated=titleFormated)
    TMDBresponse = requests.get(TMDBurl)
    TMDBjson_response = TMDBresponse.json()


    returnDictionary=[]

    # check for errors in the request and continue with the first movie from the search
    if TMDBresponse.status_code == 200:
        if not TMDBjson_response['total_results']>0:
            return None
        else:
            # organize data from response
            for movie in TMDBjson_response['results']:
                movieTitle = movie['original_title']
                movieRating = movie['vote_average']
                moviePosterURL = "https://image.tmdb.org/t/p/w500{posterUrl}".format(posterUrl = movie['poster_path'])
                tmdbID=movie['id']
                movieDescription = movie['overview'] + "\n" + getMovieCrew(tmdbID)
                movieTMDB_URL = "https://www.themoviedb.org/movie/{movie_id}".format(movie_id=tmdbID)


                # get age rating
                age_ratingURL = "https://api.themoviedb.org/3/movie/{movie_id}/release_dates?api_key={api_key}".format(movie_id = tmdbID, api_key=apiKey)
                age_ratingResponse = requests.get(age_ratingURL)
                age_ratingJsonResponse = age_ratingResponse.json()
                age_rating = "Not Available"



                # search for US data since it is the most likely to have this info available, many other regions in the response I looked at are empty
                for country in age_ratingJsonResponse['results']:
                    if country["iso_3166_1"] == "US":
                        if country["release_dates"][0]["certification"] != '':
                            age_rating = country["release_dates"][0]["certification"]

                


                # get duration
                durationURL = "https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}".format(movie_id = tmdbID, api_key=apiKey)
                durationResponse = requests.get(durationURL)
                durationJsonResponse = durationResponse.json()
                movieDuration = durationJsonResponse['runtime']
                





                 # get trailer link
                trailerLink = getTrailerFromID(tmdbID)
                returnDictionary.append({"Title": movieTitle, "Rating": movieRating, "Description": movieDescription, "PosterURL": moviePosterURL, "InfoURL": movieTMDB_URL, "Age_Rating": age_rating, "Duration": movieDuration, "ID":tmdbID, "TrailerURL":trailerLink})


            

            return returnDictionary


    elif TMDBresponse.status_code == 404:
        print('TMDB page not Found.')
        return None
    
    
    
    return None



def getUpcomingMovies():

    apiKey="bd3bccc81b8b90568f58a7d8d3299477"
    TMDBurl = "https://api.themoviedb.org/3/movie/upcoming?api_key={api_key}&language=en-US&page=1".format(api_key=apiKey)

    TMDBresponse = requests.get(TMDBurl)
    TMDBjson_response = TMDBresponse.json()

    returnDictionary = []


    # check for errors in the request and continue with the first movie from the search
    if TMDBresponse.status_code == 200:
        if not TMDBjson_response['total_results']>0:
            return None
        else:
            for movie in TMDBjson_response['results']:
                movieTitle = movie['original_title']
                movieRating = movie['vote_average']
                moviePosterURL = "https://image.tmdb.org/t/p/w500{posterUrl}".format(posterUrl = movie['poster_path'])
                tmdbID=movie['id']
                movieDescription = movie['overview'] + "\n" + getMovieCrew(tmdbID)

                movieTMDB_URL = "https://www.themoviedb.org/movie/{movie_id}".format(movie_id=tmdbID)


                # get age rating
                age_ratingURL = "https://api.themoviedb.org/3/movie/{movie_id}/release_dates?api_key={api_key}".format(movie_id = tmdbID, api_key=apiKey)
                age_ratingResponse = requests.get(age_ratingURL)
                age_ratingJsonResponse = age_ratingResponse.json()
                age_rating = "Not Available"



                # search for US data since it is the most likely to have this info available, many other regions in the response I looked at are empty
                for country in age_ratingJsonResponse['results']:
                    if country["iso_3166_1"] == "US":
                        if country["release_dates"][0]["certification"] != '':
                            age_rating = country["release_dates"][0]["certification"]

                


                # get duration
                durationURL = "https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}".format(movie_id = tmdbID, api_key=apiKey)
                durationResponse = requests.get(durationURL)
                durationJsonResponse = durationResponse.json()
                movieDuration = durationJsonResponse['runtime']
            
                # get trailer link
                trailerLink = getTrailerFromID(tmdbID)
                returnDictionary.append({"Title": movieTitle, "Rating": movieRating, "Description": movieDescription, "PosterURL": moviePosterURL, "InfoURL": movieTMDB_URL, "Age_Rating": age_rating, "Duration": movieDuration, "ID":tmdbID, "TrailerURL":trailerLink})




    elif TMDBresponse.status_code == 404:
        print('TMDB page not Found.')
        return None

    return returnDictionary



def getMovieInfoFromID(tmdbID:str):
    apiKey="bd3bccc81b8b90568f58a7d8d3299477"

    TMDBurl = "https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US".format(movie_id = tmdbID, api_key = apiKey)


    TMDBresponse = requests.get(TMDBurl)
    TMDBjson_response = TMDBresponse.json()


    returnDictionary=[]

    # check for errors in the request and continue with the first movie from the search
    if TMDBresponse.status_code == 200:
        
        # organize data from response
        movie = TMDBjson_response
        movieTitle = movie['original_title']
        movieRating = movie['vote_average']
        moviePosterURL = "https://image.tmdb.org/t/p/w500{posterUrl}".format(posterUrl = movie['poster_path'])
        tmdbID=movie['id']
        movieDescription = movie['overview'] + "\n" + getMovieCrew(tmdbID)
        movieTMDB_URL = "https://www.themoviedb.org/movie/{movie_id}".format(movie_id=tmdbID)


        # get age rating
        age_ratingURL = "https://api.themoviedb.org/3/movie/{movie_id}/release_dates?api_key={api_key}".format(movie_id = tmdbID, api_key=apiKey)
        age_ratingResponse = requests.get(age_ratingURL)
        age_ratingJsonResponse = age_ratingResponse.json()
        age_rating = "Not Available"



        # search for US data since it is the most likely to have this info available, many other regions in the response I looked at are empty
        for country in age_ratingJsonResponse['results']:
            if country["iso_3166_1"] == "US":
                if country["release_dates"][0]["certification"] != '':
                    age_rating = country["release_dates"][0]["certification"]

        


        # get duration
        durationURL = "https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}".format(movie_id = tmdbID, api_key=apiKey)
        durationResponse = requests.get(durationURL)
        durationJsonResponse = durationResponse.json()
        movieDuration = durationJsonResponse['runtime']
        





    

        # get trailer link
        trailerLink = getTrailerFromID(tmdbID)
        returnDictionary={"Title": movieTitle, "Rating": movieRating, "Description": movieDescription, "PosterURL": moviePosterURL, "InfoURL": movieTMDB_URL, "Age_Rating": age_rating, "Duration": movieDuration, "ID":tmdbID, "TrailerURL":trailerLink}
        
    

        return returnDictionary


def getTrailerFromID(tmdbID:str):
    """
    param: tmdbID

    return URL of trailer, if not available return none
    
    """
    apiKey="bd3bccc81b8b90568f58a7d8d3299477"

    TMDBurl = "https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}&language=en-US".format(movie_id = tmdbID, api_key = apiKey)


    TMDBresponse = requests.get(TMDBurl)
    TMDBjson_response = TMDBresponse.json()

    if( tmdbID == None):
        return None

    if TMDBresponse.status_code == 200:

        for result in TMDBjson_response["results"]:
            if(result["type"]=="Trailer" and result["site"]=="YouTube"):
                return "https://www.youtube.com/watch?v={youtubeID}".format(youtubeID=result["key"])

    
    return None




def getMovieCrew(tmdbID:str):
    """
    param: tmdbID

    return String containing the main 5 actors + director, if not available return none
    
    """
    apiKey="bd3bccc81b8b90568f58a7d8d3299477"

    TMDBurl = "https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={api_key}&language=en-US".format(movie_id = tmdbID, api_key = apiKey)


    TMDBresponse = requests.get(TMDBurl)
    TMDBjson_response = TMDBresponse.json()

    returnStr="Actors: "

    if( tmdbID == None):
        return None

    if TMDBresponse.status_code == 200:

        for i in range(5):
            returnStr+= TMDBjson_response["cast"][i]["name"]
            if i < 4:
                returnStr+= ", "

        returnStr+= "\nDirector: "
        for p in TMDBjson_response["crew"]:
            if p["job"]=="Director":
                returnStr+= p["name"]
                return returnStr
    
    return None    



