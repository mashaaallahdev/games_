import math
import random
import numpy as np
import pygame
from pathlib import Path
from core.config import VIDEO_WIDTH, VIDEO_HEIGHT, FPS
from core.audio_synth import ProceduralAudioEngine
from core.video_renderer import VideoRenderer
from games.marble_arena import COUNTRY_DATABASE, render_flag_surface

# ==============================================================================
# PARTICLES & FLOATING UI EFFECTS
# ==============================================================================
class Spark:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        ang = random.uniform(0, 2 * math.pi)
        spd = random.uniform(2, 9)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd
        self.life = 1.0
        self.decay = random.uniform(0.025, 0.06)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.life -= self.decay

    def draw(self, surf):
        if self.life > 0:
            alpha = int(self.life * 255)
            r, g, b = self.color
            s = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(s, (r, g, b, alpha), (4, 4), 4)
            surf.blit(s, (int(self.x - 4), int(self.y - 4)))


class FloatingText:
    def __init__(self, x, y, text, color=(255, 220, 0), font_size=28):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 1.0
        self.decay = 0.035
        self.font = pygame.font.SysFont("Arial", font_size, bold=True)

    def update(self):
        self.y -= 1.8
        self.life -= self.decay

    def draw(self, surf):
        if self.life > 0:
            alpha = int(self.life * 255)
            r, g, b = self.color
            txt_surf = self.font.render(self.text, True, (r, g, b))
            txt_surf.set_alpha(alpha)
            surf.blit(txt_surf, txt_surf.get_rect(center=(int(self.x), int(self.y))))


# ==============================================================================
# BALL & TARGET COUNTRY BLOCK CLASSES
# ==============================================================================
class CountryBall:
    def __init__(self, country: dict, x: float, y: float, vx: float = 0.0, vy: float = 0.0, radius: int = 11):
        self.country = country
        self.name = country["name"]
        self.code = country["code"]
        self.color = country["primary"]
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.radius = radius
        self.alive = True
        self.flag_surf = render_flag_surface(country, radius)

    def update(self):
        self.vy += 0.26  # Gravity
        self.vx *= 0.995
        self.vy *= 0.995
        self.x += self.vx
        self.y += self.vy

    def draw(self, surf):
        # Draw circular flag marble
        surf.blit(self.flag_surf, (int(self.x - self.radius), int(self.y - self.radius)))
        pygame.draw.circle(surf, (255, 255, 255), (int(self.x), int(self.y)), self.radius, 1)


