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
        self.life = 1.0
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

class RotatingRing:
    """
    A continuous glowing neon ring with ONE clearly visible small escape gap.
    The gap rotates continuously.
    """
    def __init__(self, radius, thickness, gap_degrees, rot_speed, color, name="RING"):
        self.radius = radius
        self.thickness = thickness
        self.gap_radians = math.radians(gap_degrees)
        self.rot_speed = rot_speed
        self.rotation = random.uniform(0, 2 * math.pi)
        self.color = color
        self.name = name

    def update(self):
        self.rotation = (self.rotation + self.rot_speed) % (2 * math.pi)

    def is_in_gap(self, angle):
        """Checks if a given angle (0 to 2pi) falls inside the small escape gap."""
        rel_ang = (angle - self.rotation) % (2 * math.pi)
        return rel_ang <= self.gap_radians

    def draw(self, surface, center_x, center_y):
        rect = pygame.Rect(
            int(center_x - self.radius),
            int(center_y - self.radius),
            int(self.radius * 2),
            int(self.radius * 2)
        )
        solid_start = (self.rotation + self.gap_radians) % (2 * math.pi)
        solid_end = self.rotation % (2 * math.pi)

        # Draw glowing neon arc (solid wall)
        pygame.draw.arc(surface, self.color, rect, solid_start, solid_end, self.thickness)

        # Draw glowing rounded cap caps at gap edges so the small escape is visually sharp
        e1_x = center_x + self.radius * math.cos(self.rotation)
        e1_y = center_y + self.radius * math.sin(self.rotation)
        pygame.draw.circle(surface, (255, 255, 255), (int(e1_x), int(e1_y)), self.thickness // 2)
        pygame.draw.circle(surface, self.color, (int(e1_x), int(e1_y)), self.thickness // 2 + 2, 2)

        gap_end = self.rotation + self.gap_radians
        e2_x = center_x + self.radius * math.cos(gap_end)
        e2_y = center_y + self.radius * math.sin(gap_end)
        pygame.draw.circle(surface, (255, 255, 255), (int(e2_x), int(e2_y)), self.thickness // 2)
        pygame.draw.circle(surface, self.color, (int(e2_x), int(e2_y)), self.thickness // 2 + 2, 2)


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
        self.ball_x = float(self.center_x + random.randint(-30, 30))
        self.ball_y = float(self.center_y + random.randint(-30, 30))
        speed = 12.0
        angle = random.uniform(0.3, math.pi * 1.7)
        self.ball_vx = math.cos(angle) * speed
        self.ball_vy = math.sin(angle) * speed
        self.ball_radius = 14
        self.ball_color = (0, 255, 200)

        # Center glowing core bumper (radius 36)
        self.core_radius = 36

        # 3 Concentric Rings with clearly defined small escape gaps
        # Space 0 = inside Ring 1 (between center core and Ring 1 inner wall)
        # Space 1 = channel between Ring 1 outer wall and Ring 2 inner wall
        # Space 2 = channel between Ring 2 outer wall and Ring 3 inner wall
        # Space 3 = escaped into open space!
        gap_size = 42 if duration_sec <= 15 else 36
        self.rings = [
            RotatingRing(radius=200, thickness=16, gap_degrees=gap_size, rot_speed=0.022, color=(0, 220, 255), name="RING 1"),
            RotatingRing(radius=330, thickness=18, gap_degrees=gap_size, rot_speed=-0.018, color=(200, 75, 255), name="RING 2"),
            RotatingRing(radius=460, thickness=20, gap_degrees=gap_size, rot_speed=0.015, color=(255, 50, 160), name="RING 3"),
        ]

        self.current_space = 0  # 0: Inner space, 1: Middle space, 2: Outer space, 3: Escaped!
        self.particles = []
        self.trail = []
        self.bounce_count = 0
        self.escaped = False
        self.escape_time = None
        self.stage_banner = "SPACE 1: FIND ESCAPE GAP 1"
        self.banner_timer = 0

        # Audio event collector: (timestamp, freq, is_breakthrough)
        self.audio_events = []
        self.base_notes = [220, 246.94, 261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25, 783.99, 880.00]

        # Font setup
        self.font_title = pygame.font.SysFont("Arial", 46, bold=True)
        self.font_ui = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 62, bold=True)
        self.font_sub = pygame.font.SysFont("Arial", 28, bold=True)

    def update_physics(self, t):
        """
        Sub-stepped continuous physics engine:
        Ensures the ball NEVER glitches or tunnels through walls.
        The ball bounces between inner and outer walls in its current space.
        It ONLY transitions from an inner space to an outer space when it physically hits the small escape gap!
        """
        sub_steps = 8
        dt = 1.0 / sub_steps

        for _ in range(sub_steps):
            self.ball_x += self.ball_vx * dt
            self.ball_y += self.ball_vy * dt
            self.ball_vy += 0.08 * dt  # Gentle gravity

            dx = self.ball_x - self.center_x
            dy = self.ball_y - self.center_y
            dist = math.hypot(dx, dy)
            ball_angle = math.atan2(dy, dx) % (2 * math.pi)
            norm_x = dx / (dist + 1e-6)
            norm_y = dy / (dist + 1e-6)
            dot = self.ball_vx * norm_x + self.ball_vy * norm_y

            # -------------------------------------------------------------
            # SPACE 0: Inner space (between center bumper and Ring 1 inner wall)
            # -------------------------------------------------------------
            if self.current_space == 0:
                # 1. Inner bounce: Center Core bumper
                if dist < self.core_radius + self.ball_radius and dot < 0:
                    self.ball_vx -= 2 * dot * norm_x
                    self.ball_vy -= 2 * dot * norm_y
                    self.bounce_count += 1
                    self.audio_events.append((t, 520.0, False))
                    for _ in range(3):
                        self.particles.append(Particle(self.ball_x, self.ball_y, (255, 40, 150), speed_mult=1.2))

                # 2. Outer bounce: Ring 1 inner wall
                ring1 = self.rings[0]
                r1_inner = ring1.radius - ring1.thickness / 2
                if dist > r1_inner - self.ball_radius and dot > 0:
                    if ring1.is_in_gap(ball_angle):
                        # SUCCESS: Passes through small escape gap 1 into Space 1!
                        self.current_space = 1
                        self.stage_banner = "ESCAPED TO SPACE 2! GAP 1 FOUND!"
                        self.banner_timer = 60
                        self.audio_events.append((t, 660.0, True))
                        for _ in range(25):
                            self.particles.append(Particle(self.ball_x, self.ball_y, ring1.color, speed_mult=1.8))
                    else:
                        # Solid bounce off Ring 1 inner wall back toward center!
                        self.ball_x = self.center_x + norm_x * (r1_inner - self.ball_radius)
                        self.ball_y = self.center_y + norm_y * (r1_inner - self.ball_radius)
                        self.ball_vx -= 2 * dot * norm_x
                        self.ball_vy -= 2 * dot * norm_y
                        self.bounce_count += 1
                        self.audio_events.append((t, self.base_notes[self.bounce_count % len(self.base_notes)], False))
                        for _ in range(2):
                            self.particles.append(Particle(self.ball_x, self.ball_y, ring1.color))

            # -------------------------------------------------------------
            # SPACE 1: Channel between Ring 1 (inner wall) and Ring 2 (outer wall)
            # -------------------------------------------------------------
            elif self.current_space == 1:
                ring1 = self.rings[0]
                ring2 = self.rings[1]
                r1_outer = ring1.radius + ring1.thickness / 2
                r2_inner = ring2.radius - ring2.thickness / 2

                # 1. Inner wall bounce: Bounces off Ring 1's outer wall (bouncing outward)
                if dist < r1_outer + self.ball_radius and dot < 0:
                    self.ball_x = self.center_x + norm_x * (r1_outer + self.ball_radius)
                    self.ball_y = self.center_y + norm_y * (r1_outer + self.ball_radius)
                    self.ball_vx -= 2 * dot * norm_x
                    self.ball_vy -= 2 * dot * norm_y
                    self.bounce_count += 1
                    self.audio_events.append((t, 440.0, False))
                    for _ in range(2):
                        self.particles.append(Particle(self.ball_x, self.ball_y, ring1.color))

                # 2. Outer wall bounce: Bounces off Ring 2's inner wall (bouncing inward)
                elif dist > r2_inner - self.ball_radius and dot > 0:
                    if ring2.is_in_gap(ball_angle):
                        # SUCCESS: Passes through small escape gap 2 into Space 2!
                        self.current_space = 2
                        self.stage_banner = "ESCAPED TO SPACE 3! GAP 2 FOUND!"
                        self.banner_timer = 60
                        self.audio_events.append((t, 820.0, True))
                        for _ in range(25):
                            self.particles.append(Particle(self.ball_x, self.ball_y, ring2.color, speed_mult=1.8))
                    else:
                        # Solid bounce off Ring 2 inner wall back inward!
                        self.ball_x = self.center_x + norm_x * (r2_inner - self.ball_radius)
                        self.ball_y = self.center_y + norm_y * (r2_inner - self.ball_radius)
                        self.ball_vx -= 2 * dot * norm_x
                        self.ball_vy -= 2 * dot * norm_y
                        self.bounce_count += 1
                        self.audio_events.append((t, self.base_notes[(self.bounce_count * 2) % len(self.base_notes)], False))
                        for _ in range(2):
                            self.particles.append(Particle(self.ball_x, self.ball_y, ring2.color))

            # -------------------------------------------------------------
            # SPACE 2: Channel between Ring 2 (inner wall) and Ring 3 (outer wall)
            # -------------------------------------------------------------
            elif self.current_space == 2:
                ring2 = self.rings[1]
                ring3 = self.rings[2]
                r2_outer = ring2.radius + ring2.thickness / 2
                r3_inner = ring3.radius - ring3.thickness / 2

                # 1. Inner wall bounce: Bounces off Ring 2's outer wall (bouncing outward)
                if dist < r2_outer + self.ball_radius and dot < 0:
                    self.ball_x = self.center_x + norm_x * (r2_outer + self.ball_radius)
                    self.ball_y = self.center_y + norm_y * (r2_outer + self.ball_radius)
                    self.ball_vx -= 2 * dot * norm_x
                    self.ball_vy -= 2 * dot * norm_y
                    self.bounce_count += 1
                    self.audio_events.append((t, 550.0, False))
                    for _ in range(2):
                        self.particles.append(Particle(self.ball_x, self.ball_y, ring2.color))

                # 2. Outer wall bounce: Bounces off Ring 3's inner wall (bouncing inward)
                elif dist > r3_inner - self.ball_radius and dot > 0:
                    if ring3.is_in_gap(ball_angle):
                        # SUCCESS: Passes through final escape gap 3 into OPEN FREEDOM!
                        self.current_space = 3
                        self.escaped = True
                        self.escape_time = t
                        self.stage_banner = "FINAL ESCAPE COMPLETE! VICTORY!"
                        self.banner_timer = 90
                        self.audio_events.append((t, 990.0, True))
                        self.audio_events.append((t + 0.15, 1200.0, True))
                        for _ in range(70):
                            self.particles.append(Particle(self.ball_x, self.ball_y, (0, 255, 200), speed_mult=2.8))
                    else:
                        # Solid bounce off Ring 3 inner wall back inward!
                        self.ball_x = self.center_x + norm_x * (r3_inner - self.ball_radius)
                        self.ball_y = self.center_y + norm_y * (r3_inner - self.ball_radius)
                        self.ball_vx -= 2 * dot * norm_x
                        self.ball_vy -= 2 * dot * norm_y
                        self.bounce_count += 1
                        self.audio_events.append((t, self.base_notes[(self.bounce_count * 3) % len(self.base_notes)], False))
                        for _ in range(2):
                            self.particles.append(Particle(self.ball_x, self.ball_y, ring3.color))

            # -------------------------------------------------------------
            # SPACE 3: Escaped into outside space!
            # -------------------------------------------------------------
            elif self.current_space == 3:
                # Ball flies freely outward with fireworks
                pass

    def render_frame(self, frame_idx):
        t = frame_idx / self.fps
        surface = pygame.Surface((self.width, self.height))
        surface.fill((8, 10, 22))

        # Ambient decorative grid rings
        pygame.draw.circle(surface, (18, 24, 45), (self.center_x, self.center_y), 530, 2)
        
        # Center Core Glowing Bumper (Inner bounce wall in Space 0)
        core_glow = pygame.Surface((self.core_radius * 3, self.core_radius * 3), pygame.SRCALPHA)
        pygame.draw.circle(core_glow, (255, 40, 150, 45), (int(self.core_radius * 1.5), int(self.core_radius * 1.5)), int(self.core_radius * 1.3))
        surface.blit(core_glow, (int(self.center_x - self.core_radius * 1.5), int(self.center_y - self.core_radius * 1.5)))
        pygame.draw.circle(surface, (20, 24, 45), (self.center_x, self.center_y), self.core_radius)
        pygame.draw.circle(surface, (255, 40, 150), (self.center_x, self.center_y), self.core_radius, 4)
        pygame.draw.circle(surface, (255, 255, 255), (self.center_x, self.center_y), self.core_radius // 2)

        # 1. Update & Draw Rings
        for ring in self.rings:
            ring.update()
            ring.draw(surface, self.center_x, self.center_y)

        # 2. Physics Update (Continuous Sub-stepped Collision)
        self.update_physics(t)

        # 3. Trail update & render
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

        # 4. Draw Ball with glowing bloom
        glow_surf = pygame.Surface((self.ball_radius * 4, self.ball_radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.ball_color, 75), (self.ball_radius * 2, self.ball_radius * 2), self.ball_radius * 2)
        surface.blit(glow_surf, (int(self.ball_x - self.ball_radius * 2), int(self.ball_y - self.ball_radius * 2)))

        # Inner solid core
        pygame.draw.circle(surface, (255, 255, 255), (int(self.ball_x), int(self.ball_y)), self.ball_radius - 3)
        pygame.draw.circle(surface, self.ball_color, (int(self.ball_x), int(self.ball_y)), self.ball_radius, 3)

        # 5. Particles update & render
        for p in self.particles[:]:
            p.update()
            p.draw(surface)
            if p.life <= 0:
                self.particles.remove(p)

        # 6. Cinematic UI Overlays
        header_surf = self.font_title.render("ESCAPE THE NEON CIRCLE", True, (255, 255, 255))
        surface.blit(header_surf, header_surf.get_rect(center=(self.width // 2, 130)))

        # Current Space Tracker
        space_name = f"CURRENT: SPACE {self.current_space + 1} / 3" if self.current_space < 3 else "STATUS: ESCAPED!"
        sub_surf = self.font_ui.render(f"{space_name}  |  BOUNCES: {self.bounce_count}", True, (0, 255, 220))
        surface.blit(sub_surf, sub_surf.get_rect(center=(self.width // 2, 190)))

        # Stage breakthrough notification
        if self.banner_timer > 0:
            self.banner_timer -= 1
            note_surf = self.font_ui.render(self.stage_banner, True, (255, 220, 50))
            surface.blit(note_surf, note_surf.get_rect(center=(self.width // 2, 250)))

        # Stats Bar (Bottom)
        status_label = "ESCAPED!" if self.escaped else "BOUNCING & SEEKING GAPS..."
        stats_text = f"BOUNCES: {self.bounce_count}   |   STATUS: {status_label}"
        color_stat = (50, 255, 120) if self.escaped else (255, 200, 80)
        bot_surf = self.font_ui.render(stats_text, True, color_stat)
        surface.blit(bot_surf, bot_surf.get_rect(center=(self.width // 2, 1750)))

        # Dramatic Escape Celebration Card (Shown when fully escaped in climax)
        if self.escaped:
            for _ in range(5):
                fx = random.randint(150, self.width - 150)
                fy = random.randint(500, 1300)
                self.particles.append(Particle(fx, fy, random.choice([(0, 255, 200), (255, 220, 50), (255, 50, 180), (120, 240, 255)]), speed_mult=1.8))

            card_w = 920
            card_h = 420
            card_x = (self.width - card_w) // 2
            card_y = 750

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (12, 16, 32, 245), (0, 0, card_w, card_h), border_radius=28)
            pygame.draw.rect(card_surf, (0, 255, 200), (0, 0, card_w, card_h), width=5, border_radius=28)
            pygame.draw.rect(card_surf, (255, 255, 255, 60), (4, 4, card_w - 8, card_h - 8), width=2, border_radius=26)
            surface.blit(card_surf, (card_x, card_y))

            crown_txt = self.font_ui.render("--- MISSION COMPLETE ---", True, (255, 215, 0))
            surface.blit(crown_txt, crown_txt.get_rect(center=(self.width // 2, card_y + 50)))

            win_txt = self.font_big.render("ESCAPE SUCCESSFUL!", True, (0, 255, 200))
            surface.blit(win_txt, win_txt.get_rect(center=(self.width // 2, card_y + 125)))

            b_info = self.font_ui.render(f"TOTAL BOUNCES: {self.bounce_count}  |  ALL 3 GAPS FOUND!", True, (255, 255, 255))
            surface.blit(b_info, b_info.get_rect(center=(self.width // 2, card_y + 215)))

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

        for (timestamp, freq, is_breakthrough) in self.audio_events:
            audio.add_tone(start_time=timestamp, freq=freq, duration=0.20, volume=0.65)
            if is_breakthrough:
                audio.add_explosion(start_time=timestamp, volume=0.75)

        temp_wav = output_path.with_suffix(".temp.wav")
        audio.export_wav(temp_wav)

        print("[NeonEscape] Muxing video and audio into final MP4...")
        final_file = renderer.finalize_with_audio(temp_wav)
        print(f"[NeonEscape] Done! Video saved at: {final_file}")
        return final_file
