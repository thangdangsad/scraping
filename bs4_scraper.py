"""
Bai tap: Thu thap danh sach san pham bang BeautifulSoup
Nguon du lieu: http://books.toscrape.com (website mo, duoc dung rieng de luyen scraping)

Cach chay:
    python3 bs4_scraper.py
Ket qua: data/raw_bs4.csv va anh bia sach trong data/images/
"""

import csv
import os
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://books.toscrape.com/catalogue/page-{}.html"
OUTPUT_FILE = "data/raw_bs4.csv"
IMAGE_DIR = "data/images"
HEADERS = {"User-Agent": "Mozilla/5.0 (educational scraping exercise)"}


def download_image(image_url):
    """Tai anh ve IMAGE_DIR, tra ve duong dan file (bo qua neu da co)."""
    path = os.path.join(IMAGE_DIR, os.path.basename(image_url))
    if os.path.exists(path):
        return path
    response = requests.get(image_url, headers=HEADERS, timeout=10)
    if response.status_code != 200:
        return ""
    with open(path, "wb") as f:
        f.write(response.content)
    return path


def scrape_page(page_number):
    url = BASE_URL.format(page_number)
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code != 200:
        return None

    # Server khong tra Content-Type kem charset nen requests mac dinh doan
    # ISO-8859-1, lam sai ky tu £. Dua response.content (bytes) cho
    # BeautifulSoup de no tu doc <meta charset="utf-8"> trong HTML.
    soup = BeautifulSoup(response.content, "html.parser")
    products = []

    for article in soup.select("article.product_pod"):
        name = article.h3.a["title"]
        price = article.select_one("p.price_color").get_text(strip=True)
        availability = article.select_one("p.instock.availability").get_text(strip=True)
        rating_class = article.select_one("p.star-rating")["class"]
        rating = rating_class[1] if len(rating_class) > 1 else ""

        # src la duong dan tuong doi (../media/...), doi sang URL day du
        image_url = urljoin(url, article.select_one("img.thumbnail")["src"])
        image_path = download_image(image_url)
        time.sleep(0.2)

        products.append({
            "name": name,
            "price": price,
            "availability": availability,
            "rating": rating,
            "image_url": image_url,
            "image_path": image_path,
        })

    return products


def main():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    all_products = []
    page = 1

    while True:
        print(f"Dang thu thap trang {page} ...")
        products = scrape_page(page)
        if not products:
            break
        all_products.extend(products)
        page += 1
        time.sleep(0.5)  # tranh gui request qua nhanh, lich su voi server

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "price", "availability", "rating", "image_url", "image_path"])
        writer.writeheader()
        writer.writerows(all_products)

    print(f"Da luu {len(all_products)} san pham vao {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
