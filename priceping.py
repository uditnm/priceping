import os

import requests
from bs4 import BeautifulSoup
import re
import json
import sys
import resend
from dotenv import load_dotenv

load_dotenv()

if len(sys.argv) == 2 and sys.argv[1] == "--check-all":
    check_all = True
elif len(sys.argv) == 1:
    check_all = False
    PRODUCT_URL = sys.argv[1]
else:
    print("Usage:")
    print("  python priceping.py <myntra-product-url>")
    print("  python priceping.py --check-all")
    sys.exit(1)


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
    name = soup.find(
            "meta",
            attrs={"name": "keywords"}
        )
    
    if not name:
        raise ValueError("Could not find product name")

    keywords = name["content"]

    product_name = keywords.split(",")[0].strip()

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

def load_all_products():
    try:
        with open("state.json", "r") as file:
            state = json.load(file)

        return state.get("products", {})

    except FileNotFoundError:
        return {}


def send_email_notification(product, previous_price):
    current_price = product["price"]

    if(current_price < previous_price):
        subject = f"Price dropped for {product['product_name']}"
        change_text = f"Price dropped by ₹{previous_price - current_price}!"
    else:
        subject = f"Price increased for {product['product_name']}"
        change_text = f"Price increased by ₹{current_price - previous_price}!"

    html = f"""
    <h2>{product['product_name']}</h2>

    <p>{change_text}</p>

    <p>
        Previous price: ₹{previous_price}<br>
        Current price: ₹{current_price}
    </p>

    <p>
        <a href="{product['url']}">View product</a>
    </p>
    """

    resend.api_key = os.getenv("RESEND_API_KEY")

    resend.Emails.send({
        "from": "PricePing <onboarding@resend.dev>",
        "to": [os.getenv("EMAIL_TO")],
        "subject": subject,
        "html": html
    })


def check_product(url):
    product = get_myntra_product(url)
    previous_product = load_product(url)

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

            send_email_notification(product, previous_price)
            
        elif current_price > previous_price:
            difference = current_price - previous_price
            print(f"Price increased by ₹{difference}!")

            send_email_notification(product, previous_price)

        else:
            print("Price unchanged.")

    save_product(product)


if check_all:
    products = load_all_products()

    for url in products.keys():
        print(f"Checking {url}...")
        check_product(url)

else:
    check_product(PRODUCT_URL)