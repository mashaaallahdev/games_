import math
import random
import numpy as np
import pygame
from pathlib import Path
from core.config import VIDEO_WIDTH, VIDEO_HEIGHT, FPS
from core.audio_synth import ProceduralAudioEngine
from core.video_renderer import VideoRenderer

# ==============================================================================
# 8 UNIQUE PROCEDURAL BALL TYPES
# Each ball has its own distinct personality, rendering style, and particle trail
# ==============================================================================
BALL_TYPES = [
    {
        "id": "solar_phoenix",
        "name": "SOLAR PHOENIX",
        "core_color": (255, 255, 240),
        "body_color": (255, 140, 20),
        "glow_color": (255, 60, 0),
        "trail_color": (255, 190, 60),
        "style": "fire",
        "sound_pitch": 1.0,
    },
    {
        "id": "cyber_lightning",
        "name": "CYBER LIGHTNING",
        "core_color": (240, 255, 255),
        "body_color": (0, 220, 255),
        "glow_color": (0, 120, 255),
        "trail_color": (160, 245, 255),
        "style": "electric",
        "sound_pitch": 1.25,
    },
    {
        "id": "cosmic_void",
        "name": "COSMIC VOID",
        "core_color": (255, 230, 255),
        "body_color": (210, 50, 255),
        "glow_color": (140, 0, 220),
        "trail_color": (240, 160, 255),
        "style": "cosmic",
        "sound_pitch": 0.85,
    },
    {
        "id": "emerald_matrix",
        "name": "EMERALD MATRIX",
        "core_color": (230, 255, 235),
        "body_color": (40, 255, 110),
        "glow_color": (0, 190, 70),
        "trail_color": (150, 255, 190),
        "style": "matrix",
        "sound_pitch": 1.1,
    },
    {
        "id": "crimson_meteor",
        "name": "CRIMSON METEOR",
        "core_color": (255, 240, 220),
        "body_color": (255, 45, 65),
        "glow_color": (200, 10, 30),
        "trail_color": (255, 130, 90),
        "style": "meteor",
        "sound_pitch": 0.75,
    },
    {
        "id": "golden_supernova",
        "name": "GOLDEN SUPERNOVA",
        "core_color": (255, 255, 255),
        "body_color": (255, 215, 30),
        "glow_color": (255, 150, 0),
        "trail_color": (255, 240, 140),
        "style": "gold",
        "sound_pitch": 1.35,
    },
    {
        "id": "arctic_blizzard",
        "name": "ARCTIC BLIZZARD",
        "core_color": (255, 255, 255),
        "body_color": (130, 225, 255),
        "glow_color": (40, 170, 255),
        "trail_color": (205, 245, 255),
        "style": "frost",
        "sound_pitch": 1.4,
    },
    {
        "id": "disco_chrome",
        "name": "DISCO CHROME",
        "core_color": (255, 255, 255),
        "body_color": (255, 90, 200),
        "glow_color": (0, 255, 220),
        "trail_color": (255, 180, 240),
        "style": "chrome",
        "sound_pitch": 1.15,
    },
]

# ==============================================================================
# 6 CURATED COLOR PALETTES FOR WALLS
# ==============================================================================
COLOR_THEMES = [
    {
        "name": "CYBERPUNK NEON",
        "colors": [(0, 240, 255), (255, 40, 180), (180, 50, 255)],
        "bg_glow": (0, 40, 80),
    },
    {
        "name": "INFERNO BLAZE",
        "colors": [(255, 210, 30), (255, 120, 20), (255, 40, 40)],
        "bg_glow": (80, 20, 10),
    },
    {
        "name": "SYNTHWAVE 1984",
        "colors": [(255, 60, 150), (255, 170, 30), (150, 40, 255)],
        "bg_glow": (50, 10, 70),
    },
    {
        "name": "TOXIC MATRIX",
        "colors": [(40, 255, 120), (20, 240, 220), (0, 200, 100)],
        "bg_glow": (10, 50, 25),
    },
    {
        "name": "DEEP GALAXY",
        "colors": [(140, 240, 255), (200, 80, 255), (80, 140, 255)],
        "bg_glow": (20, 20, 60),
    },
    {
        "name": "GOLDEN ROYALE",
        "colors": [(255, 190, 40), (255, 130, 20), (255, 230, 140)],
        "bg_glow": (60, 45, 10),
    },
]

# ==============================================================================
# 4 WALL ARCHITECTURAL STYLES
# ==============================================================================
WALL_STYLES = [
    "CYBER_LASER",    # Sleek, ultra-bright laser ring with bright gap beacons
    "DOUBLE_NEON",   # Dual parallel concentric rails with connecting cross-struts
    "DASHED_CIRCUIT", # High-tech segmented circuit tracks with tick notches
    "RUNIC_GEAR",    # Perimeter chevrons pointing along rotation
]


