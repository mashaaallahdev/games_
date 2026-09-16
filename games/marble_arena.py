import math
import random
import numpy as np
import pygame
from pathlib import Path
from core.config import VIDEO_WIDTH, VIDEO_HEIGHT, FPS
from core.audio_synth import ProceduralAudioEngine
from core.video_renderer import VideoRenderer

# ==============================================================================
# GLOBAL COUNTRY DATABASE (45+ Nations with Authentic Flag Patterns)
# ==============================================================================
COUNTRY_DATABASE = [
    # Americas
    {"code": "USA", "name": "United States", "primary": (218, 41, 28), "pattern": "canton_stripes", "stripe1": (218, 41, 28), "stripe2": (255, 255, 255), "canton": (10, 30, 120)},
    {"code": "BRA", "name": "Brazil", "primary": (0, 155, 58), "pattern": "brazil", "bg": (0, 155, 58), "rhombus": (254, 223, 0), "circle": (0, 39, 118)},
    {"code": "ARG", "name": "Argentina", "primary": (117, 170, 219), "pattern": "h_stripes", "stripes": [(117, 170, 219), (255, 255, 255), (117, 170, 219)], "sun": True},
    {"code": "CAN", "name": "Canada", "primary": (218, 41, 28), "pattern": "canada", "side": (218, 41, 28), "center": (255, 255, 255)},
    {"code": "MEX", "name": "Mexico", "primary": (0, 104, 71), "pattern": "v_stripes", "stripes": [(0, 104, 71), (255, 255, 255), (206, 17, 38)], "emblem": True},
    {"code": "COL", "name": "Colombia", "primary": (252, 209, 22), "pattern": "colombia", "stripes": [(252, 209, 22), (0, 56, 147), (206, 17, 38)]},
    {"code": "CHI", "name": "Chile", "primary": (213, 43, 30), "pattern": "chile", "bottom": (213, 43, 30), "top_right": (255, 255, 255), "canton": (0, 57, 166)},
    {"code": "JAM", "name": "Jamaica", "primary": (0, 119, 73), "pattern": "saltire", "bg": (0, 119, 73), "cross": (255, 215, 0), "side": (20, 20, 20)},

    # Europe
    {"code": "FRA", "name": "France", "primary": (0, 38, 84), "pattern": "v_stripes", "stripes": [(0, 38, 84), (255, 255, 255), (237, 41, 57)]},
    {"code": "GER", "name": "Germany", "primary": (221, 0, 0), "pattern": "h_stripes", "stripes": [(20, 20, 20), (221, 0, 0), (255, 206, 0)]},
    {"code": "GBR", "name": "United Kingdom", "primary": (1, 33, 105), "pattern": "union_jack", "bg": (1, 33, 105), "white_cross": (255, 255, 255), "red_cross": (200, 16, 46)},
    {"code": "ITA", "name": "Italy", "primary": (0, 146, 70), "pattern": "v_stripes", "stripes": [(0, 146, 70), (255, 255, 255), (206, 43, 55)]},
    {"code": "ESP", "name": "Spain", "primary": (241, 191, 0), "pattern": "spain", "stripes": [(170, 21, 27), (241, 191, 0), (170, 21, 27)]},
    {"code": "POR", "name": "Portugal", "primary": (255, 0, 0), "pattern": "portugal", "left": (0, 102, 0), "right": (255, 0, 0), "emblem": (255, 215, 0)},
    {"code": "NED", "name": "Netherlands", "primary": (174, 28, 40), "pattern": "h_stripes", "stripes": [(174, 28, 40), (255, 255, 255), (33, 70, 139)]},
    {"code": "BEL", "name": "Belgium", "primary": (253, 218, 36), "pattern": "v_stripes", "stripes": [(25, 25, 25), (253, 218, 36), (239, 51, 64)]},
    {"code": "SWE", "name": "Sweden", "primary": (0, 106, 167), "pattern": "nordic", "bg": (0, 106, 167), "cross": (254, 204, 0)},
    {"code": "NOR", "name": "Norway", "primary": (186, 12, 47), "pattern": "nordic_double", "bg": (186, 12, 47), "outer": (255, 255, 255), "inner": (0, 32, 91)},
    {"code": "SUI", "name": "Switzerland", "primary": (218, 41, 28), "pattern": "swiss", "bg": (218, 41, 28), "cross": (255, 255, 255)},
    {"code": "POL", "name": "Poland", "primary": (220, 20, 60), "pattern": "h_stripes", "stripes": [(255, 255, 255), (220, 20, 60)]},
    {"code": "GRE", "name": "Greece", "primary": (13, 94, 175), "pattern": "greece", "c1": (13, 94, 175), "c2": (255, 255, 255)},
    {"code": "TUR", "name": "Turkey", "primary": (227, 10, 23), "pattern": "crescent", "bg": (227, 10, 23), "fg": (255, 255, 255)},

    # Asia & Middle East
    {"code": "JPN", "name": "Japan", "primary": (188, 0, 45), "pattern": "circle", "bg": (255, 255, 255), "circle": (188, 0, 45)},
    {"code": "KOR", "name": "South Korea", "primary": (0, 71, 160), "pattern": "korea", "bg": (255, 255, 255), "top": (205, 46, 58), "bottom": (0, 71, 160)},
    {"code": "IND", "name": "India", "primary": (255, 153, 51), "pattern": "h_stripes", "stripes": [(255, 153, 51), (255, 255, 255), (19, 136, 8)], "chakra": True},
    {"code": "CHN", "name": "China", "primary": (222, 41, 16), "pattern": "star", "bg": (222, 41, 16), "star": (255, 222, 0)},
    {"code": "KSA", "name": "Saudi Arabia", "primary": (0, 108, 53), "pattern": "solid", "bg": (0, 108, 53), "accent": (255, 255, 255)},
    {"code": "UAE", "name": "United Arab Emirates", "primary": (0, 115, 47), "pattern": "uae", "left": (255, 0, 0), "stripes": [(0, 115, 47), (255, 255, 255), (20, 20, 20)]},
    {"code": "INA", "name": "Indonesia", "primary": (255, 0, 0), "pattern": "h_stripes", "stripes": [(255, 0, 0), (255, 255, 255)]},
    {"code": "VIE", "name": "Vietnam", "primary": (218, 37, 29), "pattern": "star", "bg": (218, 37, 29), "star": (255, 255, 0)},
    {"code": "PAK", "name": "Pakistan", "primary": (1, 65, 28), "pattern": "crescent_left", "bg": (1, 65, 28), "left": (255, 255, 255), "fg": (255, 255, 255)},
    {"code": "BAN", "name": "Bangladesh", "primary": (0, 106, 78), "pattern": "circle_offcenter", "bg": (0, 106, 78), "circle": (244, 42, 65)},
    {"code": "PHI", "name": "Philippines", "primary": (0, 56, 168), "pattern": "philippines", "top": (0, 56, 168), "bottom": (206, 17, 38), "triangle": (255, 255, 255), "sun": (252, 209, 22)},
    {"code": "THA", "name": "Thailand", "primary": (45, 42, 74), "pattern": "thailand", "colors": [(165, 25, 49), (255, 255, 255), (45, 42, 74)]},

    # Africa
    {"code": "NGA", "name": "Nigeria", "primary": (0, 135, 81), "pattern": "v_stripes", "stripes": [(0, 135, 81), (255, 255, 255), (0, 135, 81)]},
    {"code": "RSA", "name": "South Africa", "primary": (0, 122, 77), "pattern": "south_africa", "bg": (0, 122, 77), "top": (222, 56, 49), "bottom": (0, 35, 149), "gold": (255, 182, 18)},
    {"code": "EGY", "name": "Egypt", "primary": (206, 17, 38), "pattern": "h_stripes", "stripes": [(206, 17, 38), (255, 255, 255), (20, 20, 20)], "eagle": True},
    {"code": "MAR", "name": "Morocco", "primary": (193, 39, 45), "pattern": "morocco", "bg": (193, 39, 45), "star": (0, 98, 51)},
    {"code": "GHA", "name": "Ghana", "primary": (206, 17, 38), "pattern": "h_stripes", "stripes": [(206, 17, 38), (254, 203, 0), (0, 107, 63)], "star": (20, 20, 20)},
    {"code": "SEN", "name": "Senegal", "primary": (0, 133, 63), "pattern": "v_stripes", "stripes": [(0, 133, 63), (253, 239, 66), (227, 27, 35)], "star": (0, 133, 63)},
    {"code": "KEN", "name": "Kenya", "primary": (187, 0, 0), "pattern": "kenya", "top": (20, 20, 20), "mid": (187, 0, 0), "bot": (0, 102, 0), "white": (255, 255, 255)},
    {"code": "ALG", "name": "Algeria", "primary": (0, 98, 51), "pattern": "v_split", "c1": (0, 98, 51), "c2": (255, 255, 255), "fg": (210, 16, 52)},

    # Oceania
    {"code": "AUS", "name": "Australia", "primary": (0, 0, 139), "pattern": "canton_stars", "bg": (0, 0, 139), "c1": (255, 255, 255), "c2": (204, 0, 0)},
    {"code": "NZL", "name": "New Zealand", "primary": (0, 36, 125), "pattern": "canton_stars", "bg": (0, 36, 125), "c1": (255, 255, 255), "c2": (204, 0, 0)}
]

