import math
import random
import numpy as np
import pygame
from pathlib import Path
from core.config import VIDEO_WIDTH, VIDEO_HEIGHT, FPS
from core.audio_synth import ProceduralAudioEngine
from core.video_renderer import VideoRenderer

class Particle:
    def __init__(self, x, y, color, speed_mult=1.0):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3, 10) * speed_mult
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.04)
        self.radius = random.uniform(4, 8)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15  # subtle gravity for confetti
        self.vx *= 0.97
        self.life -= self.decay

    def draw(self, surface):
        if self.life > 0:
            alpha = int(self.life * 255)
            r, g, b = self.color
            surf = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (r, g, b, alpha), (int(self.radius), int(self.radius)), int(self.radius))
            surface.blit(surf, (int(self.x - self.radius), int(self.y - self.radius)))

class Marble:
    def __init__(self, name, color, start_x, start_y):
        self.name = name
        self.color = color
        self.x = float(start_x)
        self.y = float(start_y)
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(0.0, 2.0)
        self.radius = 18
        self.finished = False
        self.finish_time = None
        self.rank = None
        self.trail = []

    def update(self):
        if not self.finished:
            self.trail.append((self.x, self.y))
            if len(self.trail) > 8:
                self.trail.pop(0)

class Spinner:
    def __init__(self, cx, cy, length=120, speed=0.04):
        self.cx = cx
        self.cy = cy
        self.length = length
        self.angle = random.uniform(0, math.pi)
        self.speed = speed

    def update(self):
        self.angle += self.speed

    def check_collision(self, marble):
        # Line segment from -half_len to +half_len
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        p1x = self.cx - cos_a * (self.length / 2)
        p1y = self.cy - sin_a * (self.length / 2)
        p2x = self.cx + cos_a * (self.length / 2)
        p2y = self.cy + sin_a * (self.length / 2)

        # Distance from point to line segment
        seg_dx = p2x - p1x
        seg_dy = p2y - p1y
        seg_len_sq = seg_dx * seg_dx + seg_dy * seg_dy

        t = max(0, min(1, ((marble.x - p1x) * seg_dx + (marble.y - p1y) * seg_dy) / seg_len_sq))
        proj_x = p1x + t * seg_dx
        proj_y = p1y + t * seg_dy

        dist = math.hypot(marble.x - proj_x, marble.y - proj_y)
        if dist < marble.radius + 6:
            # Collision! Bounce away from normal
            norm_x = (marble.x - proj_x) / (dist + 1e-6)
            norm_y = (marble.y - proj_y) / (dist + 1e-6)
            dot = marble.vx * norm_x + marble.vy * norm_y
            if dot < 0:
                marble.vx -= 1.8 * dot * norm_x
                marble.vy -= 1.8 * dot * norm_y
                # Add spinner angular velocity to bounce
                marble.vx += -sin_a * self.speed * 40
                marble.vy += cos_a * self.speed * 40
                return True
        return False

