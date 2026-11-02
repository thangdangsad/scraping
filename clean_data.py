"""
Bai tap: Lam sach du lieu san pham truoc khi phan tich.

Doc file CSV tho (thu thap boi BeautifulSoup hoac Scrapy), chuan hoa kieu du
lieu va luu ra file CSV da lam sach, san sang cho buoc phan tich.

Cach chay:
    python3 clean_data.py [duong_dan_file_input] [duong_dan_file_output]

Mac dinh: input = data/raw_bs4.csv, output = data/cleaned_products.csv
"""

import sys

import pandas as pd

RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Loai bo khoang trang thua o cac cot dang chuoi
    for col in ["name", "price", "availability", "rating"]:
        df[col] = df[col].astype(str).str.strip()

    # 2. Loai bo dong trung lap va dong thieu du lieu quan trong (name/price)
    df = df.drop_duplicates()
    df = df.dropna(subset=["name", "price"])
    df = df[(df["name"] != "") & (df["price"] != "")]

    # 3. Chuan hoa gia: bo ky hieu tien te, ep kieu float
    df["price_gbp"] = (
        df["price"].str.replace(r"[^\d.]", "", regex=True).astype(float)
    )

    # 4. Chuan hoa tinh trang con hang thanh kieu boolean
    df["in_stock"] = df["availability"].str.contains("In stock", case=False, na=False)

    # 5. Chuyen danh gia sao tu chu sang so (1-5)
    df["rating_score"] = df["rating"].map(RATING_WORDS)

    # 6. Loai bo cac dong co gia tri bat thuong (gia <= 0 hoac rating khong hop le)
    df = df[df["price_gbp"] > 0]
    df = df.dropna(subset=["rating_score"])
    df["rating_score"] = df["rating_score"].astype(int)

    df = df.reset_index(drop=True)
    return df[["name", "price_gbp", "in_stock", "rating_score"]]


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw_bs4.csv"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "data/cleaned_products.csv"

    raw_df = pd.read_csv(input_path)
    print(f"Du lieu tho: {len(raw_df)} dong")

    cleaned_df = clean(raw_df)
    print(f"Du lieu sau khi lam sach: {len(cleaned_df)} dong")

    cleaned_df.to_csv(output_path, index=False)
    print(f"Da luu du lieu sach vao {output_path}")

    print("\n--- Thong ke nhanh sau khi lam sach ---")
    print(cleaned_df["price_gbp"].describe())
    print("\nSo luong san pham theo rating_score:")
    print(cleaned_df["rating_score"].value_counts().sort_index())
    print(f"\nTi le con hang: {cleaned_df['in_stock'].mean():.2%}")


if __name__ == "__main__":
    main()
