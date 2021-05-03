import sys, os
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import *
from reportlab.lib.colors import *

def MakePDF(Filename, QRs, MovieName, Seats, Categories, Screen, Date, Time, Types):
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
    
    # Creating the Cavnas object to allow the PDF to be written on
    canvas = Canvas(Filename, pagesize="A4")
    
    # A4 = (8.26772 inches, 11.6929 inches)
    # units given in 72ths of an inch
    content_height = 400
    page_height = 842

    for i in range(0,len(QRs)):
        qr=QRs[i]
        Seat=Seats[i]
        Category=Categories[i]
        Type = Types[i]

        y = (i % 3)

        # Adding images to the ticket
        canvas.drawImage(os.getcwd()+'/app/static/ticket/accessories/test_logo.jpg', 0, (3-y)*(842/3)- 250, width=200, height=200, preserveAspectRatio=True)
        canvas.drawImage(qr, 420, (3-y)*(842/3)- 220, width=170, height=170, preserveAspectRatio=True)

        # Adding the text to the PDF
        a=(3-y)*(842/3) - 220
        canvas.drawString(10, a, "Movie Name: "+ MovieName)
        canvas.line(10, a-5, 700,a-5)
        canvas.drawString(10, a-20, "Seat: "+ Seat)
        canvas.drawString(200, a-20, "Seat Type: "+ Type)
        canvas.drawString(200, a-40, "Seat Category: "+ Category)
        canvas.drawString(10, a-40, "Screen: "+ Screen)
        canvas.drawString(450, a-20, "Date: "+ Date)
        canvas.drawString(450, a-40, "Time: "+ Time)

        if (i+1) % 3 == 0:
            canvas.showPage()
            y=1
    
    # Saving the PDF
    canvas.save()

if __name__ == "__main__":
    pass