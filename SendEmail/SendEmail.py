import sys
import smtplib, ssl

def main(reciever_email):
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = "leeds.cinemaplanet@gmail.com"
    sender_password = input("Enter your password and press enter: ")

    context = ssl.create_default_context()

    try:
        server = smtplib.SMTP(smtp_server,port)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender_email, sender_password)
    except Exception as e:
        print(e)
    finally:
        server.quit()

if __name__ == "__main__":
    main(sys.argv[1])