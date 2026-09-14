# 🎮 Autonomous Facebook Reels Game Automation (3 Games)

A 100% free, fully automated short-form game video generation engine built for Facebook Reels monetization. Generates high-retention 9:16 vertical 1080x1920 60 FPS videos, synthesizes dynamic collision audio, generates viral engagement captions with hashtags, and sends ready-to-post videos straight to Telegram.

---

## 🌟 The 3 Games & Target Pages

| Game | Viral Hook / Psychology | Best Suited For | Target FB Page |
| :--- | :--- | :--- | :--- |
| **1. Neon Escape** | Hypnotic ball bouncing inside rotating breakable rings. Viewers stay to see if it breaks out. | High watch-time, loops | *"Oddly Satisfying Games"* |
| **2. Marble Arena** | 8 colored marbles race down through pegs and hazard wheels into an elimination finish line. | Comment wars ("Pick your color!") | *"Mini Tournament Hub"* |
| **3. Plinko Multiplier** | 1 ball drops into multiplier gates (`x2`, `x5`), splitting into 300+ balls pulverizing numbered brick walls. | Visual ASMR, exponential chaos | *"Extreme Physics ASMR"* |

---

## 🚀 Quick Start (Local Run)

### 1. Test Generate a Video Locally
Generate a 10-second test video:
```bash
python pipeline.py --game neon_escape --duration 10 --preview
```
Replace `--game` with `marble_arena` or `plinko_multiplier`.

### 2. Generate a Full Batch for All 3 Pages
```bash
python dispatcher.py --mode all --duration 30
```
All generated videos are saved into the `output/` folder.

---

## 📱 Telegram Delivery Setup (100% Free)

To get videos delivered directly to your phone:

1. Open Telegram and search for `@BotFather`.
2. Send `/newbot`, choose a name and username. BotFather will give you a **Bot Token** (e.g. `123456:ABC-DEF...`).
3. Search for `@userinfobot` on Telegram and press `/start`. It will reply with your **Id** (Chat ID).
4. Create a `.env` file in the project root (copy from `.env.example`):
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```
5. Test sending to your phone:
   ```bash
   python pipeline.py --game neon_escape --duration 10 --send-telegram
   ```

---

## ☁️ 24/7 Cloud Deployment (No PC Needed!)

With **GitHub Actions**, you don't even need to leave your computer turned on. The cloud runs 4 times every day on schedule:

1. **Initialize Git & Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of autonomous reels engine"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

2. **Add Telegram Secrets to GitHub**:
   - Go to your GitHub repository -> **Settings** -> **Secrets and variables** -> **Actions**.
   - Click **New repository secret**:
     - `TELEGRAM_BOT_TOKEN` = (Your BotFather token)
     - `TELEGRAM_CHAT_ID` = (Your Chat ID)

3. **That's It!**
   - The workflow `.github/workflows/daily_reels.yml` will automatically run **4 times a day** (03:00, 09:00, 15:00, 21:00 UTC).
   - You can also open the **GitHub Mobile App** on your phone at any time, tap **Actions** -> **Run workflow**, and generate an extra video on demand!
