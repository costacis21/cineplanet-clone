import sys
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import *
from reportlab.lib.colors import *

def main(Filename, MovieName, Seat, Category, Screen, Date, Time):
    """
    Generates a PDF ticket with the information given in the arguments

    Inputs: Filename  - Name of the PDF file to be generated
            MovieName - Name of the movie that the ticket is for
            Seat      - The seat corresponding to the ticket
            Category  - The category of the ticket (child / adult / senior)
            Screen    - The screen that the movie is being shown on
            Date      - The date of the screening
            Time      - The time of the screening

    Ouputs: PDF ticket containing the information from the inputs, saved in the same folder as the python file
    """
    
    #Creating the Cavnas object to allow the PDF to be written on
    canvas = Canvas(Filename+".pdf", pagesize="A4")
    
    #Adding images to the ticket
    canvas.drawImage("test_logo.jpg", 0, 560, width=200, height=250)
    canvas.drawImage("test_qr.png", 400, 580)

    #Adding the text to the PDF
    canvas.drawString(10,580, "Movie Name: "+ MovieName)
    canvas.line(10, 575, 700, 575)
    canvas.drawString(10, 560, "Seat: "+ Seat)
    canvas.drawString(200, 560, "Category: "+ Category)
    canvas.drawString(10, 540, "Screen: "+ Screen)
    canvas.drawString(450, 560, "Date: "+ Date)
    canvas.drawString(450, 540, "Time: "+ Time)
    
    #Saving the PDF
    canvas.save()

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])