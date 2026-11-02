"""
Bai tap: Thu thap danh sach giay tu nhieu website ban giay Viet Nam
Nguon du lieu: cac shop chay tren Haravan/Shopify. Moi shop co endpoint JSON
cong khai /collections/all/products.json, robots.txt cho phep crawl
/collections va /products, nen khong can parse HTML.

    biti       - https://bitis.com.vn          (Biti's)
    crocs      - https://crocs.com.vn          (Crocs)
    supersports- https://supersports.com.vn    (nhieu hang: Nike, Adidas, Hoka, ...)
    sneakerbuzz- https://sneakerbuzz.vn        (Sneaker Buzz)

Cach chay:
    python3 shoes_scraper.py                    # tat ca shop
    python3 shoes_scraper.py crocs biti         # chi mot so shop
    python3 shoes_scraper.py --max-pages 2      # gioi han so trang moi shop
Ket qua: data/raw_shoes_<YYYY-MM-DD>.csv va anh dai dien trong data/images_shoes/<shop>/
"""

import argparse
import csv
import os
import time

import requests

SITES = {
    "biti": "https://bitis.com.vn",
    "crocs": "https://crocs.com.vn",
    "supersports": "https://supersports.com.vn",
    "sneakerbuzz": "https://sneakerbuzz.vn",
}
OUTPUT_FILE = "data/raw_shoes_{date}.csv"  # moi ngay mot file, giu lich su gia
IMAGE_DIR = "data/images_shoes"
HEADERS = {"User-Agent": "Mozilla/5.0 (educational scraping exercise)"}
FIELDS = [
    "site", "id", "brand", "name", "product_type", "price_vnd",
    "compare_at_price_vnd", "colors", "sizes", "available", "url",
    "image_url", "image_path", "image_urls",
]
# Shop ban ca quan ao, tui, balo ... nen chi giu san pham co product_type la giay/dep
SHOE_KEYWORDS = ("giày", "giay", "dép", "dep", "sandal", "clog", "slide",
                 "flip", "flat", "sneaker", "boot", "shoe", "loafer")


def get_with_retry(url, **kwargs):
    """GET, neu bi gioi han toc do (429) hoac loi server (5xx) thi cho roi thu lai."""
    response = None
    for attempt in range(5):
        response = requests.get(url, headers=HEADERS, timeout=20, **kwargs)
        if response.status_code != 429 and response.status_code < 500:
            break
        retry_after = response.headers.get("Retry-After", "")
        wait = int(retry_after) if retry_after.isdigit() else 15 * 2 ** attempt
        print(f"  HTTP {response.status_code}, cho {wait}s roi thu lai ...")
        time.sleep(wait)
    return response


def is_shoe(product):
    product_type = product.get("product_type", "").lower()
    return any(keyword in product_type for keyword in SHOE_KEYWORDS)


def download_image(site, image_url):
    """Tai anh ve IMAGE_DIR/<site>, tra ve duong dan file (bo qua neu da co)."""
    folder = os.path.join(IMAGE_DIR, site)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, os.path.basename(image_url.split("?")[0]))
    if os.path.exists(path):
        return path
    response = get_with_retry(image_url)
    if response.status_code != 200:
        return ""
    with open(path, "wb") as f:
        f.write(response.content)
    return path


def option_values(product, name):
    # Ten option khac nhau giua cac shop (Màu sắc / Màu Sắc), nen so khong phan biet hoa thuong
    for option in product.get("options", []):
        if option["name"].lower() == name.lower():
            return option["values"]
    return []


def parse_product(site, base_url, product):
    variants = product.get("variants", [])
    prices = [float(v["price"]) for v in variants if v.get("price")]
    compare = [float(v["compare_at_price"]) for v in variants if v.get("compare_at_price")]
    images = [img["src"] for img in product.get("images", [])]
    main_image = images[0] if images else ""

    return {
        "site": site,
        "id": product["id"],
        "brand": product.get("vendor", ""),
        "name": product["title"],
        "product_type": product.get("product_type", ""),
        "price_vnd": int(min(prices)) if prices else "",
        "compare_at_price_vnd": int(max(compare)) if compare and max(compare) > 0 else "",
        "colors": "|".join(option_values(product, "Màu sắc")),
        "sizes": "|".join(option_values(product, "Kích thước")),
        "available": product.get("available", False),
        "url": f"{base_url}/products/{product['handle']}",
        "image_url": main_image,
        "image_path": download_image(site, main_image) if main_image else "",
        "image_urls": "|".join(images),
    }


def scrape_page(base_url, page_number):
    response = get_with_retry(
        f"{base_url}/collections/all/products.json",
        params={"limit": 250, "page": page_number},
    )
    if response.status_code != 200:
        return None
    return response.json().get("products", [])


def scrape_site(site, max_pages=None):
    base_url = SITES[site]
    results = []
    seen_ids = set()
    page = 1

    while max_pages is None or page <= max_pages:
        print(f"[{site}] Dang thu thap trang {page} ...")
        try:
            products = scrape_page(base_url, page)
        except requests.RequestException as e:
            print(f"[{site}] Loi mang, bo qua phan con lai: {e}")
            break
        if not products:
            break
        for product in products:
            if product["id"] in seen_ids or not is_shoe(product):
                continue
            seen_ids.add(product["id"])
            try:
                results.append(parse_product(site, base_url, product))
            except requests.RequestException as e:
                print(f"[{site}] Khong tai duoc anh san pham {product['id']}: {e}")
            time.sleep(0.2)  # lich su voi server khi tai anh
        page += 1
        time.sleep(1)

    print(f"[{site}] Thu thap duoc {len(results)} san pham giay")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("sites", nargs="*",
                        help=f"ten shop can crawl, trong {list(SITES)} (mac dinh: tat ca)")
    parser.add_argument("--max-pages", type=int, default=None)
    args = parser.parse_args()
    unknown = [s for s in args.sites if s not in SITES]
    if unknown:
        parser.error(f"shop khong hop le: {unknown}. Chon trong {list(SITES)}")

    output_file = OUTPUT_FILE.format(date=time.strftime("%Y-%m-%d"))
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    all_products = []
    for site in args.sites or SITES:
        all_products.extend(scrape_site(site, args.max_pages))

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_products)

    print(f"Da luu {len(all_products)} san pham vao {output_file}")


if __name__ == "__main__":
    main()
