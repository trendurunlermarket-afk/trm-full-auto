from telethon.sync import TelegramClient
import os

api_id = 21406034
api_hash = "c0c5a326621acf53d21a4a6e9c83a50f"
session_file = "Fahri_autobot"

client = TelegramClient(session_file, api_id, api_hash)

def main():
    print("🔹 Telegram bağlantısı başlatılıyor...")
    with client:
        dialogs = client.get_dialogs()
        print(f"🔹 {len(dialogs)} sohbet bulundu:")
        for d in dialogs:
            print(f"📂 {d.name}")
    print("✅ Veri çekimi tamamlandı!")

if __name__ == "__main__":
    main()
