# Bài tập: Thu thập & làm sạch dữ liệu sản phẩm, so sánh BeautifulSoup vs Scrapy

## 1. Nguồn dữ liệu

Dùng **http://books.toscrape.com** — một website "sách" (đóng vai trò sản
phẩm thương mại điện tử) được dựng sẵn công khai để luyện tập web scraping,
không có điều khoản cấm crawl và không cần đăng nhập/captcha. Đây là lựa chọn
an toàn về mặt pháp lý/đạo đức thay vì scrape một sàn TMĐT thật (có thể vi
phạm ToS, bị chặn IP, hoặc dữ liệu thay đổi liên tục gây khó tái lập bài tập).

Mỗi trang catalogue liệt kê 20 sản phẩm gồm: tên, giá (GBP), tình trạng còn
hàng, số sao đánh giá (dạng chữ: One–Five). Tổng cộng 1000 sản phẩm / 51 trang.

Ngoài ra có thêm bài thực tế: thu thập **giày từ nhiều website bán giày Việt
Nam** (xem mục 6).

## 2. Cấu trúc thư mục

```
Scraping/
├── bs4_scraper.py              # Thu thập sách bằng requests + BeautifulSoup (kèm ảnh bìa)
├── shoes_scraper.py            # Thu thập giày từ nhiều shop Việt Nam (kèm ảnh)
├── ecommerce_scraper/           # Project Scrapy
│   └── ecommerce_scraper/
│       ├── items.py             # Định nghĩa ProductItem
│       ├── settings.py          # Bật ImagesPipeline, IMAGES_STORE
│       └── spiders/products_spider.py
├── clean_data.py                # Làm sạch dữ liệu CSV thô bằng pandas
├── data/                        # Tự tạo khi chạy scraper
│   ├── raw_bs4.csv              # Kết quả thô từ BeautifulSoup
│   ├── raw_scrapy.csv           # Kết quả thô từ Scrapy
│   ├── cleaned_products.csv     # Kết quả sau khi làm sạch
│   ├── raw_shoes_<ngày>.csv     # Kết quả giày, mỗi ngày một file
│   ├── images/                  # Ảnh bìa sách (BeautifulSoup; Scrapy lưu ở images/full/)
│   └── images_shoes/<shop>/     # Ảnh giày theo từng shop
├── requirements.txt
└── README.md
```

## 3. Cách chạy

### 3.1 Cài đặt (dùng virtual environment)

Ubuntu/Debian chặn `pip install` vào Python hệ thống (lỗi
`externally-managed-environment`), nên cần tạo venv:

```bash
sudo apt install python3-venv      # chỉ cần nếu máy chưa có
python3 -m venv .venv
source .venv/bin/activate          # mỗi lần mở terminal mới phải chạy lại lệnh này
pip install -r requirements.txt
```

Dấu hiệu venv đang bật: prompt có thêm `(.venv)` ở đầu. Nếu gặp
`ModuleNotFoundError: No module named 'bs4'` nghĩa là chưa bật venv hoặc chưa
cài thư viện.

### 3.2 Thu thập sách (có ảnh bìa)

```bash
# Thu thập bằng BeautifulSoup
python3 bs4_scraper.py                     # -> data/raw_bs4.csv + data/images/

# Thu thập bằng Scrapy (ảnh tải qua ImagesPipeline, cần Pillow)
cd ecommerce_scraper
scrapy crawl products -O ../data/raw_scrapy.csv    # -> ../data/images/full/
cd ..

# Làm sạch dữ liệu (mặc định đọc data/raw_bs4.csv)
python3 clean_data.py data/raw_bs4.csv data/cleaned_products.csv
```

CSV của BeautifulSoup có thêm cột `image_url`, `image_path`; CSV của Scrapy có
thêm `image_urls`, `images`. `clean_data.py` chỉ giữ 4 cột cũ nên không đưa cột
ảnh vào `cleaned_products.csv`.

### 3.3 Thu thập giày (nhiều shop)

```bash
python3 shoes_scraper.py                 # tất cả shop
python3 shoes_scraper.py crocs biti      # chỉ một số shop
python3 shoes_scraper.py --max-pages 2   # giới hạn số trang mỗi shop (chạy thử nhanh)
```

Crawl đầy đủ mất vài chục phút vì phải tải hàng nghìn ảnh.

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

## 6. Thu thập giày từ các website Việt Nam (`shoes_scraper.py`)

Các shop dưới đây chạy trên Haravan/Shopify, có endpoint JSON công khai
`/collections/all/products.json` và `robots.txt` cho phép crawl `/collections`,
`/products`. Dùng JSON nên không cần parse HTML và ít hỏng khi giao diện đổi.

| Key | Website | Ghi chú |
|---|---|---|
| `biti` | bitis.com.vn | Biti's, Hunter, Êmbrace |
| `crocs` | crocs.com.vn | Clogs, sandal, dép |
| `supersports` | supersports.com.vn | Nhiều hãng (Nike, Adidas, Hoka...) |
| `sneakerbuzz` | sneakerbuzz.vn | Chỉ có vài mẫu dép |

**Cột trong `data/raw_shoes_<YYYY-MM-DD>.csv`:** `site, id, brand, name,
product_type, price_vnd, compare_at_price_vnd, colors, sizes, available, url,
image_url, image_path, image_urls`.

- `price_vnd` là giá thấp nhất trong các biến thể; `colors`, `sizes`,
  `image_urls` nối nhiều giá trị bằng dấu `|`.
- Chỉ giữ sản phẩm có `product_type` là giày/dép (các shop bán lẫn áo, balo, túi).
- Ảnh đại diện lưu ở `data/images_shoes/<shop>/`; ảnh đã có thì bỏ qua, không tải lại.

**Ghi đè dữ liệu:** mỗi ngày một file CSV nên chạy khác ngày không mất dữ
liệu cũ (dùng để so sánh giá theo thời gian). Chạy lại *trong cùng một ngày*
sẽ ghi đè file của ngày đó, và chạy một vài shop thì file chỉ chứa các shop
đó. Thư mục ảnh không bị ghi đè.

**Lịch sự với server:** có `sleep` giữa các request; nếu gặp HTTP 429 (giới
hạn tốc độ) hoặc lỗi 5xx, scraper tự chờ rồi thử lại tối đa 5 lần. Một shop
lỗi không làm dừng các shop khác.

**Thêm shop mới:** kiểm tra `https://<domain>/robots.txt` có cho crawl
không và `https://<domain>/collections/all/products.json` có trả JSON không,
rồi thêm một dòng vào dict `SITES` trong `shoes_scraper.py`.

Dữ liệu và ảnh thuộc về các thương hiệu; chỉ dùng cho mục đích học tập, không
đăng lại thương mại.
