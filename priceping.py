import os

import requests
from bs4 import BeautifulSoup
import re
import json
import sys
import resend
import time

from upstash_redis import Redis
from dotenv import load_dotenv

load_dotenv()

if len(sys.argv) == 2:
    if sys.argv[1] == "--check-all":
        check_all = True
    else:
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

redis = Redis(url = os.getenv("UPSTASH_REDIS_REST_URL"), token = os.getenv("UPSTASH_REDIS_REST_TOKEN"))
STATE_KEY = "priceping:products"

def get_myntra_product(url):
    for attempt in range(3):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30
            )

            response.raise_for_status()
            break

        except requests.exceptions.RequestException as e:
            if attempt == 2:
                raise

            print(f"Request failed, retrying... ({attempt + 1}/3)")
            time.sleep(5)

    soup = BeautifulSoup(response.text, "html.parser")

    print(f"Status: {response.status_code}")
    print(f"URL: {response.url}")
    print(f"Response length: {len(response.text)}")
    print(f"Title: {soup.title}")

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
    products = redis.get(STATE_KEY)

    if products is None:
        products = {}
    else:
        products = json.loads(products)

    products[product["url"]] = {
        "product_name": product["product_name"],
        "price": product["price"]
    }

    redis.set(STATE_KEY, json.dumps(products))


def load_product(url):
    products = redis.get(STATE_KEY)

    if products is None:
        return None

    products = json.loads(products)

    return products.get(url)


def load_all_products():
    products = redis.get(STATE_KEY)

    if products is None:
        return {}

    return json.loads(products)


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
        print(f"Checking {url}")
        check_product(url)

else:
    check_product(PRODUCT_URL)