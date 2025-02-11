import requests
import json
from bs4 import BeautifulSoup
from collections import defaultdict

tag_dict = defaultdict(dict)

def find_asin(soup):
    for parent in soup.parents:
        if parent.name == "div" and "puis-card-container" in parent.get("class", {}) and "s-card-container" in parent.get("class", {}):
            return parent["data-dib-asin"]

def reviews_number(soup):
    review_component = soup.find_all("div", {"data-csa-c-content-id": "alf-customer-ratings-count-component"})
    for each_component in review_component:
        total_reviews = each_component.find("span").get_text()
        asin = find_asin(each_component)
        print(asin)
        tag_dict[asin]["total_reviews"] = total_reviews
        return total_reviews

def stars_number(soup):
    star_component = soup.find_all("i", {"data-cy": "reviews-ratings-slot"})
    for each_component in star_component:
        stars = each_component.parent.get("aria-label").split()[0]
        asin = find_asin(each_component)
        print(asin)
        tag_dict[asin]["stars"] = stars
        return stars

def info_tags(soup):
    badge_component = soup.find_all("span", {"data-component-type": "s-status-badge-component"})
    for element in badge_component:
        tag_str = element["data-component-props"]
        tag = json.loads(tag_str) 
        asin = find_asin(element) 
        badge_type = tag["badgeType"]
        if badge_type == "amazons-choice":
            tag_dict[asin]["Is_amazon_choice"] = True
        elif badge_type == "best-seller":
            tag_dict[asin]["Is_best_seller"] = True
        else:
            tag_dict[asin]["Other_tags"] = True
    print("Got the Asin from info_tags")

    return tag_dict

def get_image_url(soup):
    images = soup.find_all("img", {"class": "s-image"})
    image_url = []
    for image in images:
        asin = find_asin(image)
        image_url = [image['src']]
        tag_dict[asin]["Image_url"] = image_url
    print("Got the asin from image_url")
    return image_url

def get_title(soup):
    titles = []
    class_string = "a-section a-spacing-small puis-padding-left-small puis-padding-right-small"
    div = soup.find_all("div", {"class": class_string})
    for lower_part in div:
        asin = find_asin(lower_part)
        title = lower_part.find("h2")
        titles.append(title["aria-label"])
        tag_dict[asin]["Title"] = title["aria-label"]
    print("Got the asinn from titles")
    return titles

def get_price(soup):
    result = []
    outer_span = soup.find_all("span", {"class": "a-price"})
    for span in outer_span:
        asin = find_asin(span)
        price_tag = span.find("span", {"class": "a-offscreen"})
        price = price_tag.get_text(strip=True) if price_tag else "Price not found"
        result.append(price) 
        tag_dict[asin]["Price"] = price
    print("Got the asin from prices")
    return result

def wrapper(soup):
    get_price(soup)
    get_title(soup)
    info_tags(soup)
    get_image_url(soup)
    reviews_number(soup)
    stars_number(soup)

    for each_asin in tag_dict.keys():
        print(f"{each_asin}:    ")
        for each_attribute in tag_dict[each_asin].keys():
            print(f"{each_attribute}:    {tag_dict[each_asin][each_attribute]}") 
        print(end = "\n\n\n")
# Amazon URL
url = 'https://www.amazon.com/s?k=gamings'

# Custom headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    'Referer': 'https://google.com',
    'Origin': 'https://www.amazon.com',
    "Accept-Language": "en-US"
}

# Make a GET request to fetch the raw HTML content
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    wrapper(soup)
    # Print the prettified HTML
    # print(soup.prettify())
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")
