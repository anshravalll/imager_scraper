import requests
import json
import os
import re
import uuid
import logging
from dotenv import load_dotenv
from collections import Counter

# Load environment variables from .env file
load_dotenv()

global extractor
extractor = False 
global counter
counter = Counter()
global search_query
search_query = "Chaniya choli"

def generate_uuid():
    return str(uuid.uuid4())

def is_unique_asin(asin, asin_set = set()):
    if asin not in asin_set:
        return True

    logging.debug(f"{asin} already exists")
    return False

def append_asin(asin, filepath, asin_set = set()):
    asin_set.add(asin)
    with open(filepath, "a") as file:
        file.write(f"{asin}\n")

def asin_loader(filepath = "asin_archive.txt"):
    asin_set = set()
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            asins = file.readlines()
            for line in asins:
                asin_set.add(line.strip())
    return asin_set

def asin_handler(asin):
    filepath = "asin_archive.txt"
    if os.path.exists(filepath):
        asin_set = asin_loader()

        if is_unique_asin(asin, asin_set):
            append_asin(asin, filepath, asin_set)
            return True
        else:
            return False

    else:
        with open(filepath, "a") as file:
            pass
        append_asin(asin, filepath)
        return True

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

def sanitize_folder_name(name, chr_set='printable'):
    """Converts name to a valid filename.

    Args:
        name: The str to convert.
        chr_set:
            'printable':    Any printable character except those disallowed on Windows/*nix.
            'extended':     'printable' + extended ASCII character codes 128-255
            'universal':    For almost *any* file system. '-.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    """

    FILLER = '-'  # Character to replace illegal characters
    MAX_LEN = 255  # Maximum length of filename is 255 bytes in Windows and some *nix flavors.

    # Step 1: Remove excluded characters.
    BLACK_LIST = set(chr(127) + r'<>:"/\|?*')  # 127 is unprintable, the rest are illegal in Windows.
    white_lists = {
        'universal': set('-.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'),
        'printable': {chr(x) for x in range(32, 127)} - BLACK_LIST,  # 0-32, 127 are unprintable,
        'extended': {chr(x) for x in range(32, 256)} - BLACK_LIST,
    }
    white_list = white_lists[chr_set]
    result = ''.join(x if x in white_list else FILLER for x in name)

    # Step 2: Device names, '.', and '..' are invalid filenames in Windows.
    DEVICE_NAMES = 'CON,PRN,AUX,NUL,COM1,COM2,COM3,COM4,' \
                   'COM5,COM6,COM7,COM8,COM9,LPT1,LPT2,' \
                   'LPT3,LPT4,LPT5,LPT6,LPT7,LPT8,LPT9,' \
                   'CONIN$,CONOUT$,..,.'.split(',')  # This list is an O(n) operation.
    if result in DEVICE_NAMES:
        result = f'{FILLER}{result}{FILLER}'

    # Step 3: Truncate long files while preserving the file extension.
    if len(result) > MAX_LEN:
        if '.' in name:
            result, _, ext = result.rpartition('.')
            ext = '.' + ext
        else:
            ext = ''
        result = result[:MAX_LEN - len(ext)] + ext

    # Step 4: Windows does not allow filenames to end with '.' or ' ' or begin with ' '.
    result = re.sub(r'^[. ]', FILLER, result)
    result = re.sub(r' $', FILLER, result)

    return result

def create_product_directory(info):
    """SOURCE → SECTION → CATEGORY → ITEM NAME → COLOR → IMAGES"""
    directory_structure = {
        "Source": "Amazon",
        "Section": "Women",
        "Category": search_query,
        "Title": sanitize_folder_name(info.get("title"))
    }
    product_path = os.path.join(*directory_structure.values(), "Images")
    
    # Prepend \\?\ to handle long paths on Windows
    if os.name == 'nt':
        product_path = '\\\\?\\' + os.path.abspath(product_path)
    
    try:
        os.makedirs(product_path, exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to create directory {product_path}: {e}")
        raise
    
    return product_path

def create_product_info_directory(query = search_query):
    """products_info → {query} → {UUID}.json"""
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

            if not asin_handler(asin_code): #if asin_handler is True, the asin code already exists in the archival
                counter["existing_products"] += 1
                continue

            response = requests_api(asin_code, query="")
            response.raise_for_status()
            info = response.json() 
            products.append((info, product_uuid))
            info_folder_path = create_product_info_directory()
            full_path = f"{info_folder_path}/{product_uuid}.json" 
    
            with open(full_path, "w") as file:
                json.dump(info, file, indent=4)
    
            counter["extracted_products"] += 1
            logging.debug(f"{counter['extracted_products']}/{counter['extracted_product_urls']} product urls has been extracted at {full_path}")
            print(f"{counter['extracted_products']}/{counter['extracted_product_urls']} extracted")

    
        if counter["extracted_products"] != counter["extracted_product_urls"] - counter["existing_products"]:
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

        #Skip the info which contains multiple nested products through customization options
        if info.get("customization_options").get("color"): 
            continue

        image_url_list = list(set(info.get("images")))
        counter["total_image_urls"] = len(image_url_list)
        image_folder_path = create_product_directory(info)
        counter["extracted_images"] = 0
    
        for idx, image in enumerate(image_url_list):
            image_name = f"{product_uuid}_{idx + 1}.jpg"
            if not os.path.exists(f"{image_folder_path}/{image_name}"):
                response = requests.get(image)
                response.raise_for_status()
                if response.status_code == 200:
                    image_path = os.path.join(image_folder_path, image_name)
                    with open(image_path, "wb") as file:
                        file.write(response.content)

                    counter["extracted_images"] += 1
                    counter["total_extracted_images"] += counter["extracted_images"]

            else:
               counter["existing_images"] += 1
                
        logging.debug(f"{counter['extracted_images']}/{counter["total_image_urls"]} images are extracted for {index + 1}/{len(products)} products at path: {image_folder_path}")
        logging.debug(f"Total extracted image count is: {counter["total_extracted_images"]} with existing image count of: {counter["existing_images"]}")

    logging.info("Images extracted successfully")
    print("Images downloaded successfully.")

def requests_api(asin_code, query, product=True, domain='com', country='us', page=1):
    """Make API requests to fetch product or search data."""
    api_key = os.getenv('scrapingdog_api')
    search_url = "https://api.scrapingdog.com/amazon/search"
    product_url = "https://api.scrapingdog.com/amazon/product"
  
    search_params = {
        "api_key": api_key,
        "domain": domain,
        "query": query,
        "page": str(page),
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

def logger_setup():
    """Setting up logger for application logging"""
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
        response = requests_api(query = search_query, product=False, asin_code="", page = 3)

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
