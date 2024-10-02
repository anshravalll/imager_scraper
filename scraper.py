import requests
import json
import os
import uuid
import logging
from dotenv import load_dotenv
from collections import Counter

# Load environment variables from .env file
load_dotenv()

global extractor
extractor = True
global counter
counter = Counter()
global search_query
search_query = "Indian lehenga"

def extract_urls(info):
    """Extract specific product URLs from the search results."""
    
    logging.info("Initializing url and asin code extraction...") 
    products = info.get("results")
    counter["total_product_urls"] = len(products)
    product_url_list = []
    
    with open("urls.txt", 'w') as file:
        for product in products:
            product_url = product.get("optimized_url") 
            asin_code = product.get("asin")
            product_uuid = generate_uuid()

            if product_url:
                file.write(product_url + '\n')
                product_url_list.append((product_url, asin_code, product_uuid))
                counter["extracted_product_urls"] += 1
    
    logging.debug(f"From the list of {counter["total_product_urls"]} urls, {counter['extracted_product_urls']} are extracted.")
    logging.info("url and asin code extraction completed.")
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

def extract_product_details_from_directory(folder_path):
    """Extract JSON files that contains product details"""
    logging.debug(f"Attempting to extract JSON files from path: {folder_path}")
    products = []
    counter["total_product_json"] = len(os.listdir(folder_path))
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            filename_without_extention = os.path.splitext(filename)[0]

            with open(file_path, 'r') as file:
                info = json.load(file)
                product_uuid = filename_without_extention
                products.append((info, product_uuid))

            counter["extracted_product_json"] += 1
            logging.debug(f"{counter["extracted_product_json"]}/{counter["total_product_json"]} JSON files has been extracted")
            print(f"{counter["extracted_product_json"]}/{counter["total_product_json"]} JSON extracted.")
    
    logging.info("JSON extraction completed")
    print("")
    print("JSON extraction completed")
    print("")
    return products

def extract_product_details(product_url, product_json_directory = ""):
    """Extract product details for every product in the product_url list."""
    logging.info("Individual product extraction begins...")
    products = []

    if not product_json_directory:
        for product in product_url:
            asin_code = product[1] 
            product_uuid = product[2]
            response = requests_api(asin_code, query="")
            response.raise_for_status()
            info = response.json() 
            products.append((info, product_uuid))
            info_folder_path = create_product_info_directory()
            full_path = f"{info_folder_path}/{product_uuid}.json" 
    
            with open(full_path, "w") as file:
                json.dump(info, file, indent=4)
    
            counter["extracted_products"] += 1
            logging.debug(f"{counter['extracted_products']} of {counter['extracted_product_urls']} product urls has been extracted at {full_path}")
            print(f"{counter['extracted_products']} of {counter['extracted_product_urls']} extracted")

    
        if counter["extracted_products"] != counter["extracted_product_urls"]:
            missing_product_num = counter["extracted_product_urls"] - counter["extracted_products"]
            logging.warning(f"Out of {counter['extracted_product_urls']}, number of missed products are: {missing_product_num}")

        else:
            logging.info("Product detail extraction completed.")

        print("")
        print("Product details extracted.")
        print("")

    else:
        products = extract_product_details_from_directory(product_json_directory)
        
    return products 

def extract_images(product_url = [], product_json_directory = ""):
    """Extract images from the given product URLs."""
    products = extract_product_details(product_url, product_json_directory)
    for index, product in enumerate(products):
        info, product_uuid = product[0], product[1]
        image_list = list(set(info.get("images")))
        counter["total_image_urls"] = len(image_list)
        image_folder_path = create_product_directory(product_uuid)
    
        for idx, image in enumerate(image_list):
            counter["extracted_images"] = 0
            response = requests.get(image)
            response.raise_for_status()
            if response.status_code == 200:
                image_name = f"{product_uuid}_{idx + 1}.jpg"

                with open(f"{image_folder_path}/{image_name}", "wb") as file:
                    file.write(response.content)

                counter["extracted_images"] += 1
                counter["total_extracted_images"] += counter["extracted_images"]
                
        logging.debug(f"{counter['extracted_images']}/{counter["total_image_urls"]} images are extracted for {index}/{counter['extracted_products']} products at path: {image_folder_path}")
        logging.debug(f"Total extracted image count is: {counter["total_extracted_images"]}")

    logging.info("Images extracted successfully")
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
        logging.debug(f"Trying to get response object for product: {asin_code}")
    else:
        response = requests.get(search_url, params=search_params)
        logging.debug(f"Trying to get response object for search query: {query}")

    logging.debug(f"Got the respones with status code: {response.status_code}")
    
    return response

def generate_uuid():
    return str(uuid.uuid4())

def logger_setup():
    logging.basicConfig(
        filename= "scraper.log",
        filemode= "w",
        encoding= "utf-8",
        style= "{",
        format= "[{asctime}] [{levelname}] [{funcName}: {lineno}] - {message}",
        level= logging.DEBUG
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

if __name__ == "__main__":
    """Main execution block to fetch search results and extract images."""
    logger_setup()

    if extractor == True:
        logging.info("Initializing extractor")
        try:
            extract_images(product_json_directory= "products_info/Indian lehenga")
        except requests.exceptions.HTTPError as err:
            print(f"Error occurred: {err}")
            logging.exception("View the stack trace below to catch the issue.")
        logging.info("Stopping extractor")

    else:
        logging.info("Initializing scraper...")
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
                logging.exception("View the stack trace below to catch the issue.")
        else:
            print(f"Request failed with status code: {response.status_code}")

        logging.info("Stopping scraper execution.")
