import sys
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

smtp_server = "smtp.gmail.com"
port = 587
sender_email = "leeds.cinemaplanet@gmail.com"

def SendMail(receiver_email, filename):
    """
    Sends an email from the cinema's email address to the given receiver email
    
    Inputs:     receiver_email - Email address of whoever the email is being sent to
                filename       - Name of the pdf file containing the ticket to be sent to the receiver
    Outputs:    None           - Sends an email to the given address
    """

    # Get sender password
    sender_password = input("Enter your password: ")

    # Create a secure ssl context
    context = ssl.create_default_context()

    # In try/catch loop to prevent crashing if it fails
    try:
        # Connect to the mail server and login
        server = smtplib.SMTP(smtp_server,port)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender_email, sender_password)
    except Exception as e:
        print(e)

    # Set up the message object
    # "alternative" used here to ensure that if the receiver has disabled html emails then they will still receive it as plain text
    message = MIMEMultipart("alternative")
    message["Subject"] = "Test Subject"
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Bcc"] = receiver_email

    # Create the plain text portion of message
    # Will probably be the same for all messages sent (which is why this is hardcoded for now)
    text = """\
    Test Message"""

    # Create's the html portion of the message 
    html = """\
    <html>
    <body>
        <p>
            Test Paragraph
        </p>
    </body>
    </html>
    """

    # Converts the text and html parts of the message into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Adds the html and text parts to the MIMEMultipart message
    # Email client renders the last part that was added first, so part2 (the html) is attached last
    message.attach(part1)
    message.attach(part2)

    # Opens the PDF file containing the ticket in binary mode
    with open(filename, "rb") as attachment:
        # Adds the file as an application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode the file in ASCII characters to send by email    
    encoders.encode_base64(part)

    # Adds header as key/value pair to attachment part
    part.add_header("Content-Disposition",f"attachment; filename= {filename}",)

    # Adds the attachment to the message object and converts the message into a string
    message.attach(part)
    text = message.as_string()

    text = message.as_string()

    try:
        #Sends the email
        server.sendmail(sender_email, receiver_email, message.as_string())
    except Exception as e:
        print(e)

    #Ending the connection to the server
    server.quit()

if __name__ == "__main__":
    pass
    #main(sys.argv[1], sys.argv[2])