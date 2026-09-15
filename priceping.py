import requests
from bs4 import BeautifulSoup
import re
import json
import sys

if len(sys.argv) != 2:
    print("Usage: python priceping.py <myntra-product_url>")
    sys.exit(1)

PRODUCT_URL = sys.argv[1]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}

def get_myntra_product(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Product name
    title = soup.find("title")

    if not title:
        raise ValueError("Could not find product name")

    #product_name = title.get_text(strip=True)

    name = soup.find(
            "meta",
            attrs={"name": "keywords"}
        )
    
    if not name:
        raise ValueError("Could not find product name")

    prod_name_text = name["content"]

    product_name = prod_name_text.split(",")[0].strip()

    # Product description
    description = soup.find(
        "meta",
        attrs={"name": "description"}
    )

    if not description:
        raise ValueError("Could not find product description")

    text = description["content"]

    match = re.search(r"Rs\.\s*([\d,]+)", text)

    if not match:
        raise ValueError("Could not find price in product description")

    price = int(match.group(1).replace(",", ""))

    return {
        "url": url,
        "product_name": product_name,
        "price": price
    }


def save_product(product):
    try:
        with open("state.json", "r") as file:
            state = json.load(file)
    except FileNotFoundError:
        state = {"products": {}}

    state["products"][product["url"]] = {
        "product_name": product["product_name"],
        "price": product["price"]
    }

    with open("state.json", "w") as file:
        json.dump(state, file, indent=4)


def load_product(url):
    try:
        with open("state.json", "r") as file:
            state = json.load(file)

        return state["products"].get(url)

    except FileNotFoundError:
        return None

        
product = get_myntra_product(PRODUCT_URL)
previous_product = load_product(PRODUCT_URL)

print(f"Product: {product['product_name']}")
print(f"Current price: ₹{product['price']}")

if previous_product is None:
    print("First run — saving product.")

else:
    previous_price = previous_product["price"]
    current_price = product["price"]

    if current_price < previous_price:
        difference = previous_price - current_price
        print(f"Price dropped by ₹{difference}!")
        
    elif current_price > previous_price:
        difference = current_price - previous_price
        print(f"Price increased by ₹{difference}!")

    else:
        print("Price unchanged.")

save_product(product)