# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from dataclasses import dataclass


@dataclass
class ProductItem:
    name: str = None
    price: str = None
    availability: str = None
    rating: str = None
    image_urls: list = None  # ImagesPipeline doc danh sach URL nay de tai anh
    images: list = None  # ImagesPipeline ghi ket qua tai ve (url, path, checksum)
