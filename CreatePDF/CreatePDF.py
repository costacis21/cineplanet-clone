from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import *
from reportlab.lib.colors import *

#canvas = Canvas("test.pdf", pagesize=(612.0, 792.0))
#canvas = Canvas("test.pdf", pagesize=(8.5*inch, 11*inch))
canvas = Canvas("test2.pdf", pagesize="A12")
canvas.drawString(250, 250, "Hello, World")
canvas.drawImage("test_image.jpg",100,400)
canvas.line(10,10,200,10)
canvas.save()