import math
import random
import numpy as np
import pygame
from pathlib import Path
from core.config import VIDEO_WIDTH, VIDEO_HEIGHT, FPS
from core.audio_synth import ProceduralAudioEngine
from core.video_renderer import VideoRenderer

class Ball:
    def __init__(self, x, y, vx=0.0, vy=0.0, color=(0, 255, 200)):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.radius = 9
        self.color = color
        self.alive = True

    def update(self):
        self.vy += 0.28  # Gravity
        self.vx *= 0.99
        self.vy *= 0.99
        self.x += self.vx
        self.y += self.vy

class Gate:
    def __init__(self, x1, x2, y, multiplier=2, label="x2", color=(0, 220, 255)):
        self.x1 = x1
        self.x2 = x2
        self.y = y
        self.multiplier = multiplier
        self.label = label
        self.color = color
        self.cooldown = {}  # ball_id cooldown

class Brick:
    def __init__(self, x, y, w, h, hp, color=(255, 60, 100)):
        self.rect = pygame.Rect(x, y, w, h)
        self.hp = hp
        self.max_hp = hp
        self.color = color
        self.alive = True

    def hit(self, dmg=1):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False
            return True
        return False

class Spark:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        ang = random.uniform(0, 2 * math.pi)
        spd = random.uniform(2, 8)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd
        self.life = 1.0
        self.decay = random.uniform(0.03, 0.07)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay

    def draw(self, surf):
        if self.life > 0:
            alpha = int(self.life * 255)
            r, g, b = self.color
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (r, g, b, alpha), (3, 3), 3)
            surf.blit(s, (int(self.x - 3), int(self.y - 3)))

