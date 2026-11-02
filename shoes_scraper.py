"""
Bai tap: Thu thap danh sach giay tu website ban giay Viet Nam (Biti's)
Nguon du lieu: https://bitis.com.vn (nen tang Haravan). robots.txt cho phep
crawl /collections va /products; ta dung endpoint JSON cong khai cua Haravan
nen khong can parse HTML.

Cach chay:
    python3 shoes_scraper.py [so_trang_toi_da]
Ket qua: data/raw_shoes.csv va anh dai dien trong data/images_shoes/
"""

import csv
import os
import sys
import time

import requests

API_URL = "https://bitis.com.vn/collections/all/products.json"
PRODUCT_URL = "https://bitis.com.vn/products/{}"
OUTPUT_FILE = "data/raw_shoes.csv"
IMAGE_DIR = "data/images_shoes"
HEADERS = {"User-Agent": "Mozilla/5.0 (educational scraping exercise)"}
FIELDS = [
    "id", "name", "product_type", "price_vnd", "compare_at_price_vnd",
    "colors", "sizes", "available", "url", "image_url", "image_path", "image_urls",
]


def download_image(image_url):
    """Tai anh ve IMAGE_DIR, tra ve duong dan file (bo qua neu da co)."""
    path = os.path.join(IMAGE_DIR, os.path.basename(image_url.split("?")[0]))
    if os.path.exists(path):
        return path
    response = requests.get(image_url, headers=HEADERS, timeout=10)
    if response.status_code != 200:
        return ""
    with open(path, "wb") as f:
        f.write(response.content)
    return path


def option_values(product, name):
    for option in product.get("options", []):
        if option["name"] == name:
            return option["values"]
    return []


def parse_product(product):
    variants = product.get("variants", [])
    prices = [float(v["price"]) for v in variants if v.get("price")]
    compare = [float(v["compare_at_price"]) for v in variants if v.get("compare_at_price")]
    images = [img["src"] for img in product.get("images", [])]
    main_image = images[0] if images else ""

    return {
        "id": product["id"],
        "name": product["title"],
        "product_type": product.get("product_type", ""),
        "price_vnd": int(min(prices)) if prices else "",
        "compare_at_price_vnd": int(max(compare)) if compare and max(compare) > 0 else "",
        "colors": "|".join(option_values(product, "Màu sắc")),
        "sizes": "|".join(option_values(product, "Kích thước")),
        "available": product.get("available", False),
        "url": PRODUCT_URL.format(product["handle"]),
        "image_url": main_image,
        "image_path": download_image(main_image) if main_image else "",
        "image_urls": "|".join(images),
    }


def scrape_page(page_number):
    response = requests.get(
        API_URL, params={"limit": 250, "page": page_number}, headers=HEADERS, timeout=15
    )
    if response.status_code != 200:
        return None
    return response.json().get("products", [])


def main():
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else None
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    all_products = []
    page = 1

    while max_pages is None or page <= max_pages:
        print(f"Dang thu thap trang {page} ...")
        products = scrape_page(page)
        if not products:
            break
        for product in products:
            all_products.append(parse_product(product))
            time.sleep(0.2)  # lich su voi server khi tai anh
        page += 1
        time.sleep(0.5)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_products)

    print(f"Da luu {len(all_products)} san pham vao {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
