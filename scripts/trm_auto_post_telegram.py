import os
import csv
import glob
import json
import requests
import datetime
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "post_config.yaml")
SYNC_DIR = os.path.join(BASE_DIR, "SYNC")
OUTBOX_DIR = os.path.join(SYNC_DIR, "outbox")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def find_latest_posts_csv():
    pattern = os.path.join(OUTBOX_DIR, "trm_posts_*.csv")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def load_state(path):
    if not os.path.exists(path):
        return {"last_index": -1}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(path, state):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def send_post(bot_token, chat_id, text, image_url=None):
    base_url = f"https://api.telegram.org/bot{bot_token}"
    if image_url:
        url = f"{base_url}/sendPhoto"
        data = {
            "chat_id": chat_id,
            "caption": text,
            "parse_mode": "HTML"
        }
        data["photo"] = image_url
    else:
        url = f"{base_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
    resp = requests.post(url, data=data, timeout=30)
    resp.raise_for_status()

def main():
    cfg = load_config()
    bot_token = cfg["bot_token"]
    chat_id = cfg["post_chat"]
    posts_per_run = int(cfg.get("posts_per_run", 5))
    state_file = cfg.get("state_file", "post_state.json")

    os.makedirs(OUTBOX_DIR, exist_ok=True)
    state_path = os.path.join(OUTBOX_DIR, state_file)

    posts_csv = find_latest_posts_csv()
    if not posts_csv:
        print("[HATA] OUTBOX klasorunde trm_posts_*.csv bulunamadi.")
        return

    print(f"[INFO] Kullanilan posta dosyasi: {posts_csv}")

    with open(posts_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        posts = list(reader)

    if not posts:
        print("[UYARI] Posta dosyasi bos.")
        return

    state = load_state(state_path)
    last_index = state.get("last_index", -1)

    start = last_index + 1
    end = min(start + posts_per_run, len(posts))

    if start >= len(posts):
        print("[INFO] Tum postalar gonderilmis, bastan almak istersen state dosyasini sil.")
        return

    print(f"[INFO] Bu kosumda gonderilecek post index araligi: {start} - {end-1}")

    sent = 0
    for i in range(start, end):
        p = posts[i]
        text = p.get("text", "")
        image_url = p.get("image_url") or None

        try:
            send_post(bot_token, chat_id, text, image_url=image_url)
            sent += 1
            print(f"[OK] {i}. posta gonderildi.")
        except Exception as e:
            print(f"[HATA] {i}. posta gonderilemedi: {e}")

    state["last_index"] = start + sent - 1
    save_state(state_path, state)

    print(f"[INFO] Bu kosumda gonderilen toplam posta: {sent}")

if __name__ == "__main__":
    main()
