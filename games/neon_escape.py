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
        speed = random.uniform(2, 9) * speed_mult
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0  # 1.0 to 0.0
        self.decay = random.uniform(0.025, 0.05)
        self.radius = random.uniform(3, 7)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.96
        self.vy *= 0.96
        self.life -= self.decay

    def draw(self, surface):
        if self.life > 0:
            alpha = int(self.life * 255)
            r, g, b = self.color
            surf = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (r, g, b, alpha), (int(self.radius), int(self.radius)), int(self.radius))
            surface.blit(surf, (int(self.x - self.radius), int(self.y - self.radius)))

class Segment:
    def __init__(self, start_angle, end_angle, health=2):
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.health = health
        self.max_health = health
        self.alive = True

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            self.alive = False
            return True  # Shattered
        return False

class Ring:
    def __init__(self, radius, thickness, num_segments, rot_speed, base_color):
        self.radius = radius
        self.thickness = thickness
        self.num_segments = num_segments
        self.rot_speed = rot_speed
        self.rotation = random.uniform(0, 2 * math.pi)
        self.base_color = base_color
        self.segments = []
        
        seg_angle = (2 * math.pi) / num_segments
        gap = 0.08  # Radians gap between segments
        for i in range(num_segments):
            s_ang = i * seg_angle + gap / 2
            e_ang = (i + 1) * seg_angle - gap / 2
            # 2 hits for middle ring, 3 hits for outer ring
            hp = random.choice([2, 3])
            self.segments.append(Segment(s_ang, e_ang, health=hp))

    def update(self):
        self.rotation = (self.rotation + self.rot_speed) % (2 * math.pi)

    def draw(self, surface, center_x, center_y):
        rect = pygame.Rect(
            int(center_x - self.radius),
            int(center_y - self.radius),
            int(self.radius * 2),
            int(self.radius * 2)
        )
        for seg in self.segments:
            if not seg.alive:
                continue
            
            # Color shifts to warmer alert color as health decreases
            if seg.health == 1:
                col = (255, 100, 100) # Warning red/orange
            elif seg.health == 2:
                col = self.base_color
            else:
                col = (120, 220, 255)

            start = (seg.start_angle + self.rotation) % (2 * math.pi)
            end = (seg.end_angle + self.rotation) % (2 * math.pi)

            # Draw outer glow arc
            pygame.draw.arc(surface, col, rect, start, end, self.thickness)