class PlinkoMultiplierGame:
    def __init__(self, duration_sec=30, width=VIDEO_WIDTH, height=VIDEO_HEIGHT, fps=FPS):
        pygame.init()
        self.width = width
        self.height = height
        self.fps = fps
        self.duration_sec = duration_sec
        self.total_frames = int(duration_sec * fps)

        # Pegs
        self.pegs = []
        for row in range(9):
            py = 360 + row * 90
            cols = 10 if row % 2 == 0 else 9
            offset = 90 if row % 2 == 0 else 145
            for c in range(cols):
                self.pegs.append((offset + c * 100, py))

        # Multiplier Gates
        self.gates = [
            Gate(x1=200, x2=450, y=580, multiplier=3, label="x3 MULTIPLY", color=(0, 255, 150)),
            Gate(x1=630, x2=880, y=580, multiplier=2, label="x2 MULTIPLY", color=(0, 200, 255)),
            Gate(x1=150, x2=400, y=950, multiplier=4, label="x4 BURST", color=(255, 200, 0)),
            Gate(x1=450, x2=630, y=950, multiplier=5, label="x5 MEGA", color=(255, 50, 180)),
            Gate(x1=680, x2=930, y=950, multiplier=3, label="x3 MULTIPLY", color=(0, 255, 150)),
        ]

        # Bricks at the bottom
        self.bricks = []
        brick_w = 120
        brick_h = 60
        brick_rows = 3
        brick_cols = 7
        start_bx = (self.width - (brick_cols * (brick_w + 16))) // 2
        for r in range(brick_rows):
            for c in range(brick_cols):
                bx = start_bx + c * (brick_w + 16)
                by = 1380 + r * (brick_h + 16)
                hp = random.choice([40, 60, 80, 100])
                colors = [(255, 60, 120), (180, 60, 255), (0, 200, 255), (255, 160, 20)]
                self.bricks.append(Brick(bx, by, brick_w, brick_h, hp, colors[(r + c) % len(colors)]))

        self.balls = [Ball(self.width // 2, 220, random.uniform(-0.5, 0.5), 1.0)]
        self.sparks = []
        self.audio_events = []
        self.total_damage = 0

        self.font_title = pygame.font.SysFont("Arial", 44, bold=True)
        self.font_sub = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_gate = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_brick = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 56, bold=True)
        self.font_banner = pygame.font.SysFont("Arial", 32, bold=True)

    def render_frame(self, frame_idx):
        t = frame_idx / self.fps
        surface = pygame.Surface((self.width, self.height))
        surface.fill((10, 12, 24))

        # Periodic ball spawner from top (drops extra balls at intervals)
        if frame_idx % 45 == 0 and frame_idx < self.total_frames * 0.6:
            self.balls.append(Ball(self.width // 2 + random.randint(-60, 60), 200, random.uniform(-1, 1), 1.5))

        # 1. Render Gates
        for g in self.gates:
            rect = pygame.Rect(g.x1, g.y - 12, g.x2 - g.x1, 24)
            pygame.draw.rect(surface, (g.color[0]//4, g.color[1]//4, g.color[2]//4), rect, border_radius=6)
            pygame.draw.rect(surface, g.color, rect, width=3, border_radius=6)
            gtxt = self.font_gate.render(g.label, True, (255, 255, 255))
            surface.blit(gtxt, gtxt.get_rect(center=rect.center))

        # 2. Render Pegs
        for px, py in self.pegs:
            pygame.draw.circle(surface, (80, 100, 140), (px, py), 7)
            pygame.draw.circle(surface, (200, 225, 255), (px, py), 4)

        # 3. Render Bricks
        for br in self.bricks:
            if br.alive:
                pygame.draw.rect(surface, br.color, br.rect, border_radius=8)
                pygame.draw.rect(surface, (255, 255, 255), br.rect, width=2, border_radius=8)
                hp_txt = self.font_brick.render(str(br.hp), True, (255, 255, 255))
                surface.blit(hp_txt, hp_txt.get_rect(center=br.rect.center))

        # 4. Update & Render Balls
        new_balls = []
        for b in self.balls:
            if not b.alive:
                continue
            b.update()

            # Walls
            if b.x < 50:
                b.x = 50
                b.vx = abs(b.vx) * 0.8
            elif b.x > self.width - 50:
                b.x = self.width - 50
                b.vx = -abs(b.vx) * 0.8

            # Peg collisions
            for px, py in self.pegs:
                dx = b.x - px
                dy = b.y - py
                dist = math.hypot(dx, dy)
                if dist < b.radius + 7:
                    overlap = (b.radius + 7) - dist
                    nx = dx / (dist + 1e-6)
                    ny = dy / (dist + 1e-6)
                    b.x += nx * overlap
                    b.y += ny * overlap
                    dot = b.vx * nx + b.vy * ny
                    if dot < 0:
                        b.vx -= 1.6 * dot * nx
                        b.vy -= 1.6 * dot * ny
                        b.vx += random.uniform(-0.5, 0.5)

            # Gate collision (Multiplication!)
            for g in self.gates:
                if g.x1 <= b.x <= g.x2 and abs(b.y - g.y) < 14 and b.vy > 0:
                    # Spawn multiplied copies (capped to avoid memory overload)
                    if len(self.balls) + len(new_balls) < 500:
                        for _ in range(g.multiplier - 1):
                            nb = Ball(b.x + random.uniform(-10, 10), b.y + random.uniform(5, 15),
                                      b.vx + random.uniform(-2, 2), b.vy + random.uniform(0, 1.5),
                                      color=g.color)
                            new_balls.append(nb)
                        self.audio_events.append((t, 550.0 + random.randint(-50, 150), False))

            # Brick collisions
            for br in self.bricks:
                if br.alive and br.rect.collidepoint(b.x, b.y):
                    b.vy = -abs(b.vy) * 0.75 + random.uniform(-1, 1)
                    b.vx += random.uniform(-1.5, 1.5)
                    shattered = br.hit(1)
                    self.total_damage += 1
                    self.audio_events.append((t, 320.0 + (self.total_damage % 20) * 15, shattered))

                    # Sparks
                    for _ in range(8 if not shattered else 25):
                        self.sparks.append(Spark(b.x, b.y, br.color))
                    break

            # Despawn if fallen below screen
            if b.y > self.height + 50:
                b.alive = False

            # Draw ball
            pygame.draw.circle(surface, b.color, (int(b.x), int(b.y)), b.radius)
            pygame.draw.circle(surface, (255, 255, 255), (int(b.x - 2), int(b.y - 2)), int(b.radius * 0.35))

        self.balls = [b for b in self.balls if b.alive] + new_balls

        # 5. Update Sparks
        for sp in self.sparks[:]:
            sp.update()
            sp.draw(surface)
            if sp.life <= 0:
                self.sparks.remove(sp)

        # 6. UI Overlays
        title = self.font_title.render("EXPONENTIAL MULTIPLIER RUSH", True, (255, 255, 255))
        surface.blit(title, title.get_rect(center=(self.width // 2, 80)))

        sub = self.font_sub.render(f"ACTIVE BALLS: {len(self.balls)}   |   DAMAGE: {self.total_damage}", True, (0, 255, 200))
        surface.blit(sub, sub.get_rect(center=(self.width // 2, 140)))

        # Progress bar
        progress = frame_idx / self.total_frames
        bar_w = 800
        bar_h = 14
        bx = (self.width - bar_w) // 2
        by = 1840
        pygame.draw.rect(surface, (40, 40, 60), (bx, by, bar_w, bar_h), border_radius=7)
        pygame.draw.rect(surface, (0, 230, 255), (bx, by, int(bar_w * progress), bar_h), border_radius=7)

        # Final Victory / Results Screen (Triggered in final 20% of the video)
        if progress > 0.78:
            # Celebration spark fireworks
            for _ in range(5):
                fx = random.randint(120, self.width - 120)
                fy = random.randint(500, 1300)
                self.sparks.append(Spark(fx, fy, random.choice([(255, 60, 120), (0, 255, 200), (255, 220, 50), (180, 80, 255)])))

            card_w = 920
            card_h = 420
            card_x = (self.width - card_w) // 2
            card_y = 680

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (14, 16, 30, 242), (0, 0, card_w, card_h), border_radius=28)
            pygame.draw.rect(card_surf, (0, 230, 255), (0, 0, card_w, card_h), width=5, border_radius=28)
            pygame.draw.rect(card_surf, (255, 255, 255, 60), (4, 4, card_w - 8, card_h - 8), width=2, border_radius=26)
            surface.blit(card_surf, (card_x, card_y))

            # Header
            head_txt = self.font_banner.render("--- STAGE COMPLETE ---", True, (255, 215, 0))
            surface.blit(head_txt, head_txt.get_rect(center=(self.width // 2, card_y + 45)))

            # Big Score Announcement
            score_txt = self.font_big.render(f"SCORE: {self.total_damage * 10:,}", True, (0, 255, 200))
            surface.blit(score_txt, score_txt.get_rect(center=(self.width // 2, card_y + 120)))

            # Stats line
            stats_line = self.font_sub.render(f"TOTAL BRICKS PULVERIZED: {self.total_damage}  |  MAX MULTIPLIER: x5", True, (255, 255, 255))
            surface.blit(stats_line, stats_line.get_rect(center=(self.width // 2, card_y + 205)))

            rating_line = self.font_sub.render("RANK: LEGENDARY CHAOS", True, (255, 220, 50))
            surface.blit(rating_line, rating_line.get_rect(center=(self.width // 2, card_y + 255)))

            # Call to Action
            cta_txt = self.font_banner.render("DID YOU ENJOY THIS ASMR? COMMENT BELOW!", True, (255, 60, 160))
            surface.blit(cta_txt, cta_txt.get_rect(center=(self.width // 2, card_y + 340)))

        return pygame.image.tostring(surface, "RGB")

    def generate_video(self, output_path: Path):
        output_path = Path(output_path)
        print(f"[PlinkoMultiplier] Generating {self.duration_sec}s video ({self.total_frames} frames)...")

        renderer = VideoRenderer(output_path=output_path, width=self.width, height=self.height, fps=self.fps)
        renderer.start()

        for frame_idx in range(self.total_frames):
            frame_bytes = self.render_frame(frame_idx)
            renderer.write_frame(frame_bytes)

            if frame_idx % 120 == 0 or frame_idx == self.total_frames - 1:
                percent = int((frame_idx + 1) / self.total_frames * 100)
                print(f"  -> Rendering progress: {percent}% ({frame_idx+1}/{self.total_frames})")

        print("[PlinkoMultiplier] Synthesizing procedural audio...")
        audio = ProceduralAudioEngine(duration_sec=self.duration_sec)
        audio.add_subtle_background_pulse(bpm=128.0, volume=0.15)

        for (timestamp, freq, is_shatter) in self.audio_events:
            audio.add_tone(start_time=timestamp, freq=freq, duration=0.12, volume=0.45)
            if is_shatter:
                audio.add_explosion(start_time=timestamp, volume=0.85)

        temp_wav = output_path.with_suffix(".temp.wav")
        audio.export_wav(temp_wav)

        print("[PlinkoMultiplier] Muxing video and audio into final MP4...")
        final_file = renderer.finalize_with_audio(temp_wav)
        print(f"[PlinkoMultiplier] Done! Video saved at: {final_file}")
        return final_file
