import requests
from bs4 import BeautifulSoup
import time

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
    
    # Save the raw HTML to a file
    with open("page.html", 'a', encoding='utf-8') as file:
        file.write(prettified_html)
    
    # Extract product information
    products = []
    for item in soup.select('.s-main-slot .s-result-item'):
        title = item.select_one('span.a-text-normal')
        price = item.select_one('.a-price .a-offscreen')
        rating = item.select_one('.a-icon-alt')

        if title and price:
            products.append({
                'title': title.get_text(),
                'price': price.get_text(),
                'rating': rating.get_text() if rating else 'No rating'
            })

    # Print the extracted product details
    for product in products:
        print(f"Title: {product['title']}")
        print(f"Price: {product['price']}")
        print(f"Rating: {product['rating']}")
        print('-' * 40)

    # Save the extracted product details to a file
    with open("products.txt", 'a', encoding='utf-8') as file:
        for product in products:
            file.write(f"Title: {product['title']}\n")
            file.write(f"Price: {product['price']}\n")
            file.write(f"Rating: {product['rating']}\n")
            file.write('-' * 40 + '\n')
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")
    time.sleep(3)  # Delay for a few seconds and try again if needed