class MarbleArenaGame:
    def __init__(self, duration_sec=30, width=VIDEO_WIDTH, height=VIDEO_HEIGHT, fps=FPS):
        pygame.init()
        self.width = width
        self.height = height
        self.fps = fps
        self.duration_sec = duration_sec
        self.total_frames = int(duration_sec * fps)

        # 8 Contestant Marbles
        contestants = [
            ("RED", (255, 65, 65)),
            ("BLUE", (65, 140, 255)),
            ("GREEN", (65, 255, 120)),
            ("YELLOW", (255, 230, 45)),
            ("PURPLE", (200, 75, 255)),
            ("ORANGE", (255, 140, 30)),
            ("CYAN", (30, 240, 240)),
            ("WHITE", (240, 240, 250))
        ]

        # Staggered launch at top
        self.marbles = []
        start_x_spacing = (width - 300) / (len(contestants) - 1)
        for i, (name, col) in enumerate(contestants):
            sx = 150 + i * start_x_spacing
            sy = random.uniform(260, 310)
            self.marbles.append(Marble(name, col, sx, sy))

        # Pegboard Grid
        self.pegs = []
        rows = 12
        for r in range(rows):
            py = 420 + r * 95
            cols = 9 if r % 2 == 0 else 8
            offset_x = 100 if r % 2 == 0 else 155
            for c in range(cols):
                px = offset_x + c * 110
                self.pegs.append((px, py))

        # Spinners (Hazard Wheels)
        self.spinners = [
            Spinner(cx=300, cy=750, length=140, speed=0.045),
            Spinner(cx=780, cy=750, length=140, speed=-0.045),
            Spinner(cx=540, cy=1050, length=160, speed=0.05),
            Spinner(cx=320, cy=1350, length=130, speed=-0.04),
            Spinner(cx=760, cy=1350, length=130, speed=0.04),
        ]

        self.finish_line_y = 1620
        self.finishers = []
        self.audio_events = []
        self.particles = []

        self.font_title = pygame.font.SysFont("Arial", 44, bold=True)
        self.font_sub = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_name = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 62, bold=True)
        self.font_podium = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_cta = pygame.font.SysFont("Arial", 28, bold=True)

    def render_frame(self, frame_idx):
        t = frame_idx / self.fps
        surface = pygame.Surface((self.width, self.height))
        surface.fill((12, 14, 28))

        # 1. Draw Arena Side Walls
        pygame.draw.line(surface, (0, 200, 255), (60, 250), (60, self.finish_line_y + 100), 8)
        pygame.draw.line(surface, (0, 200, 255), (self.width - 60, 250), (self.width - 60, self.finish_line_y + 100), 8)

        # 2. Update and Draw Spinners
        for sp in self.spinners:
            sp.update()
            cos_a = math.cos(sp.angle)
            sin_a = math.sin(sp.angle)
            p1 = (sp.cx - cos_a * (sp.length / 2), sp.cy - sin_a * (sp.length / 2))
            p2 = (sp.cx + cos_a * (sp.length / 2), sp.cy + sin_a * (sp.length / 2))
            pygame.draw.line(surface, (255, 60, 160), p1, p2, 10)
            pygame.draw.circle(surface, (255, 255, 255), (sp.cx, sp.cy), 10)

        # 3. Draw Pegs
        for px, py in self.pegs:
            pygame.draw.circle(surface, (70, 90, 130), (px, py), 9)
            pygame.draw.circle(surface, (180, 210, 255), (px, py), 6)

        # 4. Elimination Line (Marbles that drop first are OUT)
        pygame.draw.line(surface, (255, 60, 60), (60, self.finish_line_y), (self.width - 60, self.finish_line_y), 6)
        elim_text = self.font_sub.render("--- DANGER: ELIMINATION ZONE (OUT!) ---", True, (255, 80, 80))
        surface.blit(elim_text, elim_text.get_rect(center=(self.width // 2, self.finish_line_y - 20)))

        # Dynamic gravity calibrated so marbles survive across the designated video duration
        base_gravity = max(0.08, min(0.24, 2.8 / (self.duration_sec * 0.85)))

        # 5. Physics Update for Marbles
        for m in self.marbles:
            if not m.finished:
                # Gravity & air resistance
                m.vy += base_gravity
                m.vx *= 0.99
                m.vy *= 0.99

                m.x += m.vx
                m.y += m.vy

                # Side wall collision
                if m.x - m.radius < 68:
                    m.x = 68 + m.radius
                    m.vx = abs(m.vx) * 0.75 + random.uniform(0.5, 1.5)
                elif m.x + m.radius > self.width - 68:
                    m.x = self.width - 68 - m.radius
                    m.vx = -abs(m.vx) * 0.75 - random.uniform(0.5, 1.5)

                # Peg collisions
                for px, py in self.pegs:
                    dx = m.x - px
                    dy = m.y - py
                    dist = math.hypot(dx, dy)
                    if dist < m.radius + 8:
                        overlap = (m.radius + 8) - dist
                        nx = dx / (dist + 1e-6)
                        ny = dy / (dist + 1e-6)
                        m.x += nx * overlap
                        m.y += ny * overlap

                        dot = m.vx * nx + m.vy * ny
                        if dot < 0:
                            m.vx -= 1.7 * dot * nx
                            m.vy -= 1.7 * dot * ny
                            m.vx += random.uniform(-1.0, 1.0)
                            # Extra upward bounce to keep marbles fighting on pegs
                            if random.random() < 0.25:
                                m.vy -= random.uniform(0.5, 2.0)

                            # Trigger pleasant peg chime
                            freq = 300 + (py / self.height) * 500
                            self.audio_events.append((t, freq, False))

                # Spinner collisions
                for sp in self.spinners:
                    if sp.check_collision(m):
                        self.audio_events.append((t, 650.0, False))

                # Elimination Check: Falling below elimination line eliminates the marble
                if m.y >= self.finish_line_y:
                    m.finished = True
                    m.finish_time = t
                    self.finishers.append(m)  # Added in order of elimination
                    # Elimination drop sound
                    self.audio_events.append((t, 180.0 + len(self.finishers) * 20, False))

                m.update()

            # Render Marble Trails
            for idx, (tx, ty) in enumerate(m.trail):
                alpha = int(120 * (idx + 1) / len(m.trail))
                r, g, b = m.color
                surf = pygame.Surface((m.radius * 2, m.radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (r, g, b, alpha), (m.radius, m.radius), int(m.radius * 0.75))
                surface.blit(surf, (int(tx - m.radius), int(ty - m.radius)))

            # Render Marble (only if still alive or just crossed)
            if not m.finished or (m.finished and t - m.finish_time < 0.5):
                pygame.draw.circle(surface, m.color, (int(m.x), int(m.y)), m.radius)
                pygame.draw.circle(surface, (255, 255, 255), (int(m.x - 4), int(m.y - 4)), int(m.radius * 0.35))
                pygame.draw.circle(surface, (20, 20, 30), (int(m.x), int(m.y)), m.radius, 2)

                # Name tag
                txt = self.font_name.render(m.name[:3], True, (255, 255, 255))
                surface.blit(txt, txt.get_rect(center=(int(m.x), int(m.y - 25))))

        # Alive marbles calculation
        alive_marbles = [m for m in self.marbles if not m.finished]
        progress = frame_idx / self.total_frames

        # 6. Header & Real-Time Survival Tracker
        title = self.font_title.render("MARBLE SURVIVAL ELIMINATION", True, (255, 255, 255))
        surface.blit(title, title.get_rect(center=(self.width // 2, 80)))

        status_text = f"LAST COLOR STANDING WINS!  |  ALIVE: {len(alive_marbles)} / 8"
        sub = self.font_sub.render(status_text, True, (0, 255, 220))
        surface.blit(sub, sub.get_rect(center=(self.width // 2, 140)))

        # 7. Winner Announcement Card (ONLY appears in the final 22% of video or when 1 survivor remains near end)
        show_winner = (progress >= 0.76) or (len(alive_marbles) <= 1 and progress >= 0.65)
        if show_winner:
            # Ranking: The LAST marble to survive is the 1st place champion!
            # Marbles still alive are ranked highest (lowest y / highest on board),
            # followed by the most recently eliminated marbles.
            remaining = sorted(alive_marbles, key=lambda m: m.y)
            eliminated_reversed = list(reversed(self.finishers))
            full_ranking = remaining + eliminated_reversed

            winner = full_ranking[0]
            p2 = full_ranking[1] if len(full_ranking) > 1 else None
            p3 = full_ranking[2] if len(full_ranking) > 2 else None

            # Spawn continuous confetti fireworks
            for _ in range(5):
                cx = random.randint(100, self.width - 100)
                cy = random.randint(500, 1300)
                confetti_colors = [(255, 50, 50), (50, 150, 255), (50, 255, 100), (255, 220, 50), (255, 100, 255), (0, 255, 255)]
                self.particles.append(Particle(cx, cy, random.choice(confetti_colors), speed_mult=1.8))

            # Glassmorphism Backdrop Card
            card_w = 920
            card_h = 440
            card_x = (self.width - card_w) // 2
            card_y = 660

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (15, 18, 35, 242), (0, 0, card_w, card_h), border_radius=28)
            pygame.draw.rect(card_surf, winner.color, (0, 0, card_w, card_h), width=5, border_radius=28)
            # Inner accent glow
            pygame.draw.rect(card_surf, (255, 255, 255, 60), (4, 4, card_w - 8, card_h - 8), width=2, border_radius=26)
            surface.blit(card_surf, (card_x, card_y))

            # Header Banner
            crown_txt = self.font_sub.render("--- LAST COLOR STANDING ---", True, (255, 215, 0))
            surface.blit(crown_txt, crown_txt.get_rect(center=(self.width // 2, card_y + 45)))

            # Big Winner Announcement
            win_name_surf = self.font_big.render(f"{winner.name} IS THE WINNER!", True, winner.color)
            surface.blit(win_name_surf, win_name_surf.get_rect(center=(self.width // 2, card_y + 115)))

            # Podium Standings
            p1_txt = self.font_podium.render(f"1ST PLACE (CHAMPION): {winner.name}", True, (255, 220, 50))
            p2_name = p2.name if p2 else "..."
            p3_name = p3.name if p3 else "..."
            p2_txt = self.font_podium.render(f"2ND PLACE: {p2_name}", True, (210, 220, 230))
            p3_txt = self.font_podium.render(f"3RD PLACE: {p3_name}", True, (205, 127, 50))

            surface.blit(p1_txt, p1_txt.get_rect(center=(self.width // 2, card_y + 190)))
            surface.blit(p2_txt, p2_txt.get_rect(center=(self.width // 2, card_y + 245)))
            surface.blit(p3_txt, p3_txt.get_rect(center=(self.width // 2, card_y + 300)))

            # Comment Call to Action (High engagement bait)
            cta_txt = self.font_cta.render("DID YOUR COLOR SURVIVE? COMMENT BELOW!", True, (0, 255, 220))
            surface.blit(cta_txt, cta_txt.get_rect(center=(self.width // 2, card_y + 375)))

        # Update & Draw Particles (Confetti)
        for p in self.particles[:]:
            p.update()
            p.draw(surface)
            if p.life <= 0:
                self.particles.remove(p)

        # Progress bar
        progress = frame_idx / self.total_frames
        bar_w = 800
        bar_h = 14
        bx = (self.width - bar_w) // 2
        by = 1840
        pygame.draw.rect(surface, (40, 40, 60), (bx, by, bar_w, bar_h), border_radius=7)
        pygame.draw.rect(surface, (255, 200, 0), (bx, by, int(bar_w * progress), bar_h), border_radius=7)

        return pygame.image.tostring(surface, "RGB")

    def generate_video(self, output_path: Path):
        output_path = Path(output_path)
        print(f"[MarbleArena] Generating {self.duration_sec}s video ({self.total_frames} frames)...")

        renderer = VideoRenderer(output_path=output_path, width=self.width, height=self.height, fps=self.fps)
        renderer.start()

        for frame_idx in range(self.total_frames):
            frame_bytes = self.render_frame(frame_idx)
            renderer.write_frame(frame_bytes)

            if frame_idx % 120 == 0 or frame_idx == self.total_frames - 1:
                percent = int((frame_idx + 1) / self.total_frames * 100)
                print(f"  -> Rendering progress: {percent}% ({frame_idx+1}/{self.total_frames})")

        print("[MarbleArena] Synthesizing procedural audio...")
        audio = ProceduralAudioEngine(duration_sec=self.duration_sec)
        audio.add_subtle_background_pulse(bpm=130.0, volume=0.15)

        for (timestamp, freq, is_finish) in self.audio_events:
            audio.add_tone(start_time=timestamp, freq=freq, duration=0.18, volume=0.55)
            if is_finish:
                audio.add_explosion(start_time=timestamp, volume=0.8)

        temp_wav = output_path.with_suffix(".temp.wav")
        audio.export_wav(temp_wav)

        print("[MarbleArena] Muxing video and audio into final MP4...")
        final_file = renderer.finalize_with_audio(temp_wav)
        print(f"[MarbleArena] Done! Video saved at: {final_file}")
        return final_file