class NeonEscapeGame:
    def __init__(self, duration_sec=30, width=VIDEO_WIDTH, height=VIDEO_HEIGHT, fps=FPS):
        pygame.init()
        self.width = width
        self.height = height
        self.fps = fps
        self.duration_sec = duration_sec
        self.total_frames = int(duration_sec * fps)

        self.center_x = width // 2
        self.center_y = height // 2

        # Physics ball setup
        self.ball_x = float(self.center_x + random.randint(-40, 40))
        self.ball_y = float(self.center_y + random.randint(-40, 40))
        speed = 10.0
        angle = random.uniform(0.2, math.pi * 1.8)
        self.ball_vx = math.cos(angle) * speed
        self.ball_vy = math.sin(angle) * speed
        self.ball_radius = 16
        self.ball_color = (0, 255, 200)

        # Concentric Rings (Inner, Middle, Outer)
        self.rings = [
            Ring(radius=220, thickness=16, num_segments=6, rot_speed=0.015, base_color=(0, 220, 255)),
            Ring(radius=340, thickness=18, num_segments=8, rot_speed=-0.012, base_color=(180, 80, 255)),
            Ring(radius=460, thickness=20, num_segments=10, rot_speed=0.009, base_color=(255, 50, 180)),
        ]

        self.particles = []
        self.trail = []
        self.bounce_count = 0
        self.escaped = False

        # Audio event collector: (timestamp, freq, is_shatter)
        self.audio_events = []
        # Musical scale (A minor pentatonic / ascending frequencies)
        self.base_notes = [220, 246.94, 261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25, 783.99, 880.00]

        # Font setup (use default if custom not present)
        self.font_title = pygame.font.SysFont("Arial", 46, bold=True)
        self.font_ui = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 62, bold=True)
        self.font_sub = pygame.font.SysFont("Arial", 28, bold=True)

    def render_frame(self, frame_idx):
        t = frame_idx / self.fps
        surface = pygame.Surface((self.width, self.height))
        # Sleek dark cyber background with subtle gradient
        surface.fill((8, 10, 22))

        # Ambient decorative grid or circle markers
        pygame.draw.circle(surface, (18, 24, 45), (self.center_x, self.center_y), 520, 2)
        pygame.draw.circle(surface, (14, 18, 35), (self.center_x, self.center_y), 100, 1)

        # 1. Update rings
        for ring in self.rings:
            ring.update()
            ring.draw(surface, self.center_x, self.center_y)

        # 2. Physics Update: Ball movement
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy
        # Gravity / micro drift towards center or down
        self.ball_vy += 0.08

        dx = self.ball_x - self.center_x
        dy = self.ball_y - self.center_y
        dist = math.sqrt(dx * dx + dy * dy)
        ball_angle = math.atan2(dy, dx) % (2 * math.pi)

        # 3. Collision with rings
        for r_idx, ring in enumerate(self.rings):
            min_r = ring.radius - ring.thickness / 2
            max_r = ring.radius + ring.thickness / 2

            if (min_r - self.ball_radius) <= dist <= (max_r + self.ball_radius):
                # Check which segment covers ball_angle
                rel_angle = (ball_angle - ring.rotation) % (2 * math.pi)
                for seg in ring.segments:
                    if seg.alive and seg.start_angle <= rel_angle <= seg.end_angle:
                        # Collision detected!
                        # Calculate normal vector
                        norm_x = dx / (dist + 1e-6)
                        norm_y = dy / (dist + 1e-6)

                        # Dot product of velocity and normal
                        dot = self.ball_vx * norm_x + self.ball_vy * norm_y
                        if (dist < ring.radius and dot > 0) or (dist > ring.radius and dot < 0):
                            self.ball_vx -= 2 * dot * norm_x
                            self.ball_vy -= 2 * dot * norm_y

                            # Speed increase to raise tension
                            self.ball_vx *= 1.015
                            self.ball_vy *= 1.015
                            
                            self.bounce_count += 1
                            # In final 30% of video, ball power increases to guarantee thrilling breakout
                            if frame_idx > self.total_frames * 0.65:
                                seg.health = 1
                            shattered = seg.hit()

                            # Audio frequency rises with bounce count
                            note_idx = (self.bounce_count * 2) % len(self.base_notes)
                            freq = self.base_notes[note_idx] * (1.0 + min(self.bounce_count * 0.01, 0.8))
                            self.audio_events.append((t, freq, shattered))

                            # Spawn impact particles
                            for _ in range(16 if not shattered else 35):
                                p_color = (255, 240, 100) if shattered else ring.base_color
                                self.particles.append(Particle(self.ball_x, self.ball_y, p_color, speed_mult=1.5 if shattered else 1.0))
                            break

        # Climax breakout trigger in last 20% of video if not yet escaped
        if frame_idx > self.total_frames * 0.78 and not self.escaped:
            # Force outward breakout
            out_ang = math.atan2(dy, dx)
            self.ball_vx = math.cos(out_ang) * 22
            self.ball_vy = math.sin(out_ang) * 22
            self.escaped = True
            self.audio_events.append((t, 990.0, True))
            for _ in range(80):
                self.particles.append(Particle(self.ball_x, self.ball_y, (0, 255, 180), speed_mult=2.5))

        # Check outer boundary escape
        if dist > 550 and not self.escaped:
            self.escaped = True
            # Massive celebration explosion
            self.audio_events.append((t, 990.0, True))
            for _ in range(80):
                self.particles.append(Particle(self.ball_x, self.ball_y, (0, 255, 180), speed_mult=2.5))

        # 4. Trail update & render
        self.trail.append((self.ball_x, self.ball_y))
        if len(self.trail) > 16:
            self.trail.pop(0)

        for i, (tx, ty) in enumerate(self.trail):
            ratio = (i + 1) / len(self.trail)
            tr_radius = int(self.ball_radius * ratio * 0.8)
            if tr_radius > 0:
                alpha = int(140 * ratio)
                surf = pygame.Surface((tr_radius * 2, tr_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*self.ball_color, alpha), (tr_radius, tr_radius), tr_radius)
                surface.blit(surf, (int(tx - tr_radius), int(ty - tr_radius)))

        # 5. Draw Ball with glowing bloom
        # Outer glow
        glow_surf = pygame.Surface((self.ball_radius * 4, self.ball_radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.ball_color, 70), (self.ball_radius * 2, self.ball_radius * 2), self.ball_radius * 2)
        surface.blit(glow_surf, (int(self.ball_x - self.ball_radius * 2), int(self.ball_y - self.ball_radius * 2)))
        # Inner solid core
        pygame.draw.circle(surface, (255, 255, 255), (int(self.ball_x), int(self.ball_y)), self.ball_radius - 3)
        pygame.draw.circle(surface, self.ball_color, (int(self.ball_x), int(self.ball_y)), self.ball_radius, 3)

        # 6. Particles update & render
        for p in self.particles[:]:
            p.update()
            p.draw(surface)
            if p.life <= 0:
                self.particles.remove(p)

        # 7. Cinematic UI Overlay (Headers & Stats)
        # Header Box
        header_surf = self.font_title.render("ESCAPE THE NEON MAZE", True, (255, 255, 255))
        h_rect = header_surf.get_rect(center=(self.width // 2, 160))
        surface.blit(header_surf, h_rect)

        sub_surf = self.font_ui.render("CAN IT BREAK OUT? WATCH TILL END!", True, (0, 255, 220))
        s_rect = sub_surf.get_rect(center=(self.width // 2, 220))
        surface.blit(sub_surf, s_rect)

        # Stats Bar (Bottom)
        status_label = "ESCAPED!" if self.escaped else "IN PROGRESS"
        stats_text = f"BOUNCES: {self.bounce_count}   |   STATUS: {status_label}"
        color_stat = (50, 255, 120) if self.escaped else (255, 200, 80)
        bot_surf = self.font_ui.render(stats_text, True, color_stat)
        b_rect = bot_surf.get_rect(center=(self.width // 2, 1750))
        surface.blit(bot_surf, b_rect)

        # Dramatic Escape Celebration Card
        if self.escaped:
            # Continuous celebratory fireworks
            for _ in range(4):
                fx = random.randint(150, self.width - 150)
                fy = random.randint(500, 1300)
                self.particles.append(Particle(fx, fy, random.choice([(0, 255, 200), (255, 220, 50), (255, 50, 180), (120, 240, 255)]), speed_mult=1.8))

            card_w = 920
            card_h = 420
            card_x = (self.width - card_w) // 2
            card_y = 750

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (12, 16, 32, 240), (0, 0, card_w, card_h), border_radius=28)
            pygame.draw.rect(card_surf, (0, 255, 200), (0, 0, card_w, card_h), width=5, border_radius=28)
            pygame.draw.rect(card_surf, (255, 255, 255, 60), (4, 4, card_w - 8, card_h - 8), width=2, border_radius=26)
            surface.blit(card_surf, (card_x, card_y))

            # Header
            crown_txt = self.font_ui.render("--- MISSION COMPLETE ---", True, (255, 215, 0))
            surface.blit(crown_txt, crown_txt.get_rect(center=(self.width // 2, card_y + 50)))

            # Main Victory Text
            win_txt = self.font_big.render("ESCAPE SUCCESSFUL!", True, (0, 255, 200))
            surface.blit(win_txt, win_txt.get_rect(center=(self.width // 2, card_y + 125)))

            # Stats line
            b_info = self.font_ui.render(f"TOTAL BOUNCES: {self.bounce_count}  |  STATUS: WINNER!", True, (255, 255, 255))
            surface.blit(b_info, b_info.get_rect(center=(self.width // 2, card_y + 215)))

            # Engagement Call to action
            cta_txt = self.font_sub.render("DID YOU PREDICT THE ESCAPE? COMMENT BELOW!", True, (255, 220, 50))
            surface.blit(cta_txt, cta_txt.get_rect(center=(self.width // 2, card_y + 310)))

        # Progress bar
        progress = frame_idx / self.total_frames
        bar_w = 800
        bar_h = 14
        bx = (self.width - bar_w) // 2
        by = 1800
        pygame.draw.rect(surface, (40, 40, 60), (bx, by, bar_w, bar_h), border_radius=7)
        pygame.draw.rect(surface, (0, 255, 200), (bx, by, int(bar_w * progress), bar_h), border_radius=7)

        return pygame.image.tostring(surface, "RGB")

    def generate_video(self, output_path: Path):
        output_path = Path(output_path)
        print(f"[NeonEscape] Generating {self.duration_sec}s video ({self.total_frames} frames)...")

        renderer = VideoRenderer(output_path=output_path, width=self.width, height=self.height, fps=self.fps)
        renderer.start()

        for frame_idx in range(self.total_frames):
            frame_bytes = self.render_frame(frame_idx)
            renderer.write_frame(frame_bytes)

            if frame_idx % 120 == 0 or frame_idx == self.total_frames - 1:
                percent = int((frame_idx + 1) / self.total_frames * 100)
                print(f"  -> Rendering progress: {percent}% ({frame_idx+1}/{self.total_frames})")

        print("[NeonEscape] Synthesizing procedural bounce audio...")
        audio = ProceduralAudioEngine(duration_sec=self.duration_sec)
        audio.add_subtle_background_pulse(bpm=125.0, volume=0.18)

        for (timestamp, freq, shattered) in self.audio_events:
            audio.add_tone(start_time=timestamp, freq=freq, duration=0.22, volume=0.65)
            if shattered:
                audio.add_explosion(start_time=timestamp, volume=0.7)

        temp_wav = output_path.with_suffix(".temp.wav")
        audio.export_wav(temp_wav)

        print("[NeonEscape] Muxing video and audio into final MP4...")
        final_file = renderer.finalize_with_audio(temp_wav)
        print(f"[NeonEscape] Done! Video saved at: {final_file}")
        return final_file
