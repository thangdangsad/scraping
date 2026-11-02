"""
Bai tap: Thu thap danh sach san pham bang Scrapy
Nguon du lieu: http://books.toscrape.com (website mo, duoc dung rieng de luyen scraping)

Cach chay (trong thu muc ecommerce_scraper):
    scrapy crawl products -O ../data/raw_scrapy.csv
Anh duoc luu vao data/images/ (qua ImagesPipeline, can cai Pillow).
"""

import scrapy

from ecommerce_scraper.items import ProductItem


class ProductsSpider(scrapy.Spider):
    name = "products"
    start_urls = ["http://books.toscrape.com/catalogue/page-1.html"]

    def parse(self, response):
        for article in response.css("article.product_pod"):
            yield ProductItem(
                name=article.css("h3 a::attr(title)").get(),
                price=article.css("p.price_color::text").get(default="").strip(),
                availability=" ".join(
                    article.css("p.instock.availability::text").getall()
                ).strip(),
                rating=(article.css("p.star-rating::attr(class)").get() or "").replace(
                    "star-rating ", ""
                ),
                image_urls=[
                    response.urljoin(article.css("img.thumbnail::attr(src)").get())
                ],
            )

        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
