import requests
import json
import os
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

global search_query
search_query = "Indian lehenga"

def extract_urls(info):
    """Extract specific product URLs from the search results."""
    
    products = info.get("results")
    product_url_list = []
    
    with open("urls.txt", 'w') as file:
        for product in products:
            product_url = product.get("optimized_url") 
            asin_code = product.get("asin")
            product_uuid = generate_uuid()

            if product_url:
                file.write(product_url + '\n')
                product_url_list.append((product_url, asin_code, product_uuid))
    
    print('URLs and ASINs provided.')
    return product_url_list

def create_product_directory(product_uuid):
    """products ----> {UUID} ----> images ----> {UUID}_idx"""
    product_path = os.path.join("products", product_uuid, "images")
    os.makedirs(product_path, exist_ok = True)
    return product_path

def create_product_info_directory(query = search_query):
    """products_info ----> {query} ----> {UUID}.json"""
    info_path = os.path.join("products_info", query)
    os.makedirs(info_path, exist_ok = True)
    return info_path

def extract_product_details(product_url):
    """Extract product details for every product in the product_url list."""
    asin_code = product_url[0][1]
    product_uuid = product_url[0][2]
    response = requests_api(asin_code, query="")
    response.raise_for_status()
    info = response.json() 
    info_folder_path = create_product_info_directory()
    
    with open(f"{info_folder_path}/{product_uuid}.json", "w") as file:
        json.dump(info, file, indent=4)
    
    print("Product details extracted.")
    return info, product_uuid

def extract_images(product_url):
    """Extract images from the given product URLs."""
    info, product_uuid = extract_product_details(product_url)
    image_list = list(set(info.get("images")))
    image_folder_path = create_product_directory(product_uuid)
    
    for idx, image in enumerate(image_list):
        response = requests.get(image)
        if response.status_code == 200:
            image_name = f"{product_uuid}_{idx + 1}.jpg"
            with open(f"{image_folder_path}/{image_name}", "wb") as file:
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

def generate_uuid():
    return str(uuid.uuid4())

if __name__ == "__main__":
    """Main execution block to fetch search results and extract images."""
    response = requests_api(query = search_query, product=False, asin_code="")
    
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
