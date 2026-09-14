import random

GAME_CAPTION_TEMPLATES = {
    "neon_escape": {
        "hooks": [
            "Wait for the last 5 seconds... Did not expect that! 😱⚡",
            "This is oddly satisfying to watch on loop 🤤✨",
            "Can it actually break the final layer? Watch closely! 🎯",
            "Turn your sound on for pure ASMR chills 🎧🔊",
            "Only 1% of people can look away before it escapes! 🔥",
            "Watch until it breaks out... Pure satisfaction! 💥",
            "Rate this breakout from 1 to 10 in the comments! 👇",
            "The tension in the last 10 seconds is unreal ⚡🤯"
        ],
        "questions": [
            "What color ring should we try next? Drop it below! 👇",
            "Did you think it was going to escape? Be honest! 😂",
            "How many bounces did it take? Count if you can! 🔢",
            "Drop a 🟢 if you watched till the final breakout!"
        ],
        "hashtags": [
            "#satisfying", "#oddlysatisfying", "#reels", "#fyp", "#viral",
            "#gaming", "#asmr", "#neon", "#satisfyingvideo", "#physics",
            "#loop", "#relaxing", "#fbreels", "#trending", "#videogames"
        ]
    },
    "marble_arena": {
        "hooks": [
            "Pick your color NOW before the race ends! 🏁🎯",
            "Which color will survive the final elimination? 🏆⚡",
            "The comeback at the end was INSANE! 😱🔥",
            "Who are you rooting for? Comment your pick! 👇",
            "This obstacle course shows zero mercy! 💀🛑",
            "Did your favorite color win or get knocked out? 🥊"
        ],
        "questions": [
            "Which color did you choose? Let me know in the comments! 💬",
            "Who had the biggest clutch moment in this round? 👑",
            "Tell me your favorite color and see if it wins next time! ✨"
        ],
        "hashtags": [
            "#marblerace", "#elimination", "#gaming", "#reels", "#fbreels",
            "#tournament", "#viral", "#fyp", "#competition", "#physics",
            "#challenge", "#gamereels", "#predict", "#whowins"
        ]
    },
    "plinko_multiplier": {
        "hooks": [
            "Wait for the x10 multiplier flood... Absolute chaos! 🤯💣",
            "From 1 ball to 1,000 in 15 seconds! Pure ASMR 🤤✨",
            "Can the multiplier break the final boss block? 🧱💥",
            "Listen to that satisfying particle destruction 🎧🔊",
            "Watch the numbers explode! Exponential growth is crazy 📈🔥"
        ],
        "questions": [
            "What was the highest multiplier hit? Comment below! 👇",
            "Is there anything more satisfying than this? 🤤",
            "Drop a 🔥 if you love exponential growth games!"
        ],
        "hashtags": [
            "#plinko", "#satisfying", "#asmr", "#oddlysatisfying", "#reels",
            "#viral", "#gaming", "#exponential", "#physics", "#fbreels",
            "#trending", "#particlefx", "#satisfyingvideo"
        ]
    }
}

def generate_caption(game_type: str = "neon_escape") -> str:
    """
    Generates a viral Facebook Reel caption including hook, engagement question,
    and optimized hashtags tailored to the specific game.
    """
    data = GAME_CAPTION_TEMPLATES.get(game_type, GAME_CAPTION_TEMPLATES["neon_escape"])
    hook = random.choice(data["hooks"])
    question = random.choice(data["questions"])
    
    # Pick 8-12 randomized hashtags for variety
    selected_tags = random.sample(data["hashtags"], min(10, len(data["hashtags"])))
    tags_str = " ".join(selected_tags)

    caption = f"{hook}\n\n{question}\n\n.\n.\n.\n{tags_str}"
    return caption