class CountryBlock:
    """Bottom chamber target block representing one of the 5 drafted countries."""
    def __init__(self, country: dict, x: int, y: int, w: int, h: int, max_hp: int = 80):
        self.country = country
        self.name = country["name"]
        self.code = country["code"]
        self.color = country["primary"]
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.max_hp = max_hp
        self.hp = max_hp
        self.alive = True
        self.flash_timer = 0
        self.flag_surf = render_flag_surface(country, radius=24)
        self.font_code = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_hp = pygame.font.SysFont("Arial", 22, bold=True)

    def hit(self, dmg: int = 2) -> bool:
        self.hp = max(0, self.hp - dmg)
        self.flash_timer = 8
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def update(self):
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def draw(self, surf):
        is_lit = self.flash_timer > 0
        border_col = (255, 255, 255) if is_lit else self.color

        # Background chamber
        bg_col = (20, 24, 45) if self.alive else (10, 10, 18)
        pygame.draw.rect(surf, bg_col, (self.x, self.y, self.w, self.h), border_radius=16)
        pygame.draw.rect(surf, border_col, (self.x, self.y, self.w, self.h), width=4 if is_lit else 2, border_radius=16)

        if self.alive:
            # Top flag icon
            flag_x = self.x + (self.w - 48) // 2
            flag_y = self.y + 16
            surf.blit(self.flag_surf, (flag_x, flag_y))

            # Country Code
            code_txt = self.font_code.render(self.code, True, (255, 255, 255))
            surf.blit(code_txt, code_txt.get_rect(center=(self.x + self.w // 2, self.y + 85)))

            # HP Progress Bar
            hp_ratio = self.hp / self.max_hp
            bar_w = self.w - 28
            bar_h = 16
            bar_x = self.x + 14
            bar_y = self.y + 115

            pygame.draw.rect(surf, (35, 40, 65), (bar_x, bar_y, bar_w, bar_h), border_radius=8)
            # HP fill in country's primary color
            fill_w = max(4, int(bar_w * hp_ratio))
            pygame.draw.rect(surf, self.color, (bar_x, bar_y, fill_w, bar_h), border_radius=8)
            pygame.draw.rect(surf, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=8)

            # HP Text
            hp_txt = self.font_hp.render(f"{self.hp} HP", True, (255, 255, 255))
            surf.blit(hp_txt, hp_txt.get_rect(center=(self.x + self.w // 2, self.y + 150)))
        else:
            # Destroyed State
            dest_txt = self.font_code.render("DESTROYED!", True, (255, 60, 80))
            surf.blit(dest_txt, dest_txt.get_rect(center=(self.x + self.w // 2, self.y + self.h // 2)))


# ==============================================================================
# PLINKO MULTIPLIER GAME CONTROLLER
# ==============================================================================
class PlinkoMultiplierGame:
    def __init__(self, duration_sec=30, width=VIDEO_WIDTH, height=VIDEO_HEIGHT, fps=FPS):
        pygame.init()
        self.width = width
        self.height = height
        self.fps = fps
        self.duration_sec = duration_sec
        self.total_frames = int(duration_sec * fps)

        # 1. Draft 5 Random Nations
        self.selected_countries = random.sample(COUNTRY_DATABASE, 5)
        print(f"[PlinkoMultiplier] Drafted 5 Countries: {[c['code'] for c in self.selected_countries]}")

        # 2. Build Bottom Country Blocks
        self.blocks = []
        block_w = 175
        block_h = 180
        total_blocks_w = 5 * block_w + 4 * 16
        start_x = (self.width - total_blocks_w) // 2
        block_y = 1460

        for i, country in enumerate(self.selected_countries):
            bx = start_x + i * (block_w + 16)
            self.blocks.append(CountryBlock(country, bx, block_y, block_w, block_h, max_hp=75))

        # 3. Plinko Pegboard Grid (Pins)
        self.pegs = []
        for row in range(11):
            py = 350 + row * 95
            cols = 10 if row % 2 == 0 else 9
            offset = 90 if row % 2 == 0 else 145
            for c in range(cols):
                self.pegs.append((offset + c * 100, py))

        # 4. Initial & Active Balls
        self.balls = []
        for i, country in enumerate(self.selected_countries):
            sx = self.width // 2 + (i - 2) * 55
            self.balls.append(CountryBall(country, sx, 220, random.uniform(-1.2, 1.2), random.uniform(0.5, 2.0)))

        self.sparks = []
        self.floating_texts = []
        self.audio_events = []
        self.total_multiplications = 0

        self.winner_start_frame = None
        self.winner_duration_sec = 3.0
        self.winner_frames_total = int(self.winner_duration_sec * self.fps)
        self.is_finished = False
        self.winner_country = None

        self.font_title = pygame.font.SysFont("Arial", 44, bold=True)
        self.font_sub = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 54, bold=True)
        self.font_podium = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_banner = pygame.font.SysFont("Arial", 28, bold=True)

    def render_frame(self, frame_idx):
        t = frame_idx / self.fps
        surface = pygame.Surface((self.width, self.height))
        # Deep space gradient background
        surface.fill((10, 12, 26))

        # Outer Neon Boundary Rails
        pygame.draw.line(surface, (0, 220, 255), (55, 220), (55, 1680), 8)
        pygame.draw.line(surface, (0, 220, 255), (self.width - 55, 220), (self.width - 55, 1680), 8)
        pygame.draw.line(surface, (255, 255, 255), (58, 220), (58, 1680), 2)
        pygame.draw.line(surface, (255, 255, 255), (self.width - 58, 220), (self.width - 58, 1680), 2)

        # Periodic Ball Reinforcement (Drops 1 ball of each nation every 40 frames until finished)
        if frame_idx % 40 == 0 and not self.is_finished and len(self.balls) < 280:
            c = random.choice(self.selected_countries)
            drop_x = random.randint(self.width // 2 - 180, self.width // 2 + 180)
            self.balls.append(CountryBall(c, drop_x, 210, random.uniform(-1.5, 1.5), random.uniform(1.0, 2.5)))

        # 1. Render Pegs with glowing neon center
        for px, py in self.pegs:
            pygame.draw.circle(surface, (45, 60, 95), (px, py), 8)
            pygame.draw.circle(surface, (0, 220, 255), (px, py), 5)
            pygame.draw.circle(surface, (255, 255, 255), (px, py), 2)

        # 2. Update & Render Bottom Country Blocks
        for blk in self.blocks:
            blk.update()
            blk.draw(surface)

        # 3. Update & Render Country Balls
        new_multiplied_balls = []
        for b in self.balls:
            if not b.alive:
                continue
            b.update()

            # Side Wall Collisions
            if b.x - b.radius < 64:
                b.x = 64 + b.radius
                b.vx = abs(b.vx) * 0.85 + random.uniform(0.5, 1.5)
            elif b.x + b.radius > self.width - 64:
                b.x = self.width - 64 - b.radius
                b.vx = -abs(b.vx) * 0.85 - random.uniform(0.5, 1.5)

            # Peg Collisions
            for px, py in self.pegs:
                dx = b.x - px
                dy = b.y - py
                dist = math.hypot(dx, dy)
                if dist < b.radius + 8:
                    overlap = (b.radius + 8) - dist
                    nx = dx / (dist + 1e-6)
                    ny = dy / (dist + 1e-6)
                    b.x += nx * overlap
                    b.y += ny * overlap
                    dot = b.vx * nx + b.vy * ny
                    if dot < 0:
                        b.vx -= 1.65 * dot * nx
                        b.vy -= 1.65 * dot * ny
                        b.vx += random.uniform(-0.5, 0.5)

            # Bottom Country Block Collisions
            for blk in self.blocks:
                if blk.x <= b.x <= blk.x + blk.w and blk.y <= b.y + b.radius <= blk.y + 35 and b.vy > 0:
                    # MATCH CHECK: Ball matches Block Country!
                    if b.code == blk.code and blk.alive:
                        # Damage block
                        shattered = blk.hit(dmg=2)
                        self.total_multiplications += 1

                        # Floating x5 label
                        self.floating_texts.append(FloatingText(b.x, b.y - 15, "x5!", color=(255, 230, 0), font_size=32))

                        # Audio Event
                        self.audio_events.append((t, 780.0 + random.randint(-40, 80), shattered))

                        # Burst Sparks
                        for _ in range(12 if not shattered else 35):
                            self.sparks.append(Spark(b.x, blk.y, b.color))

                        # MULTIPLY BY 5: Original ball bounces up + 4 new matching balls spawn!
                        b.vy = random.uniform(-19.0, -24.0)
                        b.vx = random.uniform(-3.5, 3.5)

                        # Capacity cap for 60 FPS performance stability
                        if len(self.balls) + len(new_multiplied_balls) < 320:
                            for _ in range(4):
                                nb = CountryBall(
                                    b.country,
                                    b.x + random.uniform(-15, 15),
                                    blk.y - random.uniform(5, 20),
                                    random.uniform(-4.0, 4.0),
                                    random.uniform(-18.5, -23.5)
                                )
                                new_multiplied_balls.append(nb)

                        # CHECK WIN CONDITION: Block destroyed!
                        if blk.hp <= 0 and not self.is_finished:
                            self.is_finished = True
                            self.winner_start_frame = frame_idx
                            self.winner_country = blk.country
                            self.audio_events.append((t, 880.0, True))
                            self.audio_events.append((t + 0.15, 1280.0, True))
                            # Giant explosion
                            for _ in range(60):
                                self.sparks.append(Spark(blk.x + blk.w // 2, blk.y + blk.h // 2, blk.color))

                    else:
                        # MISMATCH: Hit different country block or destroyed block
                        # Bounce back up without multiplying
                        b.vy = random.uniform(-12.0, -16.0)
                        b.vx = random.uniform(-2.5, 2.5)
                        self.audio_events.append((t, 360.0 + random.randint(-30, 30), False))
                        for _ in range(3):
                            self.sparks.append(Spark(b.x, blk.y, (140, 150, 180)))
                    break

            # Despawn if fallen below screen
            if b.y > self.height + 40:
                b.alive = False

            b.draw(surface)

        # Merge active balls
        self.balls = [b for b in self.balls if b.alive] + new_multiplied_balls

        # 4. Update & Render Sparks
        for sp in self.sparks[:]:
            sp.update()
            sp.draw(surface)
            if sp.life <= 0:
                self.sparks.remove(sp)

        # 5. Update & Render Floating Texts
        for ft in self.floating_texts[:]:
            ft.update()
            ft.draw(surface)
            if ft.life <= 0:
                self.floating_texts.remove(ft)

        # 6. Header HUD
        title = self.font_title.render("WORLD CUP PLINKO: 5X MULTIPLIER BATTLE", True, (255, 255, 255))
        surface.blit(title, title.get_rect(center=(self.width // 2, 70)))

        sub_text = "MATCH YOUR COLOR -> MULTIPLY X5!  |  FIRST TO DESTROY BLOCK WINS!"
        sub = self.font_sub.render(sub_text, True, (0, 240, 255))
        surface.blit(sub, sub.get_rect(center=(self.width // 2, 125)))

        # Mini Ball Count Stat
        count_txt = self.font_sub.render(f"ACTIVE BALLS: {len(self.balls)}  |  5X MULTIPLICATIONS: {self.total_multiplications}", True, (255, 215, 0))
        surface.blit(count_txt, count_txt.get_rect(center=(self.width // 2, 175)))

        # 7. Dramatic Winner Card (Shown for 3.0 seconds after a country destroys its block)
        if self.is_finished and self.winner_country is not None:
            frames_winner = frame_idx - self.winner_start_frame
            win_ratio = min(1.0, frames_winner / self.winner_frames_total)

            # Confetti fireworks
            if random.random() < 0.45:
                cx = random.randint(100, self.width - 100)
                cy = random.randint(400, 1300)
                confetti_colors = [(255, 215, 0), (0, 230, 255), (255, 60, 120), (50, 255, 120), (255, 255, 255)]
                for _ in range(8):
                    self.sparks.append(Spark(cx, cy, random.choice(confetti_colors)))

            # Glassmorphic Card
            card_w = 960
            card_h = 470
            card_x = (self.width - card_w) // 2
            card_y = 650
            anim_offset = max(0, int((1.0 - min(1.0, frames_winner / 12.0)) * 50))
            draw_y = card_y + anim_offset

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (14, 16, 32, 248), (0, 0, card_w, card_h), border_radius=28)
            pygame.draw.rect(card_surf, (255, 215, 0), (0, 0, card_w, card_h), width=5, border_radius=28)
            pygame.draw.rect(card_surf, self.winner_country["primary"], (5, 5, card_w - 10, card_h - 10), width=3, border_radius=26)
            surface.blit(card_surf, (card_x, draw_y))

            # Header
            crown_txt = self.font_sub.render("🏆 WORLD CUP PLINKO CHAMPION 🏆", True, (255, 215, 0))
            surface.blit(crown_txt, crown_txt.get_rect(center=(self.width // 2, draw_y + 45)))

            # Winner announcement
            win_name_surf = self.font_big.render(f"{self.winner_country['name'].upper()} WINS!", True, self.winner_country["primary"])
            surface.blit(win_name_surf, win_name_surf.get_rect(center=(self.width // 2, draw_y + 115)))

            # Standings by remaining HP (lowest HP remaining = closest to winning)
            other_blocks = [b for b in self.blocks if b.code != self.winner_country["code"]]
            other_blocks.sort(key=lambda b: b.hp)

            p1_txt = self.font_podium.render(f"🥇 1ST: {self.winner_country['name']} ({self.winner_country['code']}) - BLOCK DESTROYED!", True, (255, 220, 50))
            p2 = other_blocks[0] if len(other_blocks) > 0 else None
            p3 = other_blocks[1] if len(other_blocks) > 1 else None

            p2_str = f"🥈 2ND: {p2.name} ({p2.code}) - {p2.hp} HP LEFT" if p2 else "..."
            p3_str = f"🥉 3RD: {p3.name} ({p3.code}) - {p3.hp} HP LEFT" if p3 else "..."
            p2_txt = self.font_podium.render(p2_str, True, (210, 220, 230))
            p3_txt = self.font_podium.render(p3_str, True, (205, 127, 50))

            surface.blit(p1_txt, p1_txt.get_rect(center=(self.width // 2, draw_y + 190)))
            surface.blit(p2_txt, p2_txt.get_rect(center=(self.width // 2, draw_y + 245)))
            surface.blit(p3_txt, p3_txt.get_rect(center=(self.width // 2, draw_y + 300)))

            cta_txt = self.font_banner.render("DID YOUR COUNTRY WIN? COMMENT BELOW! 👇", True, (0, 255, 220))
            surface.blit(cta_txt, cta_txt.get_rect(center=(self.width // 2, draw_y + 380)))

            progress = 0.85 + 0.15 * win_ratio
        else:
            # Progress based on damage done to blocks
            total_hp_remaining = sum(b.hp for b in self.blocks)
            total_max_hp = sum(b.max_hp for b in self.blocks)
            progress = min(0.85, (1.0 - total_hp_remaining / total_max_hp) * 0.85)

        # Bottom Progress Bar
        bar_w = 800
        bar_h = 14
        bx = (self.width - bar_w) // 2
        by = 1840
        pygame.draw.rect(surface, (40, 40, 60), (bx, by, bar_w, bar_h), border_radius=7)
        pygame.draw.rect(surface, (255, 200, 0), (bx, by, int(bar_w * progress), bar_h), border_radius=7)

        return pygame.image.tostring(surface, "RGB")

    def generate_video(self, output_path: Path):
        output_path = Path(output_path)
        print(f"[PlinkoMultiplier] Generating dynamic video: plays until first block destroyed + 3s winner popup...")

        renderer = VideoRenderer(output_path=output_path, width=self.width, height=self.height, fps=self.fps)
        renderer.start()

        frame_idx = 0
        total_winner_frames = int(self.winner_duration_sec * self.fps)
        max_safety_frames = int(60.0 * self.fps)

        while True:
            frame_bytes = self.render_frame(frame_idx)
            renderer.write_frame(frame_bytes)

            if self.is_finished and self.winner_start_frame is not None:
                if frame_idx - self.winner_start_frame >= total_winner_frames:
                    frame_idx += 1
                    break

            if frame_idx >= max_safety_frames:
                print(f"[PlinkoMultiplier] Safety cutoff reached at {frame_idx} frames.")
                break

            if frame_idx % 120 == 0:
                print(f"  -> Rendering progress: frame {frame_idx} ({frame_idx / self.fps:.1f}s)...")

            frame_idx += 1

        total_frames = frame_idx
        actual_duration_sec = total_frames / self.fps
        print(f"[PlinkoMultiplier] Battle finished & 3s winner popup completed! Duration: {actual_duration_sec:.2f}s ({total_frames} frames).")

        print("[PlinkoMultiplier] Synthesizing procedural audio...")
        audio = ProceduralAudioEngine(duration_sec=actual_duration_sec)
        audio.add_subtle_background_pulse(bpm=128.0, volume=0.15)

        for (timestamp, freq, is_shatter) in self.audio_events:
            if timestamp <= actual_duration_sec:
                audio.add_tone(start_time=timestamp, freq=freq, duration=0.12, volume=0.45)
                if is_shatter:
                    audio.add_explosion(start_time=timestamp, volume=0.85)

        temp_wav = output_path.with_suffix(".temp.wav")
        audio.export_wav(temp_wav)

        print("[PlinkoMultiplier] Muxing video and audio into final MP4...")
        final_file = renderer.finalize_with_audio(temp_wav)
        print(f"[PlinkoMultiplier] Done! Video saved at: {final_file}")
        return final_file
