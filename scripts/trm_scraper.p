import os
import csv
import datetime
import requests
from bs4 import BeautifulSoup
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "trm_categories.yaml")
SYNC_DIR = os.path.join(BASE_DIR, "SYNC")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def fetch_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text

def parse_products(html, category_name):
    soup = BeautifulSoup(html, "html.parser")
    products = []

    # Bu kısım site tasarımına göre değişebilir;
    # ilk deneme için yaygın kullanılan bazı sınıfları tarıyoruz.
    candidates = soup.select(".productItem, .product-item, .product-list .item, .urunItem, .product")

    for item in candidates:
        name_el = item.select_one("a.productName, .product-name, .urunAdi, h3, h2")
        price_el = item.select_one(".productPrice, .newPrice, .fiyat, .price")

        if not name_el or not price_el:
            continue

        name = name_el.get_text(strip=True)
        price = price_el.get_text(strip=True)

        link = ""
        img = ""

        a_tag = item.find("a", href=True)
        if a_tag:
            link = a_tag["href"]
            if link.startswith("/"):
                link = "https://www.trendurunlermarket.com" + link

        img_tag = item.find("img")
        if img_tag and img_tag.get("src"):
            img = img_tag["src"]
            if img.startswith("/"):
                img = "https://www.trendurunlermarket.com" + img

        products.append({
            "kategori": category_name,
            "urun_adi": name,
            "fiyat_yazi": price,
            "urun_linki": link,
            "resim_linki": img,
        })

    return products

def main():
    os.makedirs(SYNC_DIR, exist_ok=True)

    cfg = load_config()
    categories = cfg.get("categories", {})
    max_per_cat = int(cfg.get("max_products_per_category", 30))

    all_products = []

    for cat_name, url in categories.items():
        print(f"[INFO] Kategori taraniyor: {cat_name} -> {url}")
        try:
            html = fetch_html(url)
            products = parse_products(html, cat_name)
            if max_per_cat > 0:
                products = products[:max_per_cat]
            print(f"[INFO] {cat_name} icin bulunan urun sayisi: {len(products)}")
            all_products.extend(products)
        except Exception as e:
            print(f"[HATA] {cat_name} kategorisi cekilirken sorun: {e}")

    if not all_products:
        print("[UYARI] Hic urun bulunamadi. Muhtemelen HTML secicileri degistirmek gerekir.")
        return

    today = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    out_path = os.path.join(SYNC_DIR, f"trm_products_{today}.csv")

    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["kategori", "urun_adi", "fiyat_yazi", "urun_linki", "resim_linki"]
        )
        writer.writeheader()
        writer.writerows(all_products)

    print(f"[OK] Toplam {len(all_products)} urun SYNC klasorune yazildi:")
    print(out_path)

if __name__ == "__main__":
    main()
