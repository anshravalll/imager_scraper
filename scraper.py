import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def extract_urls(info):
    """Extract specific product URLs from the search results."""
    
    products = info.get("results")
    product_url_list = []
    
    with open("urls.txt", 'w') as file:
        for product in products:
            product_url = product.get("optimized_url") 
            asin_code = product.get("asin")
            if product_url:
                file.write(product_url + '\n')
                product_url_list.append((product_url, asin_code))
    
    print('URLs and ASINs provided.')
    return product_url_list

def extract_product_details(product_url):
    """Extract product details for every product in the product_url list."""
    asin_code = product_url[0][1]
    response = requests_api(asin_code, query="")
    response.raise_for_status()
    info = response.json() 
    
    with open("product_details.json", "w") as file:
        json.dump(info, file, indent=4)
    
    print("Product details extracted.")
    return info

def extract_images(product_url):
    """Extract images from the given product URLs."""
    info = extract_product_details(product_url)
    image_list = info.get("images")
    
    for idx, image in enumerate(image_list):
        response = requests.get(image)
        if response.status_code == 200:
            image_name = f"downloaded_image_{idx}.jpg"
            with open(image_name, "wb") as file:
                file.write(response.content)
    
    print("Images downloaded successfully.")

def requests_api(asin_code, query, product=True, domain='com', country='us', page='1'):
    """Make API requests to fetch product or search data."""
    api_key = os.getenv('scrapingdog_api')
    search_url = "https://api.scrapingdog.com/amazon/search"
    product_url = "https://api.scrapingdog.com/amazon/product"
  
    search_params = {
        "api_key": api_key,
        "domain": domain,
        "query": query,
        "page": page,
        "country": country
    }

    product_params = {
        "api_key": api_key,
        "domain": domain,
        "asin": asin_code,
        "country": country
    }

    if product:
        response = requests.get(product_url, params=product_params)
    else:
        response = requests.get(search_url, params=search_params)
    
    return response

if __name__ == "__main__":
    """Main execution block to fetch search results and extract images."""
    
    response = requests_api(query="Indian dress", product=False, asin_code="")
    
    if response.status_code == 200:
        info = response.json()
        with open("page.json", "a") as file:
            json.dump(info, file, indent=4)
        print("Search response received.")
        
        try:
            product_url = extract_urls(info)
            extract_images(product_url)
        except requests.exceptions.HTTPError as err:
            print(f"Error occurred: {err}")
    else:
        print(f"Request failed with status code: {response.status_code}")
