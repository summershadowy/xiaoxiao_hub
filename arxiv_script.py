import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email(file_path, receiver_email):
    sender_email = "your_email@example.com"  # Replace with your email
    sender_password = "your_password"        # Replace with your email password

    # Create a multipart message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = "ArXiv Papers List"

    # Body
    body = "Please find attached the list of yesterday's papers from ArXiv."
    message.attach(MIMEText(body, 'plain'))

    # Attachment
    filename = file_path.split('/')[-1]
    attachment = open(file_path, "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= {filename}")
    message.attach(part)

    # SMTP session
    server = smtplib.SMTP('smtp.example.com', 587)  # Replace with your SMTP server and port 
    server.starttls()
    server.login(sender_email, sender_password)
    text = message.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()
