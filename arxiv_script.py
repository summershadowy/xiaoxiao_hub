import requests
import xml.etree.ElementTree as ET
import csv
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def fetch_arxiv_papers(yesterday_date):
    api_endpoint = 'http://export.arxiv.org/api/query?'
    query = f'search_query=all:LLM+AND+all:medical&start=0&max_results=50&sortBy=submittedDate&sortOrder=descending'
    response = requests.get(api_endpoint + query)

    if response.status_code == 200:
        root = ET.fromstring(response.text)
        papers = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
            abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip() 
            published = entry.find('{http://www.w3.org/2005/Atom}published').text.strip()
            link = entry.find('{http://www.w3.org/2005/Atom}id').text.strip()
            published_date = datetime.strptime(published, '%Y-%m-%dT%H:%M:%SZ').date()
            if published_date.strftime('%Y-%m-%d') == yesterday_date:
                papers.append([title, abstract, published_date.strftime('%Y-%m-%d'), link])
        return papers
    else:
        raise Exception("Failed to retrieve data from arXiv API.")

def send_email_with_attachment(gmail_user, gmail_password, receiver_email, subject, body, attachment_path):
    message = MIMEMultipart()
    message['From'] = gmail_user
    message['To'] = receiver_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    with open(attachment_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename={attachment_path}")
        message.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(gmail_user, gmail_password)
    server.send_message(message)
    server.quit()

# Main process
yesterday_date = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
papers = fetch_arxiv_papers(yesterday_date)

# Define CSV file path
csv_file_path = f'arxiv_papers_{yesterday_date}.csv'

# Save papers to CSV
with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Title', 'Abstract', 'Date', 'Link'])
    writer.writerows(papers)

# Email details
gmail_user = "xiaoxiao.han1994@gmail.com"
gmail_password = "tzdc fxhw jxcq odht"
receiver_email = "xiaoxiao.han@outlook.com"
subject = f"ArXiv Papers List {yesterday_date}"
body = f"Please find attached the list of papers from ArXiv for the date {yesterday_date}."

# Send email
send_email_with_attachment(gmail_user, gmail_password, receiver_email, subject, body, csv_file_path)
