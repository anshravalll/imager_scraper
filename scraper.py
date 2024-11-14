import requests
from bs4 import BeautifulSoup
import time
import csv
import logging
import random
from urllib.parse import urljoin
import argparse
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    filename='amazon_scraper.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# Amazon base URL
BASE_URL = 'https://www.amazon.com'

# Custom headers with user-agent rotation
HEADERS = {
    'Accept-Language': 'en-US,en;q=0.9',
}

# Proxy list (add your proxies here)
PROXIES = [
    # Add more proxies as needed
]

def parse_arguments():
    parser = argparse.ArgumentParser(description="Amazon product scraper")
    parser.add_argument('query', type=str, help="Search query for Amazon products")
    parser.add_argument('pages', type=int, help="Number of pages to scrape")
    parser.add_argument('output', type=str, help="Output CSV file name")
    return parser.parse_args()

def get_random_user_agent():
    ua = UserAgent()
    return ua.random

def get_random_proxy():
    return random.choice(PROXIES)

session = requests.Session()

def fetch_page(url, retries=3, backoff_factor=1):
    for attempt in range(1, retries + 1):
        try:
            headers = HEADERS.copy()
            headers['User-Agent'] = get_random_user_agent()
            proxy = get_random_proxy()
            response = session.get(url, headers=headers, proxies={"http": proxy, "https": proxy}, timeout=10)
            if response.status_code == 200:
                return response.content
            elif 500 <= response.status_code < 600:
                logging.warning(f'Server error: {response.status_code} for URL: {url}')
            else:
                logging.warning(f'Client error: {response.status_code} for URL: {url}')
                break  # Do not retry on client errors
        except requests.exceptions.RequestException as e:
            logging.error(f'Request exception: {e} for URL: {url} with proxy: {proxy}')
        sleep_time = backoff_factor * (2 ** (attempt - 1))
        logging.info(f'Attempt {attempt} failed. Sleeping for {sleep_time} seconds before retrying.')
        time.sleep(sleep_time)
    logging.error(f'Failed to fetch URL after {retries} attempts: {url}')
    return None

def parse_product(item):
    # Skip sponsored products
    if item.select_one('span.s-sponsored-label-text'):
        return None

    # Extract title
    title_tag = item.select_one('h2 a.a-link-normal.a-text-normal span')
    title = title_tag.get_text(strip=True) if title_tag else 'No title'

    # Extract price
    price_whole = item.select_one('span.a-price-whole')
    price_fraction = item.select_one('span.a-price-fraction')
    if price_whole and price_fraction:
        price = f"{price_whole.get_text(strip=True)}.{price_fraction.get_text(strip=True)}"
    else:
        price = 'No price'

    # Extract rating
    rating_tag = item.select_one('span.a-icon-alt')
    rating = rating_tag.get_text(strip=True) if rating_tag else 'No rating'

    # Extract number of reviews
    reviews_tag = item.select_one('span.a-size-base')
    reviews = reviews_tag.get_text(strip=True) if reviews_tag else 'No reviews'

    # Extract product URL
    url_tag = item.select_one('h2 a.a-link-normal.a-text-normal')
    product_url = urljoin(BASE_URL, url_tag['href']) if url_tag else 'No URL'

    # Extract image URL
    img_tag = item.select_one('img.s-image')
    image_url = img_tag['src'] if img_tag else 'No image URL'

    # Clean and validate data
    if product_url != 'No URL' and not product_url.startswith('http'):
        product_url = urljoin(BASE_URL, product_url)

    # Convert price to float
    if price != 'No price':
        price = price.replace(',', '').strip()
        try:
            price = float(price)
        except ValueError:
            price = None
    else:
        price = None

    # Convert rating to float
    if rating != 'No rating':
        try:
            rating = float(rating.split(' out of')[0])
        except ValueError:
            rating = None
    else:
        rating = None

    # Convert number of reviews to int
    if reviews != 'No reviews':
        reviews = reviews.replace(',', '').strip()
        try:
            reviews = int(reviews)
        except ValueError:
            reviews = None
    else:
        reviews = None

    return {
        'Title': title,
        'Price': price,
        'Rating': rating,
        'Number of Reviews': reviews,
        'Product URL': product_url,
        'Image URL': image_url
    }

def fetch_and_parse(url):
    html_content = fetch_page(url)
    if not html_content:
        return []
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []
    for item in soup.select('.s-main-slot .s-result-item'):
        product = parse_product(item)
        if product and product['Title'] != 'No title':
            products.append(product)
    return products

def scrape_amazon(search_query, num_pages, output_file):
    urls = [f"{BASE_URL}/s?k={search_query}&page={page}" for page in range(1, num_pages + 1)]
    all_products = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch_and_parse, url): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                products = future.result()
                all_products.extend(products)
                logging.info(f'Extracted {len(products)} products from URL: {url}')
            except Exception as e:
                logging.error(f'Error fetching/parsing URL {url}: {e}')

    # Write all products to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Title', 'Price', 'Rating', 'Number of Reviews', 'Product URL', 'Image URL']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for product in all_products:
            writer.writerow(product)

    logging.info('Scraping completed.')

if __name__ == "__main__":
    args = parse_arguments()
    scrape_amazon(args.query, args.pages, args.output)
