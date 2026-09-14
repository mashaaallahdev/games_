import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pipeline import run_pipeline
from core.config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    DEFAULT_DURATION
)

# Optional separate Telegram channel IDs per page
CHAT_ID_GAME1 = os.getenv("TELEGRAM_CHAT_ID_PAGE1", TELEGRAM_CHAT_ID)
CHAT_ID_GAME2 = os.getenv("TELEGRAM_CHAT_ID_PAGE2", TELEGRAM_CHAT_ID)
CHAT_ID_GAME3 = os.getenv("TELEGRAM_CHAT_ID_PAGE3", TELEGRAM_CHAT_ID)

GAMES_CONFIG = [
    {
        "name": "neon_escape",
        "page_label": "PAGE 1: Oddly Satisfying Games",
        "chat_id": CHAT_ID_GAME1
    },
    {
        "name": "marble_arena",
        "page_label": "PAGE 2: Mini Tournament Hub",
        "chat_id": CHAT_ID_GAME2
    },
    {
        "name": "plinko_multiplier",
        "page_label": "PAGE 3: Extreme Physics ASMR",
        "chat_id": CHAT_ID_GAME3
    }
]

def dispatch_single(game_cfg, duration=DEFAULT_DURATION, send_telegram=True):
    print(f"\n>>> Dispatching {game_cfg['name'].upper()} for {game_cfg['page_label']} <<<")
    # Temporarily set active chat id
    os.environ["TELEGRAM_CHAT_ID"] = game_cfg["chat_id"]
    return run_pipeline(
        game_name=game_cfg["name"],
        duration=duration,
        send_telegram=send_telegram
    )

def main():
    parser = argparse.ArgumentParser(description="Multi-Game Reels Dispatcher")
    parser.add_argument(
        "--mode",
        type=str,
        default="all",
        choices=["all", "cycle", "neon_escape", "marble_arena", "plinko_multiplier"],
        help="Run all 3 games, cycle based on hour, or run a specific game"
    )
    parser.add_argument("--duration", type=int, default=30, help="Duration in seconds (default 30)")
    parser.add_argument("--no-telegram", action="store_true", help="Skip sending to Telegram")

    args = parser.parse_args()
    send_tg = not args.no_telegram

    if args.mode == "all":
        print("🚀 RUNNING BATCH DISPATCH FOR ALL 3 FACEBOOK PAGES...")
        for cfg in GAMES_CONFIG:
            dispatch_single(cfg, duration=args.duration, send_telegram=send_tg)
    elif args.mode == "cycle":
        # Cycle through games based on hour of day (e.g. 4 times a day)
        current_hour = datetime.utcnow().hour
        cycle_idx = (current_hour // 6) % len(GAMES_CONFIG)
        cfg = GAMES_CONFIG[cycle_idx]
        print(f"⏰ Cron Cycle Triggered at UTC hour {current_hour}: Selected {cfg['name']}")
        dispatch_single(cfg, duration=args.duration, send_telegram=send_tg)
    else:
        # Run specific game
        matched = [c for c in GAMES_CONFIG if c["name"] == args.mode]
        if matched:
            dispatch_single(matched[0], duration=args.duration, send_telegram=send_tg)
        else:
            print(f"Unknown game: {args.mode}")

if __name__ == "__main__":
    main()
