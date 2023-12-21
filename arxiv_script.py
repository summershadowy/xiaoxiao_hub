import requests
import xml.etree.ElementTree as ET
import csv
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def translate_text(text, source_lang='en', target_lang='zh', limit=1000):
    libretranslate_api_url = "https://libretranslate.de/translate"
    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

    # 将文本分割为多个部分
    parts = [text[i:i+limit] for i in range(0, len(text), limit)]
    translated_parts = []

    for part in parts:
        params = {
            "q": part,
            "source": source_lang, 
            "target": target_lang, 
            "format": "text"
        }
        try:
            response = requests.post(libretranslate_api_url, data=params, headers=headers)
            response.raise_for_status()
            translated_parts.append(response.json()['translatedText'])
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return "翻译失败"

    # 将翻译后的所有部分拼接成一个字符串
    return ''.join(translated_parts) 

# Fetch papers from arXiv
yesterday = datetime.now() - timedelta(1)
yesterday_date = yesterday.strftime('%Y-%m-%d')

# Get the most recent papers
api_endpoint = 'http://export.arxiv.org/api/query?'
query = 'search_query=all:LLM+AND+all:medical&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending'
full_url = api_endpoint + query

response = requests.get(full_url)

papers = []  # Initialize the list to store paper details
if response.status_code == 200:
    root = ET.fromstring(response.text)
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
        abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
        published = entry.find('{http://www.w3.org/2005/Atom}published').text.strip()
        link = entry.find('{http://www.w3.org/2005/Atom}id').text.strip()
        published_date = datetime.strptime(published, '%Y-%m-%dT%H:%M:%SZ').date()

        if published_date.strftime('%Y-%m-%d') == yesterday_date:
            try:
                translated_abstract = translate_text(abstract)  # 调用翻译函数
            except Exception as e:
                print(f"Failed to translate abstract for '{title}': {e}")
                translated_abstract = "翻译失败" 

            papers.append([title, abstract, translated_abstract, published_date.strftime('%Y-%m-%d'), link])


# Save the papers to a CSV file named with yesterday's date
csv_file_path = f'arxiv_papers_{yesterday_date}.csv'
with open(csv_file_path, 'w', newline='', encoding='utf-8-sig') as file:
    writer = csv.writer(file)
    writer.writerow(['Title', 'Abstract', 'Translated Abstract', 'Date', 'Link'])
    writer.writerows(papers) 

# Gmail 邮箱的 SMTP 服务器地址和端口
gmail_smtp_server = "smtp.gmail.com"
gmail_smtp_port = 587  # 使用TLS 

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
