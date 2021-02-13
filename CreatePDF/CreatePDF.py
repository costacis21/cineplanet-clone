from reportlab.pdfgen.canvas import Canvas

canvas = Canvas("test.pdf")
canvas.drawString(72, 72, "Hello, World")
canvas.save()