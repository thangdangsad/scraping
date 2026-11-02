# Bài tập: Thu thập & làm sạch dữ liệu sản phẩm, so sánh BeautifulSoup vs Scrapy

## 1. Nguồn dữ liệu

Dùng **http://books.toscrape.com** — một website "sách" (đóng vai trò sản
phẩm thương mại điện tử) được dựng sẵn công khai để luyện tập web scraping,
không có điều khoản cấm crawl và không cần đăng nhập/captcha. Đây là lựa chọn
an toàn về mặt pháp lý/đạo đức thay vì scrape một sàn TMĐT thật (có thể vi
phạm ToS, bị chặn IP, hoặc dữ liệu thay đổi liên tục gây khó tái lập bài tập).

Mỗi trang catalogue liệt kê 20 sản phẩm gồm: tên, giá (GBP), tình trạng còn
hàng, số sao đánh giá (dạng chữ: One–Five). Tổng cộng 1000 sản phẩm / 51 trang.

## 2. Cấu trúc thư mục

```
Scraping/
├── bs4_scraper.py              # Thu thập bằng requests + BeautifulSoup
├── ecommerce_scraper/           # Project Scrapy
│   └── ecommerce_scraper/
│       ├── items.py             # Định nghĩa ProductItem
│       └── spiders/products_spider.py
├── clean_data.py                # Làm sạch dữ liệu CSV thô bằng pandas
├── data/
│   ├── raw_bs4.csv              # Kết quả thô từ BeautifulSoup
│   ├── raw_scrapy.csv           # Kết quả thô từ Scrapy
│   └── cleaned_products.csv     # Kết quả sau khi làm sạch
├── requirements.txt
└── README.md
```

## 3. Cách chạy

```bash
pip install -r requirements.txt

# Thu thập bằng BeautifulSoup
python3 bs4_scraper.py                     # -> data/raw_bs4.csv

# Thu thập bằng Scrapy
cd ecommerce_scraper
scrapy crawl products -O ../data/raw_scrapy.csv
cd ..

# Làm sạch dữ liệu (mặc định đọc data/raw_bs4.csv)
python3 clean_data.py data/raw_bs4.csv data/cleaned_products.csv
```

## 4. Các bước làm sạch dữ liệu (`clean_data.py`)

| Vấn đề trong dữ liệu thô | Cách xử lý |
|---|---|
| Khoảng trắng thừa quanh chuỗi | `.str.strip()` |
| Dòng trùng lặp | `drop_duplicates()` |
| Thiếu tên/giá | `dropna` + lọc chuỗi rỗng |
| Giá dạng chuỗi có ký hiệu tiền tệ (`£51.77`) | Regex bỏ ký tự không phải số/dấu chấm rồi ép kiểu `float` → cột `price_gbp` |
| Tình trạng kho dạng text tự do | Chuyển thành `in_stock` (bool) |
| Rating dạng chữ (`Three`) | Map sang số nguyên `rating_score` (1–5) |
| Giá trị bất thường (giá ≤ 0, rating không hợp lệ) | Lọc bỏ trước khi xuất |

Kết quả `cleaned_products.csv` có 4 cột: `name, price_gbp, in_stock,
rating_score` — sẵn sàng cho các bước phân tích (thống kê mô tả, group by...).

Lưu ý: khi viết `bs4_scraper.py`, ban đầu dùng `response.text` khiến ký hiệu
`£` bị lỗi encoding thành `Â£` (server không trả `charset` trong header
`Content-Type`, nên `requests` đoán nhầm ISO-8859-1). Đã sửa bằng cách đưa
`response.content` (bytes) cho `BeautifulSoup` để nó tự đọc `<meta
charset="utf-8">` trong HTML. Đây là một lỗi encoding rất phổ biến khi
scraping — nên luôn kiểm tra ký tự đặc biệt trong dữ liệu thu được.

## 5. So sánh BeautifulSoup vs Scrapy

Đo thực tế trên cùng bài toán (51 trang, 1000 sản phẩm, cùng `DOWNLOAD_DELAY`
≈ 1s để lịch sự với server):

| Tiêu chí | BeautifulSoup (+ requests) | Scrapy |
|---|---|---|
| Thời gian chạy thực tế | ~79 giây | ~62 giây |
| Số dòng code | ~55 dòng, 1 file | ~30 dòng spider + cấu trúc project có sẵn |
| Mô hình xử lý | Đồng bộ (tuần tự): tự viết vòng lặp `for` qua từng trang | Bất đồng bộ (Twisted reactor): tự động điều phối request, chỉ cần `response.follow()` |
| Điều hướng phân trang | Tự viết logic gọi `scrape_page()` lặp lại | Có sẵn cơ chế `yield response.follow(next_page)` |
| Xuất dữ liệu | Tự viết `csv.DictWriter` | Có sẵn Feed Exporter (`-O file.csv`, hỗ trợ cả JSON, XML...) |
| Tôn trọng robots.txt / throttle | Phải tự thêm `time.sleep()` | Có sẵn `ROBOTSTXT_OBEY`, `DOWNLOAD_DELAY`, `AutoThrottle` |
| Retry khi lỗi mạng | Không có, phải tự viết | Có sẵn middleware retry |
| Xử lý bất đồng bộ/song song nhiều domain | Khó, phải tự dùng `asyncio`/`threading` | Cơ chế lõi, cấu hình `CONCURRENT_REQUESTS` |
| Độ dốc học (learning curve) | Thấp — chỉ cần biết HTML + CSS selector | Cao hơn — cần hiểu project structure, spider, item, pipeline, settings |
| Phù hợp khi | Cào nhanh 1 trang/script nhỏ, học tập, xử lý dữ liệu cần logic Python tùy biến nhiều (vd. gọi thêm API khác giữa các bước) | Dự án crawl lớn, nhiều trang/nhiều domain, cần lặp lại định kỳ, cần pipeline xử lý/lưu dữ liệu chuẩn hóa |

### Nhận xét

- **BeautifulSoup** chỉ là thư viện *parse HTML* — phải tự kết hợp với
  `requests` để tải trang và tự viết toàn bộ vòng lặp, retry, lưu file. Ưu
  điểm là đơn giản, dễ đọc, phù hợp script nhỏ hoặc khi cần xử lý dữ liệu xen
  kẽ với logic Python phức tạp.
- **Scrapy** là một *framework* crawl hoàn chỉnh: có sẵn scheduler, downloader
  bất đồng bộ, middleware (retry, robots.txt, throttle), item pipeline, và
  feed exporter. Vì chạy bất đồng bộ và có cơ chế throttle/caching tối ưu hơn,
  Scrapy thường nhanh hơn và tiết kiệm code hơn khi crawl số lượng trang lớn,
  nhưng đòi hỏi thời gian làm quen với cấu trúc project ban đầu.
- Với bài tập quy mô nhỏ (1000 sản phẩm), cả hai đều đáp ứng tốt; sự khác
  biệt về tốc độ trong ví dụ này chủ yếu do độ trễ mạng/`DOWNLOAD_DELAY`, còn
  khác biệt thực sự nằm ở **khả năng mở rộng** và **hạ tầng có sẵn** khi dự án
  lớn dần (nhiều domain, cần resume, cần pipeline lưu DB...).
