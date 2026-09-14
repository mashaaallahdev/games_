import argparse
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Ensure UTF-8 output in Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from core.config import OUTPUT_DIR, DEFAULT_DURATION
from core.caption_generator import generate_caption
from core.telegram_sender import send_video_to_telegram
from games.neon_escape import NeonEscapeGame

def run_pipeline(game_name="neon_escape", duration=DEFAULT_DURATION, send_telegram=False, preview=False):
    print("=" * 60)
    print(f"🎬 STARTING AUTOMATED REELS PIPELINE: {game_name.upper()}")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{game_name}_{timestamp}.mp4"
    output_path = OUTPUT_DIR / output_filename

    start_time = time.time()

    # 1. Generate Game Video
    if game_name == "neon_escape":
        game = NeonEscapeGame(duration_sec=duration)
        video_file = game.generate_video(output_path)
    elif game_name == "marble_arena":
        from games.marble_arena import MarbleArenaGame
        game = MarbleArenaGame(duration_sec=duration)
        video_file = game.generate_video(output_path)
    elif game_name == "plinko_multiplier":
        from games.plinko_multiplier import PlinkoMultiplierGame
        game = PlinkoMultiplierGame(duration_sec=duration)
        video_file = game.generate_video(output_path)
    else:
        raise ValueError(f"Unknown game name: {game_name}")

    elapsed = time.time() - start_time
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ Video generated in {elapsed:.1f}s | Size: {file_size_mb:.2f} MB")
    print(f"📁 Path: {output_path}")

    # 2. Generate Caption & Hashtags
    caption = generate_caption(game_type=game_name)
    print("\n" + "-" * 40)
    print("📝 GENERATED CAPTION & HASHTAGS:")
    print("-" * 40)
    print(caption)
    print("-" * 40)

    # 3. Deliver to Telegram (if requested)
    if send_telegram:
        print("\n🚀 Sending video and caption to Telegram...")
        success = send_video_to_telegram(output_path, caption)
        if success:
            print("🎉 Video successfully delivered to Telegram!")
        else:
            print("⚠️ Telegram delivery skipped or failed (check .env settings).")

    # 4. Open preview locally (if requested)
    if preview and sys.platform == "win32":
        print(f"\n🎥 Opening preview for: {output_path.name}")
        os.startfile(str(output_path))

    print("\n🏁 Pipeline run complete!")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Facebook Reels Automation Pipeline")
    parser.add_argument("--game", type=str, default="neon_escape", choices=["neon_escape", "marble_arena", "plinko_multiplier"], help="Game to generate")
    parser.add_argument("--duration", type=int, default=15, help="Video duration in seconds")
    parser.add_argument("--send-telegram", action="store_true", help="Send the video to Telegram")
    parser.add_argument("--preview", action="store_true", help="Automatically open preview on desktop")

    args = parser.parse_args()
    run_pipeline(game_name=args.game, duration=args.duration, send_telegram=args.send_telegram, preview=args.preview)
