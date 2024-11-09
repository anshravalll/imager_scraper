import requests
from bs4 import BeautifulSoup
import time
import csv
import logging
import random
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    filename='amazon_scraper.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# Amazon base URL
BASE_URL = 'https://www.amazon.com'

# Search query
SEARCH_QUERY = 'gaming'

# Number of pages to scrape
NUM_PAGES = 5

# Custom headers with a list of user agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
    ' Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
    ' Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko)'
    ' Version/14.0.3 Safari/605.1.15',
    # Add more user agents as needed
]

HEADERS = {
    'Accept-Language': 'en-US,en;q=0.9',
}

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def fetch_page(url, retries=3):
    for attempt in range(retries):
        try:
            headers = HEADERS.copy()
            headers['User-Agent'] = get_random_user_agent()
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.content
            else:
                logging.warning(f'Non-200 status code: {response.status_code} for URL: {url}')
        except requests.exceptions.RequestException as e:
            logging.error(f'Request exception: {e} for URL: {url}')
        time.sleep(random.uniform(2, 5))  # Wait before retrying
    logging.error(f'Failed to fetch URL after {retries} attempts: {url}')
    return None

def parse_product(item):
    # Extract title
    title_tag = item.select_one('span.a-text-normal')
    title = title_tag.get_text(strip=True) if title_tag else 'No title'

    # Extract price
    whole_price = item.select_one('.a-price-whole')
    fraction_price = item.select_one('.a-price-fraction')
    if whole_price and fraction_price:
        price = f"${whole_price.get_text(strip=True)}.{fraction_price.get_text(strip=True)}"
    else:
        price = 'No price'

    # Extract rating
    rating_tag = item.select_one('.a-icon-alt')
    rating = rating_tag.get_text(strip=True) if rating_tag else 'No rating'

    # Extract number of reviews
    reviews_tag = item.select_one('span.a-size-base')
    reviews = reviews_tag.get_text(strip=True) if reviews_tag else 'No reviews'

    # Extract product URL
    url_tag = item.select_one('a.a-link-normal.a-text-normal')
    product_url = urljoin(BASE_URL, url_tag['href']) if url_tag else 'No URL'

    # Extract image URL
    img_tag = item.select_one('img.s-image')
    image_url = img_tag['src'] if img_tag else 'No image URL'

    return {
        'Title': title,
        'Price': price,
        'Rating': rating,
        'Number of Reviews': reviews,
        'Product URL': product_url,
        'Image URL': image_url
    }

def scrape_amazon():
    # Open CSV file for writing
    with open('amazon_products.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Title', 'Price', 'Rating', 'Number of Reviews', 'Product URL', 'Image URL']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for page in range(1, NUM_PAGES + 1):
            search_url = f"{BASE_URL}/s?k={SEARCH_QUERY}&page={page}"
            logging.info(f'Scraping URL: {search_url}')
            html_content = fetch_page(search_url)
            if not html_content:
                logging.error(f'Skipping page {page} due to fetch failure.')
                continue

            soup = BeautifulSoup(html_content, 'html.parser')

            # Save raw HTML to a file (optional)
            with open(f"page_{page}.html", 'w', encoding='utf-8') as file:
                file.write(soup.prettify())

            # Extract product information
            products = []
            for item in soup.select('.s-main-slot .s-result-item'):
                product = parse_product(item)
                if product['Title'] != 'No title':  # Basic check to ensure it's a valid product
                    products.append(product)

            logging.info(f'Extracted {len(products)} products from page {page}.')

            # Write products to CSV
            for product in products:
                writer.writerow(product)

            # Print the extracted product details (optional)
            for product in products:
                print(f"Title: {product['Title']}")
                print(f"Price: {product['Price']}")
                print(f"Rating: {product['Rating']}")
                print(f"Number of Reviews: {product['Number of Reviews']}")
                print(f"Product URL: {product['Product URL']}")
                print(f"Image URL: {product['Image URL']}")
                print('-' * 40)

            # Random delay to mimic human behavior
            sleep_time = random.uniform(3, 7)
            logging.info(f'Sleeping for {sleep_time:.2f} seconds.')
            time.sleep(sleep_time)

    logging.info('Scraping completed.')

if __name__ == "__main__":
    scrape_amazon()