def render_flag_surface(country: dict, radius: int) -> pygame.Surface:
    """Renders a procedural 3D glossy circular flag marble texture."""
    d = radius * 2
    raw = pygame.Surface((d, d))
    pat = country.get("pattern", "solid")

    # 1. Base flag layout
    if pat == "v_stripes":
        stripes = country["stripes"]
        sw = d / len(stripes)
        for i, col in enumerate(stripes):
            pygame.draw.rect(raw, col, (int(i * sw), 0, int(sw) + 1, d))
        if country.get("emblem"):
            pygame.draw.circle(raw, (139, 69, 19), (radius, radius), int(radius * 0.22))
        if country.get("star"):
            pygame.draw.circle(raw, country["star"], (radius, radius), int(radius * 0.2))

    elif pat == "h_stripes":
        stripes = country["stripes"]
        sh = d / len(stripes)
        for i, col in enumerate(stripes):
            pygame.draw.rect(raw, col, (0, int(i * sh), d, int(sh) + 1))
        if country.get("sun") or country.get("chakra"):
            col = (255, 215, 0) if country.get("sun") else (0, 0, 139)
            pygame.draw.circle(raw, col, (radius, radius), int(radius * 0.22))
        if country.get("star"):
            pygame.draw.circle(raw, country["star"], (radius, radius), int(radius * 0.2))

    elif pat == "brazil":
        raw.fill(country["bg"])
        # Yellow rhombus
        pts = [(radius, 3), (d - 3, radius), (radius, d - 3), (3, radius)]
        pygame.draw.polygon(raw, country["rhombus"], pts)
        # Blue circle
        pygame.draw.circle(raw, country["circle"], (radius, radius), int(radius * 0.45))
        pygame.draw.arc(raw, (255, 255, 255), (radius - 12, radius - 12, 24, 24), 0.2, 2.8, 2)

    elif pat == "canada":
        raw.fill(country["center"])
        sw = int(d * 0.25)
        pygame.draw.rect(raw, country["side"], (0, 0, sw, d))
        pygame.draw.rect(raw, country["side"], (d - sw, 0, sw, d))
        pygame.draw.polygon(raw, country["side"], [(radius, radius - 8), (radius + 8, radius + 6), (radius - 8, radius + 6)])

    elif pat == "spain":
        stripes = country["stripes"]
        h1 = int(d * 0.25)
        h2 = int(d * 0.50)
        pygame.draw.rect(raw, stripes[0], (0, 0, d, h1))
        pygame.draw.rect(raw, stripes[1], (0, h1, d, h2))
        pygame.draw.rect(raw, stripes[2], (0, h1 + h2, d, d - (h1 + h2)))
        pygame.draw.circle(raw, (160, 20, 20), (int(radius * 0.7), radius), int(radius * 0.16))

    elif pat == "circle" or pat == "circle_offcenter":
        raw.fill(country["bg"])
        cx = radius if pat == "circle" else int(radius * 0.9)
        pygame.draw.circle(raw, country["circle"], (cx, radius), int(radius * 0.52))

    elif pat == "star":
        raw.fill(country["bg"])
        pygame.draw.circle(raw, country["star"], (radius, radius), int(radius * 0.38))

    elif pat == "nordic":
        raw.fill(country["bg"])
        cw = int(radius * 0.3)
        cx = int(radius * 0.75)
        pygame.draw.rect(raw, country["cross"], (0, radius - cw // 2, d, cw))
        pygame.draw.rect(raw, country["cross"], (cx - cw // 2, 0, cw, d))

    elif pat == "nordic_double":
        raw.fill(country["bg"])
        cw_out = int(radius * 0.38)
        cw_in = int(radius * 0.20)
        cx = int(radius * 0.75)
        pygame.draw.rect(raw, country["outer"], (0, radius - cw_out // 2, d, cw_out))
        pygame.draw.rect(raw, country["outer"], (cx - cw_out // 2, 0, cw_out, d))
        pygame.draw.rect(raw, country["inner"], (0, radius - cw_in // 2, d, cw_in))
        pygame.draw.rect(raw, country["inner"], (cx - cw_in // 2, 0, cw_in, d))

    elif pat == "swiss":
        raw.fill(country["bg"])
        cw = int(radius * 0.35)
        cl = int(radius * 0.9)
        pygame.draw.rect(raw, country["cross"], (radius - cl // 2, radius - cw // 2, cl, cw))
        pygame.draw.rect(raw, country["cross"], (radius - cw // 2, radius - cl // 2, cw, cl))

    elif pat == "union_jack":
        raw.fill(country["bg"])
        pygame.draw.line(raw, country["white_cross"], (0, 0), (d, d), int(radius * 0.25))
        pygame.draw.line(raw, country["white_cross"], (0, d), (d, 0), int(radius * 0.25))
        pygame.draw.line(raw, country["red_cross"], (0, 0), (d, d), int(radius * 0.12))
        pygame.draw.line(raw, country["red_cross"], (0, d), (d, 0), int(radius * 0.12))
        pygame.draw.rect(raw, country["white_cross"], (0, radius - 6, d, 12))
        pygame.draw.rect(raw, country["white_cross"], (radius - 6, 0, 12, d))
        pygame.draw.rect(raw, country["red_cross"], (0, radius - 3, d, 6))
        pygame.draw.rect(raw, country["red_cross"], (radius - 3, 0, 6, d))

    elif pat == "canton_stripes" or pat == "canton_stars":
        # Alternating stripes
        for s in range(7):
            sy = int(s * d / 7)
            sh = int(d / 7) + 1
            col = country.get("stripe1", (218, 41, 28)) if s % 2 == 0 else country.get("stripe2", (255, 255, 255))
            pygame.draw.rect(raw, col, (0, sy, d, sh))
        # Blue canton
        pygame.draw.rect(raw, country.get("canton", (10, 30, 120)), (0, 0, radius, radius))
        pygame.draw.circle(raw, (255, 255, 255), (radius // 2, radius // 2), 4)

    elif pat == "crescent":
        raw.fill(country["bg"])
        pygame.draw.circle(raw, country["fg"], (int(radius * 0.9), radius), int(radius * 0.38))
        pygame.draw.circle(raw, country["bg"], (int(radius * 1.05), radius), int(radius * 0.30))
        pygame.draw.circle(raw, country["fg"], (int(radius * 1.3), radius), int(radius * 0.12))

    else:
        raw.fill(country.get("primary", (100, 100, 100)))

    # 2. Circular Masking
    masked = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.circle(masked, (255, 255, 255, 255), (radius, radius), radius)
    masked.blit(raw, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

    # 3. 3D Specular Spherical Highlight & Inner Rim Shadow
    highlight = pygame.Surface((d, d), pygame.SRCALPHA)
    # Bright specular glare on top-left
    pygame.draw.circle(highlight, (255, 255, 255, 145), (int(radius * 0.65), int(radius * 0.65)), int(radius * 0.32))
    # Soft inner shadow ring for physical depth
    pygame.draw.circle(highlight, (10, 15, 30, 120), (radius, radius), radius, 2)
    masked.blit(highlight, (0, 0))

    return masked


# ==============================================================================
# PARTICLES & PHYSICS OBJECTS
# ==============================================================================
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
        self.vy += 0.16
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
    def __init__(self, country: dict, start_x: float, start_y: float, radius: int = 20):
        self.country = country
        self.name = country["name"]
        self.code = country["code"]
        self.color = country["primary"]
        self.x = float(start_x)
        self.y = float(start_y)
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(0.0, 1.5)
        self.radius = radius
        self.finished = False
        self.finish_time = None
        self.trail = []
        self.flag_surf = render_flag_surface(country, self.radius)

    def update(self):
        if not self.finished:
            self.trail.append((self.x, self.y))
            if len(self.trail) > 12:
                self.trail.pop(0)


# ==============================================================================
# PROCEDURAL MODULAR OBSTACLE ROSTER
# ==============================================================================
class PinballBumper:
    """Explosive neon ricochet bumper that flashes and blasts marbles away with sparks."""
    def __init__(self, cx, cy, radius=38, color=(255, 50, 150)):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.color = color
        self.flash_timer = 0

    def update(self):
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def check_collision(self, marble: Marble):
        dist = math.hypot(marble.x - self.cx, marble.y - self.cy)
        if dist < self.radius + marble.radius:
            nx = (marble.x - self.cx) / (dist + 1e-6)
            ny = (marble.y - self.cy) / (dist + 1e-6)
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
        glow_surf = pygame.Surface((self.radius * 3, self.radius * 3), pygame.SRCALPHA)
        alpha = 130 if is_lit else 45
        pygame.draw.circle(glow_surf, (*self.color, alpha), (int(self.radius * 1.5), int(self.radius * 1.5)), int(self.radius * 1.4))
        surface.blit(glow_surf, (int(self.cx - self.radius * 1.5), int(self.cy - self.radius * 1.5)))

        pygame.draw.circle(surface, (25, 28, 50), (int(self.cx), int(self.cy)), self.radius)
        pygame.draw.circle(surface, ring_color, (int(self.cx), int(self.cy)), self.radius, 4)
        pygame.draw.circle(surface, ring_color, (int(self.cx), int(self.cy)), self.radius // 2)


class Spinner:
    """Configurable multi-blade spinning windmill obstacle (2, 3, or 4 blades)."""
    def __init__(self, cx, cy, length=150, speed=0.04, blades=2, color=(0, 230, 255)):
        self.cx = cx
        self.cy = cy
        self.length = length
        self.speed = speed
        self.blades = blades
        self.angle = random.uniform(0, math.pi)
        self.color = color

    def update(self):
        self.angle += self.speed

    def check_collision(self, marble: Marble):
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

        pygame.draw.circle(surface, (20, 24, 40), (int(self.cx), int(self.cy)), 16)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.cx), int(self.cy)), 16, 3)
        pygame.draw.circle(surface, self.color, (int(self.cx), int(self.cy)), 8)


class VortexWhirlpool:
    """Gravitational cosmic whirlpool that pulls marbles in and slingshots them outward."""
    def __init__(self, cx, cy, radius=120, strength=0.35, color=(160, 40, 255)):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.strength = strength
        self.color = color
        self.angle = 0.0

    def update(self):
        self.angle += 0.06

    def check_influence(self, marble: Marble):
        dx = self.cx - marble.x
        dy = self.cy - marble.y
        dist = math.hypot(dx, dy)
        if dist < self.radius:
            factor = (1.0 - dist / self.radius)
            # Inward gravity pull
            pull = self.strength * factor
            marble.vx += (dx / (dist + 1e-6)) * pull
            marble.vy += (dy / (dist + 1e-6)) * pull

            # Swirling vortex torque
            swirl_speed = 3.5 * factor
            marble.vx += -(dy / (dist + 1e-6)) * swirl_speed
            marble.vy += (dx / (dist + 1e-6)) * swirl_speed

            # Explosive slingshot if suction gets too close to core
            if dist < 26:
                burst_angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(14, 20)
                marble.vx = math.cos(burst_angle) * speed
                marble.vy = math.sin(burst_angle) * speed
                return True
        return False

    def draw(self, surface):
        # Swirling accretion rings
        for i in range(4):
            r = int(self.radius * (0.3 + 0.22 * i))
            start_ang = self.angle + i * (math.pi / 2)
            glow_surf = pygame.Surface((r * 2 + 10, r * 2 + 10), pygame.SRCALPHA)
            pygame.draw.arc(glow_surf, (*self.color, 110), (5, 5, r * 2, r * 2), start_ang, start_ang + 2.2, 5)
            surface.blit(glow_surf, (int(self.cx - r - 5), int(self.cy - r - 5)))

        # Vortex black hole core
        pygame.draw.circle(surface, (12, 10, 24), (int(self.cx), int(self.cy)), 22)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.cx), int(self.cy)), 22, 2)
        pygame.draw.circle(surface, self.color, (int(self.cx), int(self.cy)), 8)


class SeeSawBeam:
    """Dynamic tilting balance beam that rocks back and forth when hit by marbles."""
    def __init__(self, cx, cy, length=220, color=(255, 170, 0)):
        self.cx = cx
        self.cy = cy
        self.length = length
        self.color = color
        self.angle = 0.0
        self.ang_vel = 0.0
        self.max_angle = 0.45

    def update(self):
        # Spring return towards horizontal
        self.ang_vel -= self.angle * 0.025
        self.ang_vel *= 0.94
        self.angle += self.ang_vel
        self.angle = max(-self.max_angle, min(self.max_angle, self.angle))

    def check_collision(self, marble: Marble):
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
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
        if dist < marble.radius + 7:
            norm_x = (marble.x - proj_x) / (dist + 1e-6)
            norm_y = (marble.y - proj_y) / (dist + 1e-6)
            dot = marble.vx * norm_x + marble.vy * norm_y
            if dot < 0:
                marble.vx -= 1.8 * dot * norm_x
                marble.vy -= 1.8 * dot * norm_y
                # Impart torque to seesaw
                offset = (t - 0.5) * self.length
                self.ang_vel += offset * 0.0012
                return True
        return False

    def draw(self, surface):
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        p1 = (self.cx - cos_a * (self.length / 2), self.cy - sin_a * (self.length / 2))
        p2 = (self.cx + cos_a * (self.length / 2), self.cy + sin_a * (self.length / 2))

        # Fulcrum base
        pts = [(self.cx, self.cy), (self.cx - 22, self.cy + 34), (self.cx + 22, self.cy + 34)]
        pygame.draw.polygon(surface, (30, 35, 60), pts)
        pygame.draw.polygon(surface, (255, 255, 255), pts, 2)

        # Beam
        pygame.draw.line(surface, self.color, p1, p2, 10)
        pygame.draw.circle(surface, (255, 255, 255), p1, 7)
        pygame.draw.circle(surface, (255, 255, 255), p2, 7)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.cx), int(self.cy)), 10)


class AngledDeflector:
    """High-tension neon slingshot deflector that provides sharp bank shots."""
    def __init__(self, p1, p2, color=(0, 255, 180), bounce_mult=1.6):
        self.p1 = p1
        self.p2 = p2
        self.color = color
        self.bounce_mult = bounce_mult
        self.flash_timer = 0

    def update(self):
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def check_collision(self, marble: Marble):
        p1x, p1y = self.p1
        p2x, p2y = self.p2
        seg_dx = p2x - p1x
        seg_dy = p2y - p1y
        seg_len_sq = seg_dx * seg_dx + seg_dy * seg_dy

        t = max(0, min(1, ((marble.x - p1x) * seg_dx + (marble.y - p1y) * seg_dy) / seg_len_sq))
        proj_x = p1x + t * seg_dx
        proj_y = p1y + t * seg_dy

        dist = math.hypot(marble.x - proj_x, marble.y - proj_y)
        if dist < marble.radius + 6:
            norm_x = (marble.x - proj_x) / (dist + 1e-6)
            norm_y = (marble.y - proj_y) / (dist + 1e-6)
            dot = marble.vx * norm_x + marble.vy * norm_y
            if dot < 0:
                marble.vx -= (1.0 + self.bounce_mult) * dot * norm_x
                marble.vy -= (1.0 + self.bounce_mult) * dot * norm_y
                self.flash_timer = 10
                return True
        return False

    def draw(self, surface):
        is_lit = self.flash_timer > 0
        col = (255, 255, 255) if is_lit else self.color
        pygame.draw.line(surface, col, self.p1, self.p2, 8)
        pygame.draw.circle(surface, (255, 255, 255), self.p1, 8)
        pygame.draw.circle(surface, (255, 255, 255), self.p2, 8)


# ==============================================================================
# MARBLE ARENA GAME CONTROLLER
# ==============================================================================
class MarbleArenaGame:
    def __init__(self, duration_sec=30, width=VIDEO_WIDTH, height=VIDEO_HEIGHT, fps=FPS):
        pygame.init()
        self.width = width
        self.height = height
        self.fps = fps
        self.duration_sec = duration_sec
        self.total_frames = int(duration_sec * fps)

        # 1. Draft 8 Unique Countries Every Run
        selected_countries = random.sample(COUNTRY_DATABASE, 8)

        # 2. Procedural Arena Layout & Theme Archetypes
        self.layout_type = random.choice([
            "VORTEX_HAVOC",
            "PINBALL_STORM",
            "ZIGZAG_SLALOM",
            "WINDMILL_GAUNTLET",
            "CHAOS_PEG_MATRIX"
        ])

        # Theme Colors
        THEMES = [
            {"name": "CYBERPUNK", "wall": (0, 230, 255), "accent": (255, 0, 160)},
            {"name": "GOLDEN_ROYALE", "wall": (255, 205, 0), "accent": (140, 60, 255)},
            {"name": "INFERNO_BLAZE", "wall": (255, 70, 30), "accent": (255, 220, 0)},
            {"name": "TOXIC_EMERALD", "wall": (0, 255, 140), "accent": (0, 220, 255)},
            {"name": "ELECTRIC_SAPPHIRE", "wall": (60, 130, 255), "accent": (255, 70, 200)}
        ]
        self.theme = random.choice(THEMES)
        print(f"[MarbleArena] Layout: {self.layout_type} | Theme: {self.theme['name']} | Countries: {[c['code'] for c in selected_countries]}")

        # Staggered launch at top
        self.marbles = []
        start_x_spacing = (width - 320) / (len(selected_countries) - 1)
        for i, country in enumerate(selected_countries):
            sx = 160 + i * start_x_spacing
            sy = random.uniform(250, 290)
            self.marbles.append(Marble(country, sx, sy, radius=20))

        # 3. Procedural Obstacles & Peg Setup based on Archetype
        self.bumpers = []
        self.spinners = []
        self.vortexes = []
        self.seesaws = []
        self.deflectors = []
        self.pegs = []
        self.finish_line_y = 1620

        self._build_procedural_arena()

        self.finishers = []
        self.particles = []
        self.audio_events = []

        self.winner_start_frame = None
        self.winner_duration_sec = 3.0
        self.winner_frames_total = int(self.winner_duration_sec * self.fps)
        self.is_finished = False
        self.winner = None
        self.podium_p2 = None
        self.podium_p3 = None

        self.font_title = pygame.font.SysFont("Arial", 46, bold=True)
        self.font_sub = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_name = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 56, bold=True)
        self.font_podium = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_cta = pygame.font.SysFont("Arial", 28, bold=True)

    def _build_procedural_arena(self):
        """Generates dynamic obstacle layouts and custom pegboards."""
        w, h = self.width, self.height

        if self.layout_type == "VORTEX_HAVOC":
            self.vortexes = [
                VortexWhirlpool(cx=320, cy=780, radius=125, strength=0.36, color=(180, 40, 255)),
                VortexWhirlpool(cx=760, cy=1120, radius=125, strength=0.36, color=(0, 230, 255))
            ]
            self.spinners = [
                Spinner(cx=760, cy=780, length=150, speed=-0.045, blades=3, color=(255, 60, 180)),
                Spinner(cx=320, cy=1120, length=150, speed=0.045, blades=3, color=(255, 215, 0))
            ]
            self.bumpers = [
                PinballBumper(cx=540, cy=950, radius=42, color=(0, 255, 190)),
                PinballBumper(cx=540, cy=1350, radius=38, color=(255, 40, 100))
            ]
            # Peg matrix in upper and mid tiers
            for r in range(8):
                py = 370 + r * 95
                cols = 9 if r % 2 == 0 else 8
                offset_x = 100 if r % 2 == 0 else 155
                for c in range(cols):
                    px = offset_x + c * 110
                    self.pegs.append((px, py))

        elif self.layout_type == "PINBALL_STORM":
            self.bumpers = [
                PinballBumper(cx=540, cy=660, radius=44, color=(255, 215, 0)),
                PinballBumper(cx=280, cy=860, radius=40, color=(0, 255, 220)),
                PinballBumper(cx=800, cy=860, radius=40, color=(0, 255, 220)),
                PinballBumper(cx=540, cy=1060, radius=46, color=(255, 40, 150)),
                PinballBumper(cx=300, cy=1280, radius=40, color=(255, 140, 0)),
                PinballBumper(cx=780, cy=1280, radius=40, color=(255, 140, 0))
            ]
            self.deflectors = [
                AngledDeflector((70, 740), (220, 840), color=(0, 220, 255)),
                AngledDeflector((w - 70, 740), (w - 220, 840), color=(0, 220, 255)),
                AngledDeflector((70, 1160), (220, 1260), color=(255, 60, 180)),
                AngledDeflector((w - 70, 1160), (w - 220, 1260), color=(255, 60, 180))
            ]
            self.spinners = [
                Spinner(cx=540, cy=1440, length=170, speed=0.04, blades=2, color=(0, 255, 220))
            ]
            for r in range(6):
                py = 370 + r * 95
                cols = 9 if r % 2 == 0 else 8
                offset_x = 100 if r % 2 == 0 else 155
                for c in range(cols):
                    self.pegs.append((offset_x + c * 110, py))

        elif self.layout_type == "ZIGZAG_SLALOM":
            self.seesaws = [
                SeeSawBeam(cx=400, cy=740, length=240, color=(255, 180, 0)),
                SeeSawBeam(cx=680, cy=980, length=240, color=(0, 230, 255)),
                SeeSawBeam(cx=400, cy=1220, length=240, color=(255, 60, 180))
            ]
            self.deflectors = [
                AngledDeflector((w - 70, 680), (w - 240, 800), color=(0, 255, 180)),
                AngledDeflector((70, 920), (240, 1040), color=(0, 255, 180)),
                AngledDeflector((w - 70, 1160), (w - 240, 1280), color=(0, 255, 180))
            ]
            self.bumpers = [
                PinballBumper(cx=540, cy=1420, radius=42, color=(255, 215, 0)),
                PinballBumper(cx=220, cy=1420, radius=36, color=(255, 50, 150)),
                PinballBumper(cx=860, cy=1420, radius=36, color=(255, 50, 150))
            ]
            for r in range(7):
                py = 370 + r * 95
                cols = 9 if r % 2 == 0 else 8
                offset_x = 100 if r % 2 == 0 else 155
                for c in range(cols):
                    self.pegs.append((offset_x + c * 110, py))

        elif self.layout_type == "WINDMILL_GAUNTLET":
            self.spinners = [
                Spinner(cx=320, cy=760, length=160, speed=0.045, blades=4, color=(0, 240, 255)),
                Spinner(cx=760, cy=760, length=160, speed=-0.045, blades=4, color=(0, 240, 255)),
                Spinner(cx=540, cy=1050, length=190, speed=0.055, blades=3, color=(255, 40, 160)),
                Spinner(cx=300, cy=1320, length=140, speed=-0.04, blades=2, color=(255, 215, 0)),
                Spinner(cx=780, cy=1320, length=140, speed=0.04, blades=2, color=(255, 215, 0))
            ]
            self.bumpers = [
                PinballBumper(cx=540, cy=760, radius=36, color=(0, 255, 160)),
                PinballBumper(cx=260, cy=1050, radius=36, color=(255, 140, 0)),
                PinballBumper(cx=820, cy=1050, radius=36, color=(255, 140, 0))
            ]
            for r in range(6):
                py = 370 + r * 95
                cols = 9 if r % 2 == 0 else 8
                offset_x = 100 if r % 2 == 0 else 155
                for c in range(cols):
                    self.pegs.append((offset_x + c * 110, py))

        else:  # CHAOS_PEG_MATRIX
            self.vortexes = [
                VortexWhirlpool(cx=540, cy=1120, radius=130, strength=0.42, color=(0, 220, 255))
            ]
            self.bumpers = [
                PinballBumper(cx=260, cy=800, radius=40, color=(255, 60, 160)),
                PinballBumper(cx=820, cy=800, radius=40, color=(255, 60, 160)),
                PinballBumper(cx=540, cy=1400, radius=44, color=(255, 215, 0))
            ]
            self.spinners = [
                Spinner(cx=260, cy=1350, length=140, speed=0.04, blades=2, color=(0, 255, 200)),
                Spinner(cx=820, cy=1350, length=140, speed=-0.04, blades=2, color=(0, 255, 200))
            ]
            # 11 dense rows of pegs
            for r in range(11):
                py = 370 + r * 95
                cols = 9 if r % 2 == 0 else 8
                offset_x = 100 if r % 2 == 0 else 155
                for c in range(cols):
                    px = offset_x + c * 110
                    # Leave space around center vortex and bumpers
                    if math.hypot(px - 540, py - 1120) > 130 and math.hypot(px - 260, py - 800) > 65 and math.hypot(px - 820, py - 800) > 65:
                        self.pegs.append((px, py))

    def render_frame(self, frame_idx):
        t = frame_idx / self.fps
        surface = pygame.Surface((self.width, self.height))
        # Deep space neon backdrop
        surface.fill((10, 12, 26))

        wall_col = self.theme["wall"]
        accent_col = self.theme["accent"]

        # 1. Outer Neon Boundary Walls
        pygame.draw.line(surface, wall_col, (60, 230), (60, self.finish_line_y + 120), 8)
        pygame.draw.line(surface, wall_col, (self.width - 60, 230), (self.width - 60, self.finish_line_y + 120), 8)
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

        # 3. Update & Draw Dynamic Obstacles
        for vx in self.vortexes:
            vx.update()
            vx.draw(surface)

        for sb in self.seesaws:
            sb.update()
            sb.draw(surface)

        for df in self.deflectors:
            df.update()
            df.draw(surface)

        for b in self.bumpers:
            b.update()
            b.draw(surface)

        for sp in self.spinners:
            sp.update()
            sp.draw(surface)

        # 4. Draw Pegs with glowing neon centers
        for px, py in self.pegs:
            pygame.draw.circle(surface, (40, 55, 90), (px, py), 9)
            pygame.draw.circle(surface, accent_col, (px, py), 5)
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

                # Vortex gravitational pull & slingshots
                for vx in self.vortexes:
                    if vx.check_influence(m):
                        self.audio_events.append((t, 820.0, True))
                        for _ in range(12):
                            self.particles.append(Particle(m.x, m.y, vx.color, speed_mult=1.6))

                # Seesaw balance beam collision
                for sb in self.seesaws:
                    if sb.check_collision(m):
                        self.audio_events.append((t, 580.0, False))

                # Angled deflector collision
                for df in self.deflectors:
                    if df.check_collision(m):
                        self.audio_events.append((t, 720.0, False))
                        for _ in range(8):
                            self.particles.append(Particle(m.x, m.y, df.color, speed_mult=1.2))

                # Pinball Bumper collisions
                for bmp in self.bumpers:
                    if bmp.check_collision(m):
                        self.audio_events.append((t, 780.0, True))
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
                    for _ in range(18):
                        self.particles.append(Particle(m.x, self.finish_line_y, (255, 60, 80), speed_mult=1.2))

                m.update()

            # Render Marbles with Motion Trails and Country Flags
            for idx, (tx, ty) in enumerate(m.trail):
                alpha = int(140 * (idx + 1) / len(m.trail))
                surf = pygame.Surface((m.radius * 2, m.radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*m.color, alpha), (m.radius, m.radius), int(m.radius * 0.75))
                surface.blit(surf, (int(tx - m.radius), int(ty - m.radius)))

            if not m.finished or (m.finished and t - m.finish_time < 0.4):
                # Outer glow halo
                halo_surf = pygame.Surface((m.radius * 3, m.radius * 3), pygame.SRCALPHA)
                pygame.draw.circle(halo_surf, (*m.color, 75), (int(m.radius * 1.5), int(m.radius * 1.5)), int(m.radius * 1.4))
                surface.blit(halo_surf, (int(m.x - m.radius * 1.5), int(m.y - m.radius * 1.5)))

                # Blit Country Flag Texture onto 3D Sphere
                surface.blit(m.flag_surf, (int(m.x - m.radius), int(m.y - m.radius)))
                # Outer border rim
                pygame.draw.circle(surface, (255, 255, 255), (int(m.x), int(m.y)), m.radius, 2)

                # High-contrast Country Code Badge above marble
                lbl = m.code
                tb = self.font_name.render(lbl, True, (255, 255, 255))
                badge_w = tb.get_width() + 10
                badge_h = tb.get_height() + 4
                bx = int(m.x - badge_w // 2)
                by = int(m.y - m.radius - 22)
                pygame.draw.rect(surface, (14, 16, 30), (bx, by, badge_w, badge_h), border_radius=6)
                pygame.draw.rect(surface, m.color, (bx, by, badge_w, badge_h), width=1, border_radius=6)
                surface.blit(tb, (bx + 5, by + 2))

        # 6. Particles update & render
        for p in self.particles[:]:
            p.update()
            p.draw(surface)
            if p.life <= 0:
                self.particles.remove(p)

        # 7. World Cup Tournament Live Survival HUD
        alive_marbles = [m for m in self.marbles if not m.finished]

        # Elimination Decision: Last Country Standing!
        if len(alive_marbles) <= 1 and not self.is_finished:
            self.is_finished = True
            self.winner_start_frame = frame_idx
            remaining = sorted(alive_marbles, key=lambda m: m.y)
            full_ranking = remaining + list(reversed(self.finishers))
            self.winner = full_ranking[0]
            self.podium_p2 = full_ranking[1] if len(full_ranking) > 1 else None
            self.podium_p3 = full_ranking[2] if len(full_ranking) > 2 else None
            self.audio_events.append((t, 880.0, True))
            self.audio_events.append((t + 0.14, 1174.0, True))

        title = self.font_title.render("WORLD CUP MARBLE RACE", True, (255, 255, 255))
        surface.blit(title, title.get_rect(center=(self.width // 2, 75)))

        sub_text = f"LAST COUNTRY STANDING WINS!  |  NATIONS: {len(alive_marbles)} / 8"
        sub = self.font_sub.render(sub_text, True, (0, 255, 220))
        surface.blit(sub, sub.get_rect(center=(self.width // 2, 135)))

        # 8. Dramatic Winner Card (Shown for 3.0 seconds after champion is decided)
        if self.is_finished and self.winner is not None:
            frames_winner = frame_idx - self.winner_start_frame
            win_ratio = min(1.0, frames_winner / self.winner_frames_total)

            # Confetti fireworks
            if random.random() < 0.45:
                cx = random.randint(100, self.width - 100)
                cy = random.randint(400, 1300)
                confetti_colors = [(255, 215, 0), (255, 60, 60), (60, 150, 255), (60, 255, 120), (220, 80, 255), (0, 255, 255)]
                for _ in range(8):
                    self.particles.append(Particle(cx, cy, random.choice(confetti_colors), speed_mult=1.9))

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
            pygame.draw.rect(card_surf, self.winner.color, (5, 5, card_w - 10, card_h - 10), width=3, border_radius=26)
            surface.blit(card_surf, (card_x, draw_y))

            # Header
            crown_txt = self.font_sub.render("🏆 WORLD CUP CHAMPION 🏆", True, (255, 215, 0))
            surface.blit(crown_txt, crown_txt.get_rect(center=(self.width // 2, draw_y + 45)))

            # Winner announcement
            win_name_surf = self.font_big.render(f"{self.winner.name.upper()} WINS!", True, self.winner.color)
            surface.blit(win_name_surf, win_name_surf.get_rect(center=(self.width // 2, draw_y + 115)))

            # Standings
            p1_txt = self.font_podium.render(f"🥇 1ST PLACE: {self.winner.name} ({self.winner.code})", True, (255, 220, 50))
            p2_str = f"{self.podium_p2.name} ({self.podium_p2.code})" if self.podium_p2 else "..."
            p3_str = f"{self.podium_p3.name} ({self.podium_p3.code})" if self.podium_p3 else "..."
            p2_txt = self.font_podium.render(f"🥈 2ND PLACE: {p2_str}", True, (210, 220, 230))
            p3_txt = self.font_podium.render(f"🥉 3RD PLACE: {p3_str}", True, (205, 127, 50))

            surface.blit(p1_txt, p1_txt.get_rect(center=(self.width // 2, draw_y + 190)))
            surface.blit(p2_txt, p2_txt.get_rect(center=(self.width // 2, draw_y + 245)))
            surface.blit(p3_txt, p3_txt.get_rect(center=(self.width // 2, draw_y + 300)))

            cta_txt = self.font_cta.render("DID YOUR COUNTRY SURVIVE? COMMENT BELOW! 👇", True, (0, 255, 220))
            surface.blit(cta_txt, cta_txt.get_rect(center=(self.width // 2, draw_y + 380)))

            progress = 0.85 + 0.15 * win_ratio
        else:
            elim_ratio = len(self.finishers) / max(1, len(self.marbles) - 1)
            progress = min(0.85, elim_ratio * 0.85)

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
        print(f"[MarbleArena] Generating dynamic video: plays until last nation standing + 3s winner popup...")

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
                print(f"[MarbleArena] Safety cutoff reached at {frame_idx} frames.")
                break

            if frame_idx % 120 == 0:
                print(f"  -> Rendering progress: frame {frame_idx} ({frame_idx / self.fps:.1f}s)...")

            frame_idx += 1

        total_frames = frame_idx
        actual_duration_sec = total_frames / self.fps
        print(f"[MarbleArena] Tournament finished & 3s winner popup completed! Duration: {actual_duration_sec:.2f}s ({total_frames} frames).")

        print("[MarbleArena] Synthesizing procedural audio...")
        audio = ProceduralAudioEngine(duration_sec=actual_duration_sec)
        audio.add_subtle_background_pulse(bpm=130.0, volume=0.15)

        for (timestamp, freq, is_finish) in self.audio_events:
            if timestamp <= actual_duration_sec:
                audio.add_tone(start_time=timestamp, freq=freq, duration=0.18, volume=0.55)
                if is_finish:
                    audio.add_explosion(start_time=timestamp, volume=0.8)

        temp_wav = output_path.with_suffix(".temp.wav")
        audio.export_wav(temp_wav)

        print("[MarbleArena] Muxing video and audio into final MP4...")
        final_file = renderer.finalize_with_audio(temp_wav)
        print(f"[MarbleArena] Done! Video saved at: {final_file}")
        return final_file
