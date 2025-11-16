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

    # Her ürün için h2.name etiketlerini kullanıyoruz
    for name_el in soup.select("h2.name"):
        name = name_el.get_text(strip=True)

        # En yakın li atasını bul
        li = name_el
        while li is not None and li.name != "li":
            li = li.parent
        if li is None:
            continue

        # Fiyat: li içindeki "TL" geçen ilk metin
        price = ""
        for txt in li.stripped_strings:
            t = txt.strip()
            if "TL" in t:
                price = t
                break

        # Ürün linki: li içindeki ilk a[href]
        link = ""
        a_tag = li.find("a", href=True)
        if a_tag:
            link = a_tag["href"]
            if link.startswith("/"):
                link = "https://www.trendurunlermarket.com" + link

        # Resim linki: li içindeki ilk img[src]
        img = ""
        img_tag = li.find("img", src=True)
        if img_tag:
            img = img_tag["src"]
            if img.startswith("/"):
                img = "https://www.trendurunlermarket.com" + img

        products.append({
            "kategori": category_name,
            "urun_adi": name,
            "fiyat": price,
            "urun_linki": link,
            "resim_linki": img
        })

    return products

def main():
    os.makedirs(SYNC_DIR, exist_ok=True)

    cfg = load_config()
    categories = cfg.get("categories", {})
    max_per_cat = int(cfg.get("max_products_per_category", 30))

    all_products = []

    print("TRM kategorilerinden urunler cekiliyor...")

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
        print("[UYARI] Hic urun bulunamadi. Seciciler guncellenmeli.")
        return

    today = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    out_path = os.path.join(SYNC_DIR, f"trm_products_{today}.csv")

    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["kategori", "urun_adi", "fiyat", "urun_linki", "resim_linki"]
        )
        writer.writeheader()
        writer.writerows(all_products)

    print(f"[OK] Toplam {len(all_products)} urun yazildi:")
    print(out_path)

if __name__ == "__main__":
    main()
