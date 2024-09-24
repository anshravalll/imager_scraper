# import requests
# from bs4 import BeautifulSoup
#
#
# api_key = "66f2d33dc47a17ab791d2453"
# url = "https://api.scrapingdog.com/amazon/search"
#
# params = {
#     "api_key": api_key,
#     "domain": "com",
#     "query": "Indian dress"
# }
#
# response = requests.get(url, params=params)
#
# if response.status_code == 200: #Success
#     html_content = response.json()
#     # Save the HTML content to a file
#     with open("page.html", "w", encoding='utf-8') as file:
#         file.write(html_content)
#     print("HTML content saved to page.html. Open it in your browser to view.")
# else:
#     print(f"HTTP Request Error: {response.status_code}")

import requests
import json
  
api_key = "63655678cd36805b2cb76220"
url = "https://api.scrapingdog.com/amazon/search"
  
params = {
    "api_key": api_key,
    "asin": "",
    "domain": "com",
    "query": "Indian dress",
    "page": '1'
}
  
response = requests.get(url, params=params)
  
if response.status_code == 200:
    info = response.json()
    with open("page.json", "w") as file:
        json.dump(info, file, indent=4) 
    print("done bruh")
        
else:
    print(f"Request failed with status code: {response.status_code}")
