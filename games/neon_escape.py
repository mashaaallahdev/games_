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

class MovingNeonRing:
    """
    Rotating neon ring with a specific escape gap.
    When the ball escapes through the gap, gap_closed becomes True,
    instantly filling the gap with solid neon wall so the ball cannot return!
    """
    def __init__(self, radius, thickness, gap_degrees, rot_speed, color, name="RING"):
        self.radius = radius
        self.thickness = thickness
        self.gap_degrees = gap_degrees
        self.gap_radians = math.radians(gap_degrees)
        self.rot_speed = rot_speed
        self.rotation = random.uniform(0, 2 * math.pi)
        self.color = color
        self.name = name
        self.gap_closed = False
        self.lock_flash_timer = 0

    def update(self):
        self.rotation = (self.rotation + self.rot_speed) % (2 * math.pi)
        if self.lock_flash_timer > 0:
            self.lock_flash_timer -= 1

    def is_in_gap(self, angle):
        """If gap is already closed, ball cannot pass."""
        if self.gap_closed:
            return False
        rel_ang = (angle - self.rotation) % (2 * math.pi)
        return rel_ang <= self.gap_radians

    def close_gap(self):
        """Permanently seals the escape gap with solid neon wall."""
        self.gap_closed = True
        self.lock_flash_timer = 20

    def draw(self, surface, center_x, center_y):
        rect = pygame.Rect(
            int(center_x - self.radius),
            int(center_y - self.radius),
            int(self.radius * 2),
            int(self.radius * 2)
        )

        draw_color = (255, 255, 255) if self.lock_flash_timer > 0 else self.color

        if self.gap_closed:
            # Fully sealed 360-degree continuous circle
            pygame.draw.circle(surface, draw_color, (center_x, center_y), self.radius, self.thickness)
        else:
            # Draw rotating arc with visible escape gap
            solid_start = (self.rotation + self.gap_radians) % (2 * math.pi)
            solid_end = self.rotation % (2 * math.pi)
            pygame.draw.arc(surface, draw_color, rect, solid_start, solid_end, self.thickness)

            # Glowing rounded cap edges at the escape gap
            e1_x = center_x + self.radius * math.cos(self.rotation)
            e1_y = center_y + self.radius * math.sin(self.rotation)
            pygame.draw.circle(surface, (255, 255, 255), (int(e1_x), int(e1_y)), self.thickness // 2)
            pygame.draw.circle(surface, draw_color, (int(e1_x), int(e1_y)), self.thickness // 2 + 2, 2)

            gap_end = self.rotation + self.gap_radians
            e2_x = center_x + self.radius * math.cos(gap_end)
            e2_y = center_y + self.radius * math.sin(gap_end)
            pygame.draw.circle(surface, (255, 255, 255), (int(e2_x), int(e2_y)), self.thickness // 2)
            pygame.draw.circle(surface, draw_color, (int(e2_x), int(e2_y)), self.thickness // 2 + 2, 2)


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

        # Physics ball setup (Never vanishes!)
        self.ball_x = float(self.center_x + random.randint(-30, 30))
        self.ball_y = float(self.center_y + random.randint(-30, 30))
        speed = 12.0
        angle = random.uniform(0.3, math.pi * 1.7)
        self.ball_vx = math.cos(angle) * speed
        self.ball_vy = math.sin(angle) * speed
        self.ball_radius = 14
        self.ball_color = (0, 255, 200)

        # Center glowing core bumper (Innermost bounce wall)
        self.core_radius = 40

        # Outer boundary ring for free space celebration (Radius = 520)
        self.outer_boundary_radius = 520

        # Progressive difficulty:
        # Ring 1 (innermost): BIGGER gap (65°)
        # Ring 2 (middle): NARROWER gap (40°)
        # Ring 3 (outermost): NARROWEST gap (24°)
        self.rings = [
            MovingNeonRing(radius=190, thickness=16, gap_degrees=65, rot_speed=0.024, color=(0, 220, 255), name="RING 1"),
            MovingNeonRing(radius=325, thickness=18, gap_degrees=40, rot_speed=-0.019, color=(210, 75, 255), name="RING 2"),
            MovingNeonRing(radius=455, thickness=20, gap_degrees=24, rot_speed=0.015, color=(255, 50, 160), name="RING 3"),
        ]

        # Current Space:
        # 0 = Inside Ring 1 (bounces between Center Core and Ring 1 inner wall)
        # 1 = Between Ring 1 (sealed outer wall) and Ring 2 inner wall
        # 2 = Between Ring 2 (sealed outer wall) and Ring 3 inner wall
        # 3 = Fully escaped into Outer Space!
        self.current_space = 0
        self.escaped = False
        self.escape_time = None
        self.bounce_count = 0

        self.particles = []
        self.trail = []
        self.audio_events = []
        self.base_notes = [220, 246.94, 261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25, 783.99, 880.00]

        self.stage_banner = "SPACE 1: FIND GAP 1 (WIDE)"
        self.banner_timer = 0

        # Fonts
        self.font_title = pygame.font.SysFont("Arial", 46, bold=True)
        self.font_ui = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 52, bold=True)
        self.font_sub = pygame.font.SysFont("Arial", 26, bold=True)

    def update_physics(self, t):
        """
        Sub-stepped continuous physics:
        - Ball bounces between inner and outer wall of its current space.
        - NEVER jumps or skips a wall.
        - When the ball passes through a gap:
            1. It advances to the next outer space.
            2. The escaped ring's gap is INSTANTLY FILLED/LOCKED!
            3. The ball cannot return.
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
            # SPACE 0: Innermost chamber (Center Core to Ring 1 Inner Wall)
            # -------------------------------------------------------------
            if self.current_space == 0:
                # 1. Inner Bounce: Center Core
                if dist < self.core_radius + self.ball_radius and dot < 0:
                    self.ball_x = self.center_x + norm_x * (self.core_radius + self.ball_radius)
                    self.ball_y = self.center_y + norm_y * (self.core_radius + self.ball_radius)
                    self.ball_vx -= 2 * dot * norm_x
                    self.ball_vy -= 2 * dot * norm_y
                    self.bounce_count += 1
                    self.audio_events.append((t, 520.0, False))
                    for _ in range(3):
                        self.particles.append(Particle(self.ball_x, self.ball_y, (255, 40, 150), speed_mult=1.2))

                # 2. Outer Bounce: Ring 1 Inner Wall
                ring1 = self.rings[0]
                r1_inner = ring1.radius - ring1.thickness / 2
                if dist > r1_inner - self.ball_radius and dot > 0:
                    if ring1.is_in_gap(ball_angle):
                        # ESCAPE RING 1!
                        self.current_space = 1
                        ring1.close_gap()  # GAP IS FILLED & LOCKED! Cannot go back!
                        self.stage_banner = "RING 1 ESCAPED! GAP SEALED 🔒"
                        self.banner_timer = 70
                        self.audio_events.append((t, 660.0, True))
                        for _ in range(30):
                            self.particles.append(Particle(self.ball_x, self.ball_y, ring1.color, speed_mult=1.8))
                    else:
                        # Solid bounce off Ring 1 Inner Wall
                        self.ball_x = self.center_x + norm_x * (r1_inner - self.ball_radius)
                        self.ball_y = self.center_y + norm_y * (r1_inner - self.ball_radius)
                        self.ball_vx -= 2 * dot * norm_x
                        self.ball_vy -= 2 * dot * norm_y
                        self.bounce_count += 1
                        self.audio_events.append((t, self.base_notes[self.bounce_count % len(self.base_notes)], False))
                        for _ in range(2):
                            self.particles.append(Particle(self.ball_x, self.ball_y, ring1.color))

            # -------------------------------------------------------------
            # SPACE 1: Channel between Ring 1 (Sealed Outer Wall) and Ring 2 Inner Wall
            # -------------------------------------------------------------
            elif self.current_space == 1:
                ring1 = self.rings[0]
                ring2 = self.rings[1]
                r1_outer = ring1.radius + ring1.thickness / 2
                r2_inner = ring2.radius - ring2.thickness / 2

                # 1. Inner Bounce: Ring 1 Outer Wall (Sealed - cannot go back!)
                if dist < r1_outer + self.ball_radius and dot < 0:
                    self.ball_x = self.center_x + norm_x * (r1_outer + self.ball_radius)
                    self.ball_y = self.center_y + norm_y * (r1_outer + self.ball_radius)
                    self.ball_vx -= 2 * dot * norm_x
                    self.ball_vy -= 2 * dot * norm_y
                    self.bounce_count += 1
                    self.audio_events.append((t, 460.0, False))
                    for _ in range(2):
                        self.particles.append(Particle(self.ball_x, self.ball_y, ring1.color))

                # 2. Outer Bounce: Ring 2 Inner Wall (Narrower gap 40°)
                elif dist > r2_inner - self.ball_radius and dot > 0:
                    if ring2.is_in_gap(ball_angle):
                        # ESCAPE RING 2!
                        self.current_space = 2
                        ring2.close_gap()  # GAP 2 IS FILLED & LOCKED!
                        self.stage_banner = "RING 2 ESCAPED! GAP SEALED 🔒"
                        self.banner_timer = 70
                        self.audio_events.append((t, 820.0, True))
                        for _ in range(30):
                            self.particles.append(Particle(self.ball_x, self.ball_y, ring2.color, speed_mult=1.8))
                    else:
                        # Solid bounce off Ring 2 Inner Wall
                        self.ball_x = self.center_x + norm_x * (r2_inner - self.ball_radius)
                        self.ball_y = self.center_y + norm_y * (r2_inner - self.ball_radius)
                        self.ball_vx -= 2 * dot * norm_x
                        self.ball_vy -= 2 * dot * norm_y
                        self.bounce_count += 1
                        self.audio_events.append((t, self.base_notes[(self.bounce_count * 2) % len(self.base_notes)], False))
                        for _ in range(2):
                            self.particles.append(Particle(self.ball_x, self.ball_y, ring2.color))

            # -------------------------------------------------------------
            # SPACE 2: Channel between Ring 2 (Sealed Outer Wall) and Ring 3 Inner Wall
            # -------------------------------------------------------------
            elif self.current_space == 2:
                ring2 = self.rings[1]
                ring3 = self.rings[2]
                r2_outer = ring2.radius + ring2.thickness / 2
                r3_inner = ring3.radius - ring3.thickness / 2

                # 1. Inner Bounce: Ring 2 Outer Wall (Sealed!)
                if dist < r2_outer + self.ball_radius and dot < 0:
                    self.ball_x = self.center_x + norm_x * (r2_outer + self.ball_radius)
                    self.ball_y = self.center_y + norm_y * (r2_outer + self.ball_radius)
                    self.ball_vx -= 2 * dot * norm_x
                    self.ball_vy -= 2 * dot * norm_y
                    self.bounce_count += 1
                    self.audio_events.append((t, 560.0, False))
                    for _ in range(2):
                        self.particles.append(Particle(self.ball_x, self.ball_y, ring2.color))

                # 2. Outer Bounce: Ring 3 Inner Wall (Narrowest gap 24° - High Tension!)
                elif dist > r3_inner - self.ball_radius and dot > 0:
                    if ring3.is_in_gap(ball_angle):
                        # FINAL ESCAPE!
                        self.current_space = 3
                        ring3.close_gap()  # Ring 3 sealed behind!
                        self.escaped = True
                        self.escape_time = t
                        self.stage_banner = "FINAL ESCAPE ACHIEVED! 🏆"
                        self.banner_timer = 90
                        self.audio_events.append((t, 990.0, True))
                        self.audio_events.append((t + 0.15, 1200.0, True))
                        for _ in range(70):
                            self.particles.append(Particle(self.ball_x, self.ball_y, (0, 255, 200), speed_mult=2.8))
                    else:
                        # Solid bounce off Ring 3 Inner Wall
                        self.ball_x = self.center_x + norm_x * (r3_inner - self.ball_radius)
                        self.ball_y = self.center_y + norm_y * (r3_inner - self.ball_radius)
                        self.ball_vx -= 2 * dot * norm_x
                        self.ball_vy -= 2 * dot * norm_y
                        self.bounce_count += 1
                        self.audio_events.append((t, self.base_notes[(self.bounce_count * 3) % len(self.base_notes)], False))
                        for _ in range(2):
                            self.particles.append(Particle(self.ball_x, self.ball_y, ring3.color))

            # -------------------------------------------------------------
            # SPACE 3: Free Outer Orbit (Ball remains 100% visible, bouncing in freedom!)
            # -------------------------------------------------------------
            elif self.current_space == 3:
                ring3 = self.rings[2]
                r3_outer = ring3.radius + ring3.thickness / 2

                # Bounce off outer boundary ring
                if dist > self.outer_boundary_radius - self.ball_radius and dot > 0:
                    self.ball_x = self.center_x + norm_x * (self.outer_boundary_radius - self.ball_radius)
                    self.ball_y = self.center_y + norm_y * (self.outer_boundary_radius - self.ball_radius)
                    self.ball_vx -= 2 * dot * norm_x
                    self.ball_vy -= 2 * dot * norm_y
                    self.audio_events.append((t, 880.0, False))
                    for _ in range(4):
                        self.particles.append(Particle(self.ball_x, self.ball_y, (0, 255, 200), speed_mult=1.5))
                # Bounce off Ring 3 outer wall
                elif dist < r3_outer + self.ball_radius and dot < 0:
                    self.ball_x = self.center_x + norm_x * (r3_outer + self.ball_radius)
                    self.ball_y = self.center_y + norm_y * (r3_outer + self.ball_radius)
                    self.ball_vx -= 2 * dot * norm_x
                    self.ball_vy -= 2 * dot * norm_y
                    self.audio_events.append((t, 740.0, False))

    def render_frame(self, frame_idx):
        t = frame_idx / self.fps
        surface = pygame.Surface((self.width, self.height))
        surface.fill((8, 10, 22))

        # Ambient Outer Boundary Ring (Where ball celebrates after escape)
        pygame.draw.circle(surface, (20, 28, 55), (self.center_x, self.center_y), self.outer_boundary_radius, 2)
        
        # Center Core Glowing Bumper (Inner bounce wall in Space 0)
        core_glow = pygame.Surface((self.core_radius * 3, self.core_radius * 3), pygame.SRCALPHA)
        pygame.draw.circle(core_glow, (255, 40, 150, 45), (int(self.core_radius * 1.5), int(self.core_radius * 1.5)), int(self.core_radius * 1.3))
        surface.blit(core_glow, (int(self.center_x - self.core_radius * 1.5), int(self.center_y - self.core_radius * 1.5)))
        pygame.draw.circle(surface, (20, 24, 45), (self.center_x, self.center_y), self.core_radius)
        pygame.draw.circle(surface, (255, 40, 150), (self.center_x, self.center_y), self.core_radius, 4)
        pygame.draw.circle(surface, (255, 255, 255), (self.center_x, self.center_y), self.core_radius // 2)

        # 1. Update & Draw Moving Neon Rings
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

        # 4. Draw Ball with Glowing Halo (ALWAYS VISIBLE!)
        glow_surf = pygame.Surface((self.ball_radius * 4, self.ball_radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.ball_color, 80), (self.ball_radius * 2, self.ball_radius * 2), self.ball_radius * 2)
        surface.blit(glow_surf, (int(self.ball_x - self.ball_radius * 2), int(self.ball_y - self.ball_radius * 2)))

        # Inner solid core & specular reflection
        pygame.draw.circle(surface, (255, 255, 255), (int(self.ball_x), int(self.ball_y)), self.ball_radius - 3)
        pygame.draw.circle(surface, self.ball_color, (int(self.ball_x), int(self.ball_y)), self.ball_radius, 3)

        # 5. Particles update & render
        for p in self.particles[:]:
            p.update()
            p.draw(surface)
            if p.life <= 0:
                self.particles.remove(p)

        # 6. Cinematic Header Overlays
        header_surf = self.font_title.render("ESCAPE THE NEON CIRCLE", True, (255, 255, 255))
        surface.blit(header_surf, header_surf.get_rect(center=(self.width // 2, 110)))

        # Current Space & Gap Width Tracker
        if self.current_space == 0:
            status_line = "CURRENT: SPACE 1 / 3  |  TARGET: GAP 1 (WIDE)"
        elif self.current_space == 1:
            status_line = "CURRENT: SPACE 2 / 3  |  TARGET: GAP 2 (NARROW)"
        elif self.current_space == 2:
            status_line = "CURRENT: SPACE 3 / 3  |  TARGET: GAP 3 (TINY)"
        else:
            status_line = "STATUS: FULLY ESCAPED!"

        sub_surf = self.font_ui.render(status_line, True, (0, 255, 220))
        surface.blit(sub_surf, sub_surf.get_rect(center=(self.width // 2, 165)))

        # Gap Lock Banner Notification
        if self.banner_timer > 0:
            self.banner_timer -= 1
            banner_surf = self.font_ui.render(self.stage_banner, True, (255, 220, 50))
            surface.blit(banner_surf, banner_surf.get_rect(center=(self.width // 2, 220)))

        # 7. Non-Obtrusive Victory Banner (Cleanly framed at bottom so the ball remains visible!)
        if self.escaped:
            # Continuous fireworks
            for _ in range(5):
                fx = random.randint(100, self.width - 100)
                fy = random.randint(400, 1400)
                self.particles.append(Particle(fx, fy, random.choice([(0, 255, 200), (255, 220, 50), (255, 50, 180), (120, 240, 255)]), speed_mult=1.8))

            card_w = 940
            card_h = 240
            card_x = (self.width - card_w) // 2
            card_y = 1520

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (12, 16, 32, 235), (0, 0, card_w, card_h), border_radius=24)
            pygame.draw.rect(card_surf, (0, 255, 200), (0, 0, card_w, card_h), width=4, border_radius=24)
            pygame.draw.rect(card_surf, (255, 255, 255, 50), (3, 3, card_w - 6, card_h - 6), width=2, border_radius=22)
            surface.blit(card_surf, (card_x, card_y))

            win_txt = self.font_big.render("ESCAPE SUCCESSFUL! ALL 3 GAPS FOUND!", True, (0, 255, 200))
            surface.blit(win_txt, win_txt.get_rect(center=(self.width // 2, card_y + 55)))

            b_info = self.font_ui.render(f"TOTAL BOUNCES: {self.bounce_count}  |  STATUS: WINNER!", True, (255, 255, 255))
            surface.blit(b_info, b_info.get_rect(center=(self.width // 2, card_y + 115)))

            cta_txt = self.font_sub.render("DID YOU PREDICT THE ESCAPE? COMMENT BELOW!", True, (255, 220, 50))
            surface.blit(cta_txt, cta_txt.get_rect(center=(self.width // 2, card_y + 180)))
        else:
            # Normal bottom stats
            stats_text = f"BOUNCES: {self.bounce_count}   |   BOUNCING ON INNER & OUTER WALLS"
            bot_surf = self.font_ui.render(stats_text, True, (255, 200, 80))
            surface.blit(bot_surf, bot_surf.get_rect(center=(self.width // 2, 1750)))

        # Progress bar
        progress = frame_idx / self.total_frames
        bar_w = 800
        bar_h = 14
        bx = (self.width - bar_w) // 2
        by = 1840
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
