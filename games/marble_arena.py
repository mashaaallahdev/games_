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
        speed = random.uniform(3, 11) * speed_mult
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.045)
        self.radius = random.uniform(4, 9)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.16  # Gravity for confetti/sparks
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
        self.vy = random.uniform(0.0, 1.5)
        self.radius = 18
        self.finished = False
        self.finish_time = None
        self.trail = []

    def update(self):
        if not self.finished:
            self.trail.append((self.x, self.y))
            if len(self.trail) > 12:
                self.trail.pop(0)

class PinballBumper:
    """High-energy neon pinball bumper that flashes and blasts marbles back with sparks."""
    def __init__(self, cx, cy, radius=36, color=(255, 40, 150)):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.color = color
        self.flash_timer = 0

    def update(self):
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def check_collision(self, marble):
        dist = math.hypot(marble.x - self.cx, marble.y - self.cy)
        if dist < self.radius + marble.radius:
            nx = (marble.x - self.cx) / (dist + 1e-6)
            ny = (marble.y - self.cy) / (dist + 1e-6)
            # Explosive bounce outward
            dot = marble.vx * nx + marble.vy * ny
            bounce_force = max(14.0, abs(dot) * 2.2)
            marble.vx = nx * bounce_force + random.uniform(-2, 2)
            marble.vy = ny * bounce_force - random.uniform(1, 4)
            self.flash_timer = 12
            return True
        return False

    def draw(self, surface):
        is_lit = self.flash_timer > 0
        ring_color = (255, 255, 255) if is_lit else self.color

        # Outer glow
        glow_surf = pygame.Surface((self.radius * 3, self.radius * 3), pygame.SRCALPHA)
        alpha = 110 if is_lit else 40
        pygame.draw.circle(glow_surf, (*self.color, alpha), (int(self.radius * 1.5), int(self.radius * 1.5)), int(self.radius * 1.4))
        surface.blit(glow_surf, (int(self.cx - self.radius * 1.5), int(self.cy - self.radius * 1.5)))

        # Bumper core
        pygame.draw.circle(surface, (25, 28, 50), (int(self.cx), int(self.cy)), self.radius)
        pygame.draw.circle(surface, ring_color, (int(self.cx), int(self.cy)), self.radius, 4)
        pygame.draw.circle(surface, ring_color, (int(self.cx), int(self.cy)), self.radius // 2)

class Spinner:
    def __init__(self, cx, cy, length=150, speed=0.045, blades=2, color=(0, 230, 255)):
        self.cx = cx
        self.cy = cy
        self.length = length
        self.speed = speed
        self.blades = blades
        self.angle = random.uniform(0, math.pi)
        self.color = color

    def update(self):
        self.angle += self.speed

    def check_collision(self, marble):
        blade_angle_step = math.pi / self.blades
        for b in range(self.blades):
            ang = self.angle + b * blade_angle_step
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            p1x = self.cx - cos_a * (self.length / 2)
            p1y = self.cy - sin_a * (self.length / 2)
            p2x = self.cx + cos_a * (self.length / 2)
            p2y = self.cy + sin_a * (self.length / 2)

            seg_dx = p2x - p1x
            seg_dy = p2y - p1y
            seg_len_sq = seg_dx * seg_dx + seg_dy * seg_dy

            t = max(0, min(1, ((marble.x - p1x) * seg_dx + (marble.y - p1y) * seg_dy) / seg_len_sq))
            proj_x = p1x + t * seg_dx
            proj_y = p1y + t * seg_dy

            dist = math.hypot(marble.x - proj_x, marble.y - proj_y)
            if dist < marble.radius + 8:
                norm_x = (marble.x - proj_x) / (dist + 1e-6)
                norm_y = (marble.y - proj_y) / (dist + 1e-6)
                dot = marble.vx * norm_x + marble.vy * norm_y
                if dot < 0:
                    marble.vx -= 1.85 * dot * norm_x
                    marble.vy -= 1.85 * dot * norm_y
                    marble.vx += -sin_a * self.speed * 45
                    marble.vy += cos_a * self.speed * 45
                    return True
        return False

    def draw(self, surface):
        blade_angle_step = math.pi / self.blades
        for b in range(self.blades):
            ang = self.angle + b * blade_angle_step
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            p1 = (self.cx - cos_a * (self.length / 2), self.cy - sin_a * (self.length / 2))
            p2 = (self.cx + cos_a * (self.length / 2), self.cy + sin_a * (self.length / 2))
            pygame.draw.line(surface, self.color, p1, p2, 8)
            pygame.draw.circle(surface, (255, 255, 255), p1, 5)
            pygame.draw.circle(surface, (255, 255, 255), p2, 5)

        # Center spinning hub
        pygame.draw.circle(surface, (20, 24, 40), (int(self.cx), int(self.cy)), 16)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.cx), int(self.cy)), 16, 3)
        pygame.draw.circle(surface, self.color, (int(self.cx), int(self.cy)), 8)


