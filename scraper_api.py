import requests
from bs4 import BeautifulSoup

# Amazon URL
url = 'https://www.amazon.com/s?k=gaming'

# Custom headers
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Accept-Language': 'en-US, en;q=0.5'
}

# Make a GET request to fetch the raw HTML content
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    prettified_html = soup.prettify()
    with open("page.html", 'a', encoding = 'utf-8') as file:
        file.write(prettified_html)
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")
