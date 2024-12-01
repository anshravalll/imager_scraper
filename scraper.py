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

# Configure logging
logging.basicConfig(
    filename='amazon_scraper.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

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
    if PROXIES:
        return random.choice(PROXIES)
    return None  # Return None if no proxies are available

def fetch_page(url, retries=3, backoff_factor=1, timeout=10):
    """Fetch a page with retries and exponential backoff in case of errors."""
    for attempt in range(1, retries + 1):
        try:
            headers = HEADERS.copy()
            headers['User-Agent'] = get_random_user_agent()
            proxy = get_random_proxy()
            # Refactored: Directly pass proxy to requests.get() method
            response = requests.get(url, headers=headers, proxies={"http": proxy, "https": proxy} if proxy else None, timeout=timeout)
            
            if response.status_code == 200:
                return response.content
            elif 500 <= response.status_code < 600:
                logging.warning(f'Server error: {response.status_code} for URL: {url}')
            elif response.status_code == 403:
                logging.warning(f'403 Forbidden: Access Denied for URL: {url}')
                break
            else:
                logging.warning(f'Client error: {response.status_code} for URL: {url}')
                break
        except requests.exceptions.RequestException as e:
            logging.error(f'Request exception: {e} for URL: {url} with proxy: {proxy}')
        
        # Exponential backoff
        sleep_time = backoff_factor * (2 ** (attempt - 1))
        logging.info(f'Attempt {attempt} failed. Sleeping for {sleep_time} seconds before retrying.')
        time.sleep(sleep_time)
    
    logging.error(f'Failed to fetch URL after {retries} attempts: {url}')
    return None

def parse_product(item):
    # Skip sponsored products
    if item.select_one('span.s-sponsored-label-text'):
        return None

    def parse_price(item):
        price_whole = item.select_one('span.a-price-whole')
        price_fraction = item.select_one('span.a-price-fraction')
        if price_whole and price_fraction:
            return float(price_whole.get_text(strip=True).replace(',', '') + '.' + price_fraction.get_text(strip=True))
        return None

    def parse_rating(item):
        rating_tag = item.select_one('span.a-icon-alt')
        if rating_tag:
            try:
                return float(rating_tag.get_text(strip=True).split(' out of')[0])
            except ValueError:
                return None
        return None

    def parse_reviews(item):
        reviews_tag = item.select_one('span.a-size-base')
        if reviews_tag:
            try:
                return int(reviews_tag.get_text(strip=True).replace(',', ''))
            except ValueError:
                return None
        return None

    # Extract title
    title_tag = item.select_one('h2 a.a-link-normal.a-text-normal span')
    title = title_tag.get_text(strip=True) if title_tag else 'No title'

    # Extract price
    price = parse_price(item)

    # Extract rating
    rating = parse_rating(item)

    # Extract number of reviews
    reviews = parse_reviews(item)

    # Extract product URL
    url_tag = item.select_one('h2 a.a-link-normal.a-text-normal')
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

def fetch_and_parse(url):
    html_content = fetch_page(url)
    if not html_content:
        return []
    soup = BeautifulSoup(html_content, 'html.parser')
    products = [parse_product(item) for item in soup.select('.s-main-slot .s-result-item') if parse_product(item)]
    return products

def scrape_amazon(search_query, num_pages, output_file):
    urls = [f"{BASE_URL}/s?k={search_query}&page={page}" for page in range(1, num_pages + 1)]
    all_products = []

    logging.info(f"Starting to scrape {num_pages} pages for search query: {search_query}")

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

    logging.info(f'Scraping completed. Extracted {len(all_products)} products in total from {num_pages} pages.')

if __name__ == "__main__":
    args = parse_arguments()
    scrape_amazon(args.query, args.pages, args.output)