class MarbleArenaGame:
    def __init__(self, duration_sec=30, width=VIDEO_WIDTH, height=VIDEO_HEIGHT, fps=FPS):
        pygame.init()
        self.width = width
        self.height = height
        self.fps = fps
        self.duration_sec = duration_sec
        self.total_frames = int(duration_sec * fps)

        # 8 Contestant Marbles (100% pure vibrant colors - zero zodiac signs)
        contestants = [
            ("RED", (255, 60, 60)),
            ("BLUE", (60, 140, 255)),
            ("GREEN", (50, 255, 120)),
            ("YELLOW", (255, 230, 40)),
            ("PURPLE", (210, 75, 255)),
            ("ORANGE", (255, 140, 30)),
            ("CYAN", (30, 245, 245)),
            ("WHITE", (245, 245, 255))
        ]

        # Staggered launch at top
        self.marbles = []
        start_x_spacing = (width - 320) / (len(contestants) - 1)
        for i, (name, col) in enumerate(contestants):
            sx = 160 + i * start_x_spacing
            sy = random.uniform(250, 290)
            self.marbles.append(Marble(name, col, sx, sy))

        # Pegboard Grid (Glowing pins)
        self.pegs = []
        rows = 11
        for r in range(rows):
            py = 390 + r * 95
            cols = 9 if r % 2 == 0 else 8
            offset_x = 100 if r % 2 == 0 else 155
            for c in range(cols):
                px = offset_x + c * 110
                self.pegs.append((px, py))

        # Pinball Bumpers (Explosive ricochet pads)
        self.bumpers = [
            PinballBumper(cx=540, cy=680, radius=38, color=(255, 50, 150)),
            PinballBumper(cx=260, cy=1050, radius=34, color=(0, 255, 200)),
            PinballBumper(cx=820, cy=1050, radius=34, color=(0, 255, 200)),
            PinballBumper(cx=540, cy=1320, radius=40, color=(255, 215, 0)),
        ]

        # Spinners (Rotating hazards)
        self.spinners = [
            Spinner(cx=300, cy=860, length=150, speed=0.04, blades=2, color=(0, 230, 255)),
            Spinner(cx=780, cy=860, length=150, speed=-0.04, blades=2, color=(0, 230, 255)),
            Spinner(cx=320, cy=1200, length=130, speed=-0.035, blades=2, color=(255, 100, 200)),
            Spinner(cx=760, cy=1200, length=130, speed=0.035, blades=2, color=(255, 100, 200)),
        ]

        self.finish_line_y = 1620
        self.finishers = []
        self.particles = []
        self.audio_events = []

        self.font_title = pygame.font.SysFont("Arial", 46, bold=True)
        self.font_sub = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_name = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 58, bold=True)
        self.font_podium = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_cta = pygame.font.SysFont("Arial", 28, bold=True)

    def render_frame(self, frame_idx):
        t = frame_idx / self.fps
        surface = pygame.Surface((self.width, self.height))
        # Deep space neon backdrop with subtle gradient glow
        surface.fill((10, 12, 26))

        # 1. Outer Neon Boundary Walls
        pygame.draw.line(surface, (0, 220, 255), (60, 230), (60, self.finish_line_y + 120), 8)
        pygame.draw.line(surface, (0, 220, 255), (self.width - 60, 230), (self.width - 60, self.finish_line_y + 120), 8)
        # Inner accent light
        pygame.draw.line(surface, (255, 255, 255), (64, 230), (64, self.finish_line_y + 120), 2)
        pygame.draw.line(surface, (255, 255, 255), (self.width - 64, 230), (self.width - 64, self.finish_line_y + 120), 2)

        # 2. Animated Laser Elimination Danger Zone
        pulse_alpha = int(180 + 75 * math.sin(frame_idx * 0.15))
        laser_surf = pygame.Surface((self.width - 120, 16), pygame.SRCALPHA)
        laser_surf.fill((255, 40, 70, pulse_alpha))
        surface.blit(laser_surf, (60, self.finish_line_y - 8))
        pygame.draw.line(surface, (255, 255, 255), (60, self.finish_line_y), (self.width - 60, self.finish_line_y), 3)

        elim_text = self.font_sub.render("--- DANGER: ELIMINATION LASER (OUT!) ---", True, (255, 90, 100))
        surface.blit(elim_text, elim_text.get_rect(center=(self.width // 2, self.finish_line_y - 25)))

        # 3. Update & Draw Obstacles (Pinball Bumpers & Spinners)
        for b in self.bumpers:
            b.update()
            b.draw(surface)

        for sp in self.spinners:
            sp.update()
            sp.draw(surface)

        # 4. Draw Pegs with glowing neon centers
        for px, py in self.pegs:
            pygame.draw.circle(surface, (40, 55, 90), (px, py), 9)
            pygame.draw.circle(surface, (140, 220, 255), (px, py), 5)
            pygame.draw.circle(surface, (255, 255, 255), (px, py), 2)

        # 5. Physics Update for Marbles
        base_gravity = max(0.08, min(0.22, 2.6 / (self.duration_sec * 0.85)))
        for m in self.marbles:
            if not m.finished:
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

                # Pinball Bumper collisions
                for bmp in self.bumpers:
                    if bmp.check_collision(m):
                        self.audio_events.append((t, 780.0, True))
                        # Bumper blast sparks
                        for _ in range(16):
                            self.particles.append(Particle(m.x, m.y, bmp.color, speed_mult=1.4))

                # Spinner collisions
                for sp in self.spinners:
                    if sp.check_collision(m):
                        self.audio_events.append((t, 640.0, False))

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
                            if random.random() < 0.25:
                                m.vy -= random.uniform(0.5, 2.0)
                            freq = 300 + (py / self.height) * 520
                            self.audio_events.append((t, freq, False))

                # Elimination Check
                if m.y >= self.finish_line_y:
                    m.finished = True
                    m.finish_time = t
                    self.finishers.append(m)
                    self.audio_events.append((t, 180.0 + len(self.finishers) * 25, False))
                    # Elimination laser burst
                    for _ in range(18):
                        self.particles.append(Particle(m.x, self.finish_line_y, (255, 60, 80), speed_mult=1.2))

                m.update()

            # Render Marbles with 3D Spherical Specular Shading
            for idx, (tx, ty) in enumerate(m.trail):
                alpha = int(140 * (idx + 1) / len(m.trail))
                surf = pygame.Surface((m.radius * 2, m.radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*m.color, alpha), (m.radius, m.radius), int(m.radius * 0.75))
                surface.blit(surf, (int(tx - m.radius), int(ty - m.radius)))

            if not m.finished or (m.finished and t - m.finish_time < 0.4):
                # Glowing outer halo
                halo_surf = pygame.Surface((m.radius * 3, m.radius * 3), pygame.SRCALPHA)
                pygame.draw.circle(halo_surf, (*m.color, 65), (int(m.radius * 1.5), int(m.radius * 1.5)), int(m.radius * 1.4))
                surface.blit(halo_surf, (int(m.x - m.radius * 1.5), int(m.y - m.radius * 1.5)))

                # 3D Base sphere
                pygame.draw.circle(surface, m.color, (int(m.x), int(m.y)), m.radius)
                # Shaded inner shadow
                pygame.draw.circle(surface, (15, 18, 30), (int(m.x), int(m.y)), m.radius, 2)
                # 3D Specular highlight
                pygame.draw.circle(surface, (255, 255, 255), (int(m.x - 5), int(m.y - 5)), int(m.radius * 0.38))

                # Name Tag
                txt = self.font_name.render(m.name[:3], True, (255, 255, 255))
                surface.blit(txt, txt.get_rect(center=(int(m.x), int(m.y - 25))))

        # 6. Particles update & render
        for p in self.particles[:]:
            p.update()
            p.draw(surface)
            if p.life <= 0:
                self.particles.remove(p)

        # 7. Esports Live Survival HUD
        alive_marbles = [m for m in self.marbles if not m.finished]
        progress = frame_idx / self.total_frames

        title = self.font_title.render("MARBLE SURVIVAL TOURNAMENT", True, (255, 255, 255))
        surface.blit(title, title.get_rect(center=(self.width // 2, 75)))

        sub_text = f"LAST COLOR STANDING WINS!  |  ALIVE: {len(alive_marbles)} / 8"
        sub = self.font_sub.render(sub_text, True, (0, 255, 220))
        surface.blit(sub, sub.get_rect(center=(self.width // 2, 135)))

        # 8. Dramatic Winner Card (Shown strictly in the climax / final 22% of the video)
        show_winner = (progress >= 0.76) or (len(alive_marbles) <= 1 and progress >= 0.65)
        if show_winner:
            remaining = sorted(alive_marbles, key=lambda m: m.y)
            full_ranking = remaining + list(reversed(self.finishers))
            winner = full_ranking[0]
            p2 = full_ranking[1] if len(full_ranking) > 1 else None
            p3 = full_ranking[2] if len(full_ranking) > 2 else None

            # Confetti fireworks
            for _ in range(5):
                cx = random.randint(100, self.width - 100)
                cy = random.randint(500, 1300)
                confetti_colors = [(255, 60, 60), (60, 150, 255), (60, 255, 120), (255, 220, 50), (220, 80, 255), (0, 255, 255)]
                self.particles.append(Particle(cx, cy, random.choice(confetti_colors), speed_mult=1.8))

            # Glassmorphic Card
            card_w = 920
            card_h = 440
            card_x = (self.width - card_w) // 2
            card_y = 660

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (14, 16, 32, 245), (0, 0, card_w, card_h), border_radius=28)
            pygame.draw.rect(card_surf, winner.color, (0, 0, card_w, card_h), width=5, border_radius=28)
            pygame.draw.rect(card_surf, (255, 255, 255, 60), (4, 4, card_w - 8, card_h - 8), width=2, border_radius=26)
            surface.blit(card_surf, (card_x, card_y))

            # Card Header
            crown_txt = self.font_sub.render("--- LAST COLOR STANDING ---", True, (255, 215, 0))
            surface.blit(crown_txt, crown_txt.get_rect(center=(self.width // 2, card_y + 45)))

            # Winner text
            win_name_surf = self.font_big.render(f"{winner.name} IS THE WINNER!", True, winner.color)
            surface.blit(win_name_surf, win_name_surf.get_rect(center=(self.width // 2, card_y + 115)))

            # Standings
            p1_txt = self.font_podium.render(f"1ST PLACE (CHAMPION): {winner.name}", True, (255, 220, 50))
            p2_name = p2.name if p2 else "..."
            p3_name = p3.name if p3 else "..."
            p2_txt = self.font_podium.render(f"2ND PLACE: {p2_name}", True, (210, 220, 230))
            p3_txt = self.font_podium.render(f"3RD PLACE: {p3_name}", True, (205, 127, 50))

            surface.blit(p1_txt, p1_txt.get_rect(center=(self.width // 2, card_y + 190)))
            surface.blit(p2_txt, p2_txt.get_rect(center=(self.width // 2, card_y + 245)))
            surface.blit(p3_txt, p3_txt.get_rect(center=(self.width // 2, card_y + 300)))

            cta_txt = self.font_cta.render("DID YOUR COLOR SURVIVE? COMMENT BELOW!", True, (0, 255, 220))
            surface.blit(cta_txt, cta_txt.get_rect(center=(self.width // 2, card_y + 375)))

        # Progress bar
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
