import requests
import xml.etree.ElementTree as ET
import csv
from datetime import datetime, timedelta

# Define the date range (yesterday)
yesterday = datetime.now() - timedelta(1)
yesterday_date = yesterday.strftime('%Y-%m-%d')

# arXiv API endpoint and query
api_endpoint = 'http://export.arxiv.org/api/query?'
query = 'search_query=all:LLM+AND+all:medical&start=0&max_results=50&sortBy=submittedDate&sortOrder=descending'

# Send the request to the arXiv API
response = requests.get(api_endpoint + query)

if response.status_code == 200:
    # Parse the response XML
    root = ET.fromstring(response.text)

    papers = []
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
        abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
        published = entry.find('{http://www.w3.org/2005/Atom}published').text.strip()
        link = entry.find('{http://www.w3.org/2005/Atom}id').text.strip()

        # Parse the published date
        published_date = datetime.strptime(published, '%Y-%m-%dT%H:%M:%SZ').date()

        # Check if the published date is yesterday
        if published_date.strftime('%Y-%m-%d') == yesterday_date:
            papers.append([title, abstract, published_date.strftime('%Y-%m-%d'), link])

    # Save the papers to a CSV file
    with open('output.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Title', 'Abstract', 'Date', 'Link'])
        writer.writerows(papers)
else:
    print("Failed to retrieve data from arXiv API.")
