import os
import glob
import csv
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNC_DIR = os.path.join(BASE_DIR, "SYNC")
OUTBOX_DIR = os.path.join(SYNC_DIR, "outbox")

def find_latest_products_csv():
    pattern = os.path.join(SYNC_DIR, "trm_products_*.csv")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def main():
    os.makedirs(OUTBOX_DIR, exist_ok=True)

    latest_csv = find_latest_products_csv()
    if not latest_csv:
        print("[HATA] SYNC klasorunde trm_products_*.csv bulunamadi.")
        return

    print(f"[INFO] Kullanilan urun dosyasi: {latest_csv}")

    today = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    out_path = os.path.join(OUTBOX_DIR, f"trm_posts_{today}.csv")

    with open(latest_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("[UYARI] Urun dosyasi bos.")
        return

    fieldnames = ["kategori", "text", "image_url", "product_link"]

    with open(out_path, "w", encoding="utf-8-sig", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            kategori = row.get("kategori", "")
            name = row.get("urun_adi", "")
            price = row.get("fiyat", "")
            link = row.get("urun_linki", "")
            img = row.get("resim_linki", "")

            text = (
                f"💥 {kategori.upper()} - {name}\n"
                f"💸 Fiyat: {price}\n"
                f"🛒 Siparis ve detay: {link}\n\n"
                f"Trend Ürünler Market avantajlı ürünler!"
            )

            writer.writerow({
                "kategori": kategori,
                "text": text,
                "image_url": img,
                "product_link": link
            })

    print(f"[OK] Toplam {len(rows)} adet posta hazirlandi:")
    print(out_path)

if __name__ == "__main__":
    main()
