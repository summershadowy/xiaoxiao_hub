import requests
import xml.etree.ElementTree as ET
import csv
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def translate_text(text, source_lang='en', target_lang='zh'):
    libretranslate_api_url = "https://libretranslate.de/translate"
    params = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
        "format": "text"
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
    response = requests.post(libretranslate_api_url, data=params, headers=headers)
    return response.json()['translatedText']

# Fetch papers from arXiv
yesterday = datetime.now() - timedelta(1)
yesterday_date = yesterday.strftime('%Y-%m-%d')

api_endpoint = 'http://export.arxiv.org/api/query?'
query = f'search_query=all:LLM+AND+all:medical&start=0&max_results=50&sortBy=submittedDate&sortOrder=descending'
response = requests.get(api_endpoint + query)

papers = []  # Initialize the list to store paper details
if response.status_code == 200:
    root = ET.fromstring(response.text)
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
        abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
        published = entry.find('{http://www.w3.org/2005/Atom}published').text.strip()
        link = entry.find('{http://www.w3.org/2005/Atom}id').text.strip()
        published_date = datetime.strptime(published, '%Y-%m-%dT%H:%M:%SZ').date()

        # Check if the published date is yesterday
        if published_date.strftime('%Y-%m-%d') == yesterday_date:
            try:
                translated_abstract = translate_text(abstract)
            except Exception as e:
                print(f"Failed to translate abstract for '{title}': {e}")
                translated_abstract = "翻译失败"

            papers.append([title, abstract, translated_abstract, published_date.strftime('%Y-%m-%d'), link])

# The rest of the script remains the same...

# Save the papers to a CSV file named with yesterday's date
csv_file_path = f'arxiv_papers_{yesterday_date}.csv'
with open(csv_file_path, 'w', newline='', encoding='utf-8-sig') as file:
    writer = csv.writer(file)
    writer.writerow(['Title', 'Abstract', 'Translated Abstract', 'Date', 'Link'])
    writer.writerows(papers)

# Email settings
gmail_smtp_server = "smtp.gmail.com"
gmail_user = os.environ.get("MY_GMAIL")
gmail_password = os.environ.get("GMAIL_PASSWORD") # 应用专用密码，不是Gmail登录密码
receiver_email = os.environ.get("MY_OUTLOOK")  # replace with your Outlook email address

# Send email with CSV attachment
def send_email_with_attachment(sender, password, receiver, subject, body, attachment_path):
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = receiver
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    with open(attachment_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename={attachment_path}")
        message.attach(part)

    server = smtplib.SMTP(gmail_smtp_server, gmail_smtp_port)
    server.starttls()
    server.login(sender, password)
    server.send_message(message)
    server.quit()

# Call the send email function
try:
    send_email_with_attachment(
        gmail_user,
        gmail_password,
        receiver_email,
        f"ArXiv Papers List {yesterday_date}",
        f"Please find attached the list of papers from ArXiv for the date {yesterday_date}.",
        csv_file_path
    )
    print('Email sent successfully')
except Exception as e:
    print('Email sending failed:', e)
