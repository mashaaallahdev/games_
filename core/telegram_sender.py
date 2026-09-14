import os
from pathlib import Path
import requests
from core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_video_to_telegram(video_path: Path, caption: str, bot_token: str = None, chat_id: str = None) -> bool:
    """
    Uploads the rendered video and formatted caption to Telegram.
    Returns True on success, False otherwise.
    """
    token = bot_token or TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN", "")
    target_chat = chat_id or TELEGRAM_CHAT_ID or os.getenv("TELEGRAM_CHAT_ID", "")

    if not token or not target_chat:
        print("[Telegram] Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID. Video saved locally.")
        return False

    video_path = Path(video_path)
    if not video_path.exists():
        print(f"[Telegram] Video file not found: {video_path}")
        return False

    print(f"[Telegram] Uploading {video_path.name} to Telegram chat {target_chat}...")
    url = f"https://api.telegram.org/bot{token}/sendVideo"

    try:
        with open(video_path, "rb") as video_file:
            files = {
                "video": (video_path.name, video_file, "video/mp4")
            }
            data = {
                "chat_id": target_chat,
                "caption": caption,
                "supports_streaming": True
            }
            response = requests.post(url, data=data, files=files, timeout=120)
            result = response.json()

            if result.get("ok"):
                print("[Telegram] Video sent successfully! Check your phone!")
                return True
            else:
                print(f"[Telegram] API Error: {result.get('description', 'Unknown error')}")
                return False
    except Exception as e:
        print(f"[Telegram] Request failed: {e}")
        return False