class Particle:
    """Dynamic particles for bounces, trails, and breakthrough explosions."""
    def __init__(self, x, y, color, speed_mult=1.0, life=1.0, radius=5.0, decay=0.03):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2.5, 9.0) * speed_mult
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = float(life)
        self.max_life = float(life)
        self.decay = float(decay)
        self.radius = float(radius)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= self.decay

    def draw(self, surface):
        if self.life > 0:
            alpha = max(0, min(255, int((self.life / self.max_life) * 255)))
            r, g, b = self.color
            rad = max(1, int(self.radius * (self.life / self.max_life)))
            surf = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (r, g, b, alpha), (rad, rad), rad)
            surface.blit(surf, (int(self.x - rad), int(self.y - rad)))


class MovingNeonWall:
    """
    A rotating neon wall with an escape gap.
    Guarantees 100% mathematical unity between visual rendering and physics:
    - Center is (center_x, center_y).
    - Angular position theta in [0, 2*pi).
    - Gap is strictly [rotation, rotation + gap_radians].
    - Solid wall is strictly [rotation + gap_radians, rotation + 2*pi].
    - When escaped, gap_closed becomes True: wall permanently seals and becomes a solid ring.
    - Architectural styles: CYBER_LASER, DOUBLE_NEON, DASHED_CIRCUIT, RUNIC_GEAR.
    """
    def __init__(self, radius, thickness, gap_degrees, rot_speed, color, name="WALL", style="CYBER_LASER"):
        self.radius = float(radius)
        self.thickness = int(thickness)
        self.half_thick = self.thickness / 2.0
        self.inner_radius = self.radius - self.half_thick
        self.outer_radius = self.radius + self.half_thick

        self.gap_degrees = float(gap_degrees)
        self.gap_radians = math.radians(gap_degrees)
        self.rot_speed = float(rot_speed)
        self.rotation = random.uniform(0, 2 * math.pi)
        self.color = color
        self.name = name
        self.style = style

        self.gap_closed = False
        self.seal_anim = 0.0  # 1.0 when sealed, decays to 0.0
        self.unlock_time = 0.0
        self.is_unlocked = False

    def update(self, current_time=0.0):
        self.rotation = (self.rotation + self.rot_speed) % (2 * math.pi)
        if self.seal_anim > 0:
            self.seal_anim = max(0.0, self.seal_anim - 0.035)
        if current_time >= self.unlock_time:
            self.is_unlocked = True

    def close_gap(self):
        self.gap_closed = True
        self.seal_anim = 1.0

    def get_gap_angles(self):
        """Returns normalized (start_angle, end_angle) of the escape gap."""
        return self.rotation, (self.rotation + self.gap_radians)

    def is_angle_in_gap(self, angle, margin_radians=0.0):
        """
        Checks if given angle falls within the escape gap.
        Must be unlocked and not closed.
        """
        if self.gap_closed or not self.is_unlocked:
            return False
        rel = (angle - self.rotation) % (2 * math.pi)
        return (margin_radians <= rel <= (self.gap_radians - margin_radians))

    def get_tip_positions(self, center_x, center_y):
        """Returns coordinates of Tip 1 (start) and Tip 2 (end) of the gap."""
        t1_x = center_x + self.radius * math.cos(self.rotation)
        t1_y = center_y + self.radius * math.sin(self.rotation)
        end_ang = self.rotation + self.gap_radians
        t2_x = center_x + self.radius * math.cos(end_ang)
        t2_y = center_y + self.radius * math.sin(end_ang)
        return (t1_x, t1_y), (t2_x, t2_y)

    def draw(self, surface, center_x, center_y):
        # Determine current primary color
        main_color = self.color
        if self.seal_anim > 0:
            flash_amt = self.seal_anim
            main_color = (
                min(255, int(self.color[0] + (255 - self.color[0]) * flash_amt)),
                min(255, int(self.color[1] + (255 - self.color[1]) * flash_amt)),
                min(255, int(self.color[2] + (255 - self.color[2]) * flash_amt)),
            )

        if self.gap_closed and self.seal_anim <= 0:
            # -------------------------------------------------------------
            # FULLY SEALED WALL: Complete unbroken ring
            # -------------------------------------------------------------
            self._draw_full_ring(surface, center_x, center_y, main_color)
        else:
            # -------------------------------------------------------------
            # OPEN WALL: Arc with escape gap
            # -------------------------------------------------------------
            self._draw_open_arc(surface, center_x, center_y, main_color)

            # If currently sealing, draw laser bridge closing the gap!
            if self.seal_anim > 0:
                self._draw_seal_bridge(surface, center_x, center_y)

    def _draw_full_ring(self, surface, center_x, center_y, color):
        R = int(self.radius)
        T = self.thickness
        # Outer soft glow
        glow_surf = pygame.Surface((R * 2 + T * 4, R * 2 + T * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, 45), (R + T * 2, R + T * 2), R + T // 2, T + 6)
        surface.blit(glow_surf, (int(center_x - R - T * 2), int(center_y - R - T * 2)))

        # Solid ring
        pygame.draw.circle(surface, color, (int(center_x), int(center_y)), R, T)
        # Bright core laser
        pygame.draw.circle(surface, (255, 255, 255), (int(center_x), int(center_y)), R, max(2, T // 4))

        # Architectural style accents on sealed ring
        if self.style == "DOUBLE_NEON":
            pygame.draw.circle(surface, (255, 255, 255), (int(center_x), int(center_y)), int(self.inner_radius), 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(center_x), int(center_y)), int(self.outer_radius), 2)

    def _draw_open_arc(self, surface, center_x, center_y, color):
        # Arc strictly from (rotation + gap_radians) to (rotation + 2*pi)
        solid_start = self.rotation + self.gap_radians
        solid_end = self.rotation + 2 * math.pi
        num_pts = 90
        angles = np.linspace(solid_start, solid_end, num_pts)

        # Primary track points
        pts = [(center_x + self.radius * math.cos(a), center_y + self.radius * math.sin(a)) for a in angles]

        # Draw main neon arc
        pygame.draw.lines(surface, color, False, pts, self.thickness)
        # Inner white laser core line
        pygame.draw.lines(surface, (255, 255, 255), False, pts, max(2, self.thickness // 4))

        # Style-specific visual accents
        if self.style == "DOUBLE_NEON":
            pts_in = [(center_x + self.inner_radius * math.cos(a), center_y + self.inner_radius * math.sin(a)) for a in angles[::2]]
            pts_out = [(center_x + self.outer_radius * math.cos(a), center_y + self.outer_radius * math.sin(a)) for a in angles[::2]]
            pygame.draw.lines(surface, (255, 255, 255), False, pts_in, 2)
            pygame.draw.lines(surface, (255, 255, 255), False, pts_out, 2)
            # Struts
            for p1, p2 in zip(pts_in[::4], pts_out[::4]):
                pygame.draw.line(surface, color, p1, p2, 2)

        elif self.style == "DASHED_CIRCUIT":
            # Circuit notches along perimeter
            for a in angles[::5]:
                nx = center_x + (self.outer_radius + 6) * math.cos(a)
                ny = center_y + (self.outer_radius + 6) * math.sin(a)
                mx = center_x + (self.outer_radius - 2) * math.cos(a)
                my = center_y + (self.outer_radius - 2) * math.sin(a)
                pygame.draw.line(surface, (255, 255, 255), (mx, my), (nx, ny), 3)

        elif self.style == "RUNIC_GEAR":
            # Gear teeth / chevrons along perimeter
            for a in angles[::6]:
                tx = center_x + (self.outer_radius + 8) * math.cos(a)
                ty = center_y + (self.outer_radius + 8) * math.sin(a)
                bx = center_x + self.radius * math.cos(a)
                by = center_y + self.radius * math.sin(a)
                pygame.draw.line(surface, color, (bx, by), (tx, ty), 4)

        # -------------------------------------------------------------
        # GLOWING CAPS & BEACONS / SECURITY BARRIERS AT ESCAPE GAP
        # -------------------------------------------------------------
        tip1, tip2 = self.get_tip_positions(center_x, center_y)
        cap_rad = self.thickness // 2

        # Tip 1 Cap
        pygame.draw.circle(surface, (255, 255, 255), (int(tip1[0]), int(tip1[1])), cap_rad)
        pygame.draw.circle(surface, color, (int(tip1[0]), int(tip1[1])), cap_rad + 3, 2)

        # Tip 2 Cap
        pygame.draw.circle(surface, (255, 255, 255), (int(tip2[0]), int(tip2[1])), cap_rad)
        pygame.draw.circle(surface, color, (int(tip2[0]), int(tip2[1])), cap_rad + 3, 2)

        if not self.is_unlocked:
            # Active security laser barrier across the locked gap
            pygame.draw.line(surface, (255, 50, 50), tip1, tip2, 4)
            pygame.draw.line(surface, (255, 200, 200), tip1, tip2, 2)
            mid_x = (tip1[0] + tip2[0]) / 2.0
            mid_y = (tip1[1] + tip2[1]) / 2.0
            pygame.draw.circle(surface, (255, 50, 50), (int(mid_x), int(mid_y)), 7)
            pygame.draw.circle(surface, (255, 255, 255), (int(mid_x), int(mid_y)), 3)
        else:
            # Pulsing Escape Direction Beacon (Arrow/Chevron at unlocked portal)
            mid_ang = self.rotation + self.gap_radians / 2.0
            beacon_x = center_x + self.radius * math.cos(mid_ang)
            beacon_y = center_y + self.radius * math.sin(mid_ang)
            pulse_r = int(self.thickness * 0.75 + math.sin(pygame.time.get_ticks() * 0.008) * 3)
            pygame.draw.circle(surface, (255, 255, 255), (int(beacon_x), int(beacon_y)), max(3, pulse_r), 2)
            pygame.draw.circle(surface, (0, 255, 220), (int(beacon_x), int(beacon_y)), max(1, pulse_r // 2))

    def _draw_seal_bridge(self, surface, center_x, center_y):
        """Draws dynamic energetic laser bridge sealing the escape gap shut."""
        t1, t2 = self.get_tip_positions(center_x, center_y)
        progress = 1.0 - self.seal_anim  # from 0 to 1
        cur_end = self.rotation + self.gap_radians * progress
        cur_x = center_x + self.radius * math.cos(cur_end)
        cur_y = center_y + self.radius * math.sin(cur_end)

        # Laser beam sealing the gap
        pygame.draw.line(surface, (255, 255, 255), t1, (cur_x, cur_y), self.thickness)
        pygame.draw.line(surface, self.color, t1, (cur_x, cur_y), self.thickness + 6)
        # Searing hot weld spark at leading edge
        pygame.draw.circle(surface, (255, 255, 255), (int(cur_x), int(cur_y)), self.thickness)


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

        # -------------------------------------------------------------
        # PROCEDURAL VARIETY: Unique Ball, Theme, Wall Style every run!
        # -------------------------------------------------------------
        self.ball = random.choice(BALL_TYPES)
        self.theme = random.choice(COLOR_THEMES)
        self.wall_style = random.choice(WALL_STYLES)

        print(f"[NeonEscape] Run Config -> Ball: {self.ball['name']} | Theme: {self.theme['name']} | Style: {self.wall_style}")

        # Ball physical parameters
        self.ball_radius = 16
        self.ball_x = float(self.center_x + random.randint(-20, 20))
        self.ball_y = float(self.center_y + random.randint(-20, 20))
        init_angle = random.uniform(0.2, math.pi * 1.8)
        init_speed = 12.0
        self.ball_vx = math.cos(init_angle) * init_speed
        self.ball_vy = math.sin(init_angle) * init_speed

        # Center core bumper
        self.core_radius = 42

        # Moving Neon Walls with progressively narrower escape gaps:
        # Ring 1: Radius 190, gap 65° (Wide, fast initial breakout)
        # Ring 2: Radius 325, gap 40° (Medium, high tension)
        # Ring 3: Radius 460, gap 25° (Narrow, thrilling climax)
        rot_dir = 1 if random.random() < 0.5 else -1
        colors = self.theme["colors"]
        self.walls = [
            MovingNeonWall(radius=190, thickness=16, gap_degrees=65, rot_speed=0.024 * rot_dir, color=colors[0], name="WALL 1", style=self.wall_style),
            MovingNeonWall(radius=325, thickness=18, gap_degrees=40, rot_speed=-0.019 * rot_dir, color=colors[1], name="WALL 2", style=self.wall_style),
            MovingNeonWall(radius=460, thickness=20, gap_degrees=25, rot_speed=0.015 * rot_dir, color=colors[2], name="WALL 3", style=self.wall_style),
        ]
        # Paced portal unlock schedules to guarantee maximum suspense and timely escape
        self.walls[0].unlock_time = self.duration_sec * 0.20
        self.walls[1].unlock_time = self.duration_sec * 0.48
        self.walls[2].unlock_time = self.duration_sec * 0.72

        # Stage State Machine:
        # 0   : Inside Chamber 0 (between Core and Wall 1)
        # 0.5 : Transiting through Wall 1 gap
        # 1   : Inside Chamber 1 (between Sealed Wall 1 and Wall 2)
        # 1.5 : Transiting through Wall 2 gap
        # 2   : Inside Chamber 2 (between Sealed Wall 2 and Wall 3)
        # 2.5 : Transiting through Wall 3 gap
        # 3   : ESCAPED! Ball moves away freely into outer space!
        self.stage = 0.0
        self.escaped = False
        self.escape_time = None
        self.bounce_count = 0

        # Audio and Visual FX
        self.particles = []
        self.trail = []
        self.audio_events = []
        self.base_notes = [220, 261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25, 783.99, 880.00, 1046.5]
        self.last_bounce_frame = -99

        # UI Banner
        self.banner_text = f"MISSION: ESCAPE THE {self.wall_style.replace('_', ' ')}"
        self.banner_timer = 90

        # Fonts
        self.font_title = pygame.font.SysFont("Arial", 46, bold=True)
        self.font_ui = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 44, bold=True)
        self.font_sub = pygame.font.SysFont("Arial", 24, bold=True)

    def _bounce_ball(self, norm_x, norm_y, radial_vel, t, note_freq=440.0, particle_color=None):
        """Inverts radial velocity across normal, registers audio event and particles."""
        self.ball_vx -= 2.0 * radial_vel * norm_x
        self.ball_vy -= 2.0 * radial_vel * norm_y
        self.bounce_count += 1
        self.audio_events.append((t, note_freq, False))
        if particle_color:
            for _ in range(3):
                self.particles.append(Particle(self.ball_x, self.ball_y, particle_color))

    def _guide_towards_gap(self, wall, strength=0.035):
        """
        Subtle director steering: gently curves velocity vector towards
        the approaching escape gap so pacing is guaranteed to be thrilling.
        """
        gap_mid = (wall.rotation + wall.gap_radians / 2.0) % (2 * math.pi)
        target_x = self.center_x + wall.radius * math.cos(gap_mid)
        target_y = self.center_y + wall.radius * math.sin(gap_mid)
        to_gap_x = target_x - self.ball_x
        to_gap_y = target_y - self.ball_y
        dist = math.hypot(to_gap_x, to_gap_y) + 1e-5
        self.ball_vx += (to_gap_x / dist) * strength
        self.ball_vy += (to_gap_y / dist) * strength

    def _check_tip_collision(self, wall):
        """Checks and resolves collision with both tips/caps of the wall gap."""
        t1, t2 = wall.get_tip_positions(self.center_x, self.center_y)
        for tx, ty in (t1, t2):
            dx = self.ball_x - tx
            dy = self.ball_y - ty
            d = math.hypot(dx, dy)
            min_d = self.ball_radius + wall.half_thick
            if d < min_d and d > 1e-4:
                nx = dx / d
                ny = dy / d
                dot = self.ball_vx * nx + self.ball_vy * ny
                if dot < 0:
                    self.ball_x = tx + nx * min_d
                    self.ball_y = ty + ny * min_d
                    self.ball_vx -= 2.0 * dot * nx
                    self.ball_vy -= 2.0 * dot * ny
                    self.bounce_count += 1
                    for _ in range(3):
                        self.particles.append(Particle(self.ball_x, self.ball_y, wall.color))
                    return True
        return False

    def update_physics(self, t, frame_idx=0):
        """
        Sub-stepped continuous collision detection (8 steps per frame):
        - Ball strictly bounces off solid neon walls with correct vector reflection.
        - Escapes ONLY happen when entering the exact angular gap.
        - When clearing a wall, that wall's gap permanently seals shut.
        - In Stage 3 (Escaped): ZERO outer walls! Ball flies freely off into space!
        """
        sub_steps = 8
        dt = 1.0 / sub_steps

        # Guide ball towards unlocked portal for prompt and dramatic breakthrough
        if self.stage == 0 and self.walls[0].is_unlocked:
            self._guide_towards_gap(self.walls[0], strength=0.08 * dt)
        elif self.stage == 1 and self.walls[1].is_unlocked:
            self._guide_towards_gap(self.walls[1], strength=0.09 * dt)
        elif self.stage == 2 and self.walls[2].is_unlocked:
            self._guide_towards_gap(self.walls[2], strength=0.11 * dt)

        for _ in range(sub_steps):
            # Apply velocity
            self.ball_x += self.ball_vx * dt
            self.ball_y += self.ball_vy * dt

            # If escaped, ball continues outward into freedom (no gravity, smooth glide into deep space)
            if self.stage >= 3:
                dx = self.ball_x - self.center_x
                dy = self.ball_y - self.center_y
                dist = math.hypot(dx, dy)
                norm_x = dx / (dist + 1e-5)
                norm_y = dy / (dist + 1e-5)
                target_spd = 19.0
                self.ball_vx = norm_x * target_spd
                self.ball_vy = norm_y * target_spd
                if random.random() < 0.25:
                    self.particles.append(Particle(self.ball_x, self.ball_y, self.ball["trail_color"], speed_mult=1.5, radius=6.0))
                continue

            # Gentle gravity inside maze
            self.ball_vy += 0.08 * dt

            dx = self.ball_x - self.center_x
            dy = self.ball_y - self.center_y
            dist = math.hypot(dx, dy)
            ball_angle = math.atan2(dy, dx) % (2 * math.pi)
            norm_x = dx / (dist + 1e-6)
            norm_y = dy / (dist + 1e-6)
            radial_vel = self.ball_vx * norm_x + self.ball_vy * norm_y

            # -------------------------------------------------------------
            # STAGE 0: Chamber 0 (Center Core to Wall 1)
            # -------------------------------------------------------------
            if self.stage == 0:
                # 1. Center Core Bumper Bounce
                if dist < self.core_radius + self.ball_radius and radial_vel < 0:
                    self.ball_x = self.center_x + norm_x * (self.core_radius + self.ball_radius)
                    self.ball_y = self.center_y + norm_y * (self.core_radius + self.ball_radius)
                    self._bounce_ball(norm_x, norm_y, radial_vel, t, 520.0 * self.ball["sound_pitch"], self.ball["glow_color"])

                # 2. Wall 1 Inner Boundary
                w1 = self.walls[0]
                if dist + self.ball_radius >= w1.inner_radius and radial_vel > 0:
                    ang_margin = math.asin(min(0.9, self.ball_radius / w1.inner_radius))
                    if w1.is_angle_in_gap(ball_angle, margin_radians=ang_margin * 0.3):
                        # ENTER WALL 1 GAP!
                        self.stage = 0.5
                    else:
                        # Solid bounce off inner surface of Wall 1
                        self.ball_x = self.center_x + norm_x * (w1.inner_radius - self.ball_radius)
                        self.ball_y = self.center_y + norm_y * (w1.inner_radius - self.ball_radius)
                        note = self.base_notes[self.bounce_count % len(self.base_notes)] * self.ball["sound_pitch"]
                        self._bounce_ball(norm_x, norm_y, radial_vel, t, note, w1.color)

            # -------------------------------------------------------------
            # STAGE 0.5: Transiting Wall 1 Gap
            # -------------------------------------------------------------
            elif self.stage == 0.5:
                w1 = self.walls[0]
                self._check_tip_collision(w1)

                if dist - self.ball_radius >= w1.outer_radius:
                    # OFFICIALLY CLEARED WALL 1!
                    self.stage = 1
                    w1.close_gap()  # Permanently sealed shut!
                    self.banner_text = f"{w1.name} ESCAPED! GAP SEALED"
                    self.banner_timer = 75
                    self.audio_events.append((t, 680.0 * self.ball["sound_pitch"], True))
                    for _ in range(35):
                        self.particles.append(Particle(self.ball_x, self.ball_y, w1.color, speed_mult=2.0, radius=7.0))
                elif dist + self.ball_radius <= w1.inner_radius and radial_vel < 0:
                    self.stage = 0

            # -------------------------------------------------------------
            # STAGE 1: Chamber 1 (Between Sealed Wall 1 and Wall 2)
            # -------------------------------------------------------------
            elif self.stage == 1:
                w1 = self.walls[0]
                w2 = self.walls[1]

                # 1. Bounce off Outer Surface of Sealed Wall 1 (Cannot go back in!)
                if dist - self.ball_radius <= w1.outer_radius and radial_vel < 0:
                    self.ball_x = self.center_x + norm_x * (w1.outer_radius + self.ball_radius)
                    self.ball_y = self.center_y + norm_y * (w1.outer_radius + self.ball_radius)
                    self._bounce_ball(norm_x, norm_y, radial_vel, t, 440.0 * self.ball["sound_pitch"], w1.color)

                # 2. Bounce or Escape through Inner Surface of Wall 2
                elif dist + self.ball_radius >= w2.inner_radius and radial_vel > 0:
                    ang_margin = math.asin(min(0.9, self.ball_radius / w2.inner_radius))
                    if w2.is_angle_in_gap(ball_angle, margin_radians=ang_margin * 0.3):
                        # ENTER WALL 2 GAP!
                        self.stage = 1.5
                    else:
                        # Solid bounce off inner surface of Wall 2
                        self.ball_x = self.center_x + norm_x * (w2.inner_radius - self.ball_radius)
                        self.ball_y = self.center_y + norm_y * (w2.inner_radius - self.ball_radius)
                        note = self.base_notes[(self.bounce_count * 2) % len(self.base_notes)] * self.ball["sound_pitch"]
                        self._bounce_ball(norm_x, norm_y, radial_vel, t, note, w2.color)

            # -------------------------------------------------------------
            # STAGE 1.5: Transiting Wall 2 Gap
            # -------------------------------------------------------------
            elif self.stage == 1.5:
                w2 = self.walls[1]
                self._check_tip_collision(w2)

                if dist - self.ball_radius >= w2.outer_radius:
                    # OFFICIALLY CLEARED WALL 2!
                    self.stage = 2
                    w2.close_gap()  # Permanently sealed shut!
                    self.banner_text = f"{w2.name} ESCAPED! GAP SEALED"
                    self.banner_timer = 75
                    self.audio_events.append((t, 840.0 * self.ball["sound_pitch"], True))
                    for _ in range(40):
                        self.particles.append(Particle(self.ball_x, self.ball_y, w2.color, speed_mult=2.2, radius=7.0))
                elif dist + self.ball_radius <= w2.inner_radius and radial_vel < 0:
                    self.stage = 1

            # -------------------------------------------------------------
            # STAGE 2: Chamber 2 (Between Sealed Wall 2 and Wall 3)
            # -------------------------------------------------------------
            elif self.stage == 2:
                w2 = self.walls[1]
                w3 = self.walls[2]

                # 1. Bounce off Outer Surface of Sealed Wall 2
                if dist - self.ball_radius <= w2.outer_radius and radial_vel < 0:
                    self.ball_x = self.center_x + norm_x * (w2.outer_radius + self.ball_radius)
                    self.ball_y = self.center_y + norm_y * (w2.outer_radius + self.ball_radius)
                    self._bounce_ball(norm_x, norm_y, radial_vel, t, 580.0 * self.ball["sound_pitch"], w2.color)

                # 2. Bounce or Escape through Inner Surface of Wall 3 (Narrowest gap!)
                elif dist + self.ball_radius >= w3.inner_radius and radial_vel > 0:
                    ang_margin = math.asin(min(0.9, self.ball_radius / w3.inner_radius))
                    if w3.is_angle_in_gap(ball_angle, margin_radians=ang_margin * 0.3):
                        # ENTER FINAL ESCAPE GAP!
                        self.stage = 2.5
                    else:
                        # Solid bounce off inner surface of Wall 3
                        self.ball_x = self.center_x + norm_x * (w3.inner_radius - self.ball_radius)
                        self.ball_y = self.center_y + norm_y * (w3.inner_radius - self.ball_radius)
                        note = self.base_notes[(self.bounce_count * 3) % len(self.base_notes)] * self.ball["sound_pitch"]
                        self._bounce_ball(norm_x, norm_y, radial_vel, t, note, w3.color)

            # -------------------------------------------------------------
            # STAGE 2.5: Transiting Wall 3 Gap (Final Climax!)
            # -------------------------------------------------------------
            elif self.stage == 2.5:
                w3 = self.walls[2]
                self._check_tip_collision(w3)

                if dist - self.ball_radius >= w3.outer_radius:
                    # FINAL ESCAPE ACHIEVED!
                    self.stage = 3
                    self.escaped = True
                    self.escape_time = t
                    w3.close_gap()  # Wall 3 seals behind!
                    self.banner_text = "FREEDOM! ESCAPED ALL NEON WALLS!"
                    self.banner_timer = 120
                    self.audio_events.append((t, 990.0 * self.ball["sound_pitch"], True))
                    self.audio_events.append((t + 0.12, 1320.0 * self.ball["sound_pitch"], True))
                    for _ in range(80):
                        self.particles.append(Particle(self.ball_x, self.ball_y, (255, 255, 255), speed_mult=3.0, radius=8.0))
                elif dist + self.ball_radius <= w3.inner_radius and radial_vel < 0:
                    self.stage = 2

    def _draw_ball(self, surface, x, y):
        """Draws the ball using its custom archetype visual styling."""
        style = self.ball["style"]
        rad = self.ball_radius
        glow = self.ball["glow_color"]
        body = self.ball["body_color"]
        core = self.ball["core_color"]

        # 1. Soft Radial Glow Halo
        glow_size = rad * 5
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*glow, 70), (glow_size, glow_size), glow_size)
        pygame.draw.circle(glow_surf, (*body, 110), (glow_size, glow_size), int(rad * 2.2))
        surface.blit(glow_surf, (int(x - glow_size), int(y - glow_size)))

        # 2. Main Spherical Body
        pygame.draw.circle(surface, body, (int(x), int(y)), rad)

        # 3. Archetype Distinctive Visual Features
        if style == "fire":
            # Fireball: pulsating flame rings and hot center
            pygame.draw.circle(surface, (255, 200, 50), (int(x), int(y)), rad - 3)
            pygame.draw.circle(surface, core, (int(x), int(y)), rad - 7)
        elif style == "electric":
            # Electric: bright cyan corona and white lightning cross
            pygame.draw.circle(surface, (180, 255, 255), (int(x), int(y)), rad - 4)
            pygame.draw.line(surface, (255, 255, 255), (int(x - 6), int(y)), (int(x + 6), int(y)), 2)
            pygame.draw.line(surface, (255, 255, 255), (int(x), int(y - 6)), (int(x), int(y + 6)), 2)
        elif style == "matrix":
            # Matrix: glowing cyber ring
            pygame.draw.circle(surface, (20, 60, 30), (int(x), int(y)), rad - 3)
            pygame.draw.circle(surface, (100, 255, 160), (int(x), int(y)), rad - 5, 2)
            pygame.draw.circle(surface, core, (int(x), int(y)), rad - 8)
        elif style == "gold":
            # Gold Supernova: 3D specular highlight and sunburst ring
            pygame.draw.circle(surface, (255, 240, 120), (int(x), int(y)), rad - 3)
            pygame.draw.circle(surface, core, (int(x), int(y)), rad - 6)
            pygame.draw.circle(surface, (255, 255, 255), (int(x - rad * 0.3), int(y - rad * 0.3)), 4)
        else:
            # Default / Cosmic / Frost: Specular 3D highlight
            pygame.draw.circle(surface, core, (int(x), int(y)), rad - 5)
            pygame.draw.circle(surface, (255, 255, 255), (int(x - rad * 0.35), int(y - rad * 0.35)), 4)

    def render_frame(self, frame_idx):
        t = frame_idx / self.fps
        surface = pygame.Surface((self.width, self.height))

        # Deep cosmic ambient backdrop
        surface.fill((8, 10, 20))

        # Ambient background theme glow
        bg_col = self.theme["bg_glow"]
        ambient_glow = pygame.Surface((900, 900), pygame.SRCALPHA)
        pygame.draw.circle(ambient_glow, (*bg_col, 55), (450, 450), 440)
        surface.blit(ambient_glow, (self.center_x - 450, self.center_y - 450))

        # Decorative orbit guide lines
        pygame.draw.circle(surface, (16, 22, 40), (self.center_x, self.center_y), 520, 1)

        # -------------------------------------------------------------
        # CENTER BUMPER CORE
        # -------------------------------------------------------------
        core_glow = pygame.Surface((self.core_radius * 4, self.core_radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(core_glow, (*self.ball["glow_color"], 55), (self.core_radius * 2, self.core_radius * 2), int(self.core_radius * 1.5))
        surface.blit(core_glow, (int(self.center_x - self.core_radius * 2), int(self.center_y - self.core_radius * 2)))

        pygame.draw.circle(surface, (20, 26, 45), (self.center_x, self.center_y), self.core_radius)
        pygame.draw.circle(surface, self.ball["body_color"], (self.center_x, self.center_y), self.core_radius, 4)
        pygame.draw.circle(surface, (255, 255, 255), (self.center_x, self.center_y), self.core_radius // 2)

        # -------------------------------------------------------------
        # 1. UPDATE & DRAW MOVING NEON WALLS
        # -------------------------------------------------------------
        for w in self.walls:
            w.update(current_time=t)
            w.draw(surface, self.center_x, self.center_y)

        # -------------------------------------------------------------
        # 2. PHYSICS UPDATE
        # -------------------------------------------------------------
        self.update_physics(t, frame_idx)

        # -------------------------------------------------------------
        # 3. BALL MOTION TRAIL
        # -------------------------------------------------------------
        if math.isfinite(self.ball_x) and math.isfinite(self.ball_y):
            self.trail.append((self.ball_x, self.ball_y))
        if len(self.trail) > 18:
            self.trail.pop(0)

        for i, (tx, ty) in enumerate(self.trail):
            if -120 <= tx <= self.width + 120 and -120 <= ty <= self.height + 120:
                ratio = (i + 1) / len(self.trail)
                tr_rad = int(self.ball_radius * ratio * 0.85)
                if tr_rad > 0:
                    alpha = int(160 * ratio)
                    surf = pygame.Surface((tr_rad * 2, tr_rad * 2), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (*self.ball["trail_color"], alpha), (tr_rad, tr_rad), tr_rad)
                    surface.blit(surf, (int(tx - tr_rad), int(ty - tr_rad)))

        # -------------------------------------------------------------
        # 4. DRAW BALL (Only if within or near viewport)
        # -------------------------------------------------------------
        if -150 <= self.ball_x <= self.width + 150 and -150 <= self.ball_y <= self.height + 150:
            self._draw_ball(surface, self.ball_x, self.ball_y)

        # -------------------------------------------------------------
        # 5. PARTICLES UPDATE & DRAW
        # -------------------------------------------------------------
        for p in self.particles[:]:
            p.update()
            p.draw(surface)
            if p.life <= 0:
                self.particles.remove(p)

        # -------------------------------------------------------------
        # 6. HEADER OVERLAYS
        # -------------------------------------------------------------
        style_clean = self.wall_style.replace("_", " ")
        header_text = f"ESCAPE THE {style_clean} MAZE"
        head_surf = self.font_title.render(header_text, True, (255, 255, 255))
        surface.blit(head_surf, head_surf.get_rect(center=(self.width // 2, 110)))

        # Dynamic status subtitle
        if self.stage < 1:
            status_line = f"CHAMBER 1/3  |  BALL: {self.ball['name']}"
        elif self.stage < 2:
            status_line = f"CHAMBER 2/3  |  BOUNCES: {self.bounce_count}"
        elif self.stage < 3:
            status_line = f"FINAL CHAMBER 3/3  |  NARROWEST GAP!"
        else:
            status_line = "STATUS: ESCAPED TO FREEDOM! BALL MOVING AWAY!"

        sub_surf = self.font_ui.render(status_line, True, (0, 240, 255))
        surface.blit(sub_surf, sub_surf.get_rect(center=(self.width // 2, 165)))

        # Flash Banner
        if self.banner_timer > 0:
            self.banner_timer -= 1
            banner_surf = self.font_ui.render(self.banner_text, True, (255, 225, 50))
            surface.blit(banner_surf, banner_surf.get_rect(center=(self.width // 2, 220)))

        # -------------------------------------------------------------
        # 7. BOTTOM CELEBRATION CARD
        # Appears once escaped or displays real-time bounce telemetry
        # -------------------------------------------------------------
        if self.escaped:
            card_w = 940
            card_h = 240
            card_x = (self.width - card_w) // 2
            card_y = 1520

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (12, 16, 32, 235), (0, 0, card_w, card_h), border_radius=24)
            pygame.draw.rect(card_surf, self.ball["body_color"], (0, 0, card_w, card_h), width=4, border_radius=24)
            pygame.draw.rect(card_surf, (255, 255, 255, 50), (3, 3, card_w - 6, card_h - 6), width=2, border_radius=22)
            surface.blit(card_surf, (card_x, card_y))

            win_txt = self.font_big.render(f"ESCAPE COMPLETE! {self.ball['name']} WON!", True, self.ball["body_color"])
            surface.blit(win_txt, win_txt.get_rect(center=(self.width // 2, card_y + 55)))

            b_info = self.font_ui.render(f"TOTAL BOUNCES: {self.bounce_count}  |  ALL 3 WALLS CLEARED!", True, (255, 255, 255))
            surface.blit(b_info, b_info.get_rect(center=(self.width // 2, card_y + 115)))

            cta_txt = self.font_sub.render("DID YOU PREDICT THE ESCAPE? COMMENT BELOW!", True, (255, 220, 50))
            surface.blit(cta_txt, cta_txt.get_rect(center=(self.width // 2, card_y + 180)))
        else:
            stats_text = f"BOUNCES: {self.bounce_count}   |   BOUNCING ON INNER & OUTER WALLS"
            bot_surf = self.font_ui.render(stats_text, True, (255, 200, 80))
            surface.blit(bot_surf, bot_surf.get_rect(center=(self.width // 2, 1750)))

        # Bottom timeline progress bar
        progress = frame_idx / self.total_frames
        bar_w = 800
        bar_h = 14
        bx = (self.width - bar_w) // 2
        by = 1840
        pygame.draw.rect(surface, (40, 40, 60), (bx, by, bar_w, bar_h), border_radius=7)
        pygame.draw.rect(surface, self.ball["body_color"], (bx, by, int(bar_w * progress), bar_h), border_radius=7)

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
