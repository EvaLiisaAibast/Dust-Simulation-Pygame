import pygame
import random
import math
import sys

# --------------------------------------------------------
# CONFIGURATION PARAMETERS (Tweak these for fun)
# --------------------------------------------------------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
NUM_DUST_PARTICLES = 800
MAX_RADIUS = 2.5
MIN_RADIUS = 0.5
MAX_SPEED = 0.3
MIN_SPEED = 0.05
FADE_RATE = 0.001
WIND_INTENSITY = 0.002
NOISE_SCALE = 0.002
DEPTH_LAYERS = 3 # Parallax layers for depth illusion
GLOW_INTENSITY = 50
BACKGROUND_COLOR = (5, 5, 10)
MOUSE_SENSITIVITY = 0.1 # Adjust this to control how strongly particles are influenced by the mouse

# --------------------------------------------------------
# INITIALIZE
# --------------------------------------------------------
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dust Simulation — Pygame")
clock = pygame.time.Clock()

# --------------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------------
def lerp(a, b, t):
    """Linear interpolation"""
    return a + (b - a) * t

def clamp(x, a, b):
    return max(a, min(x, b))

def perlin_noise(x, y, seed=0):
    """Simple 2D value noise approximation using hash tricks"""
    n = math.sin((x * 12.9898 + y * 78.233 + seed * 43758.5453)) * 43758.5453
    return n - math.floor(n)

def smooth_noise(x, y, seed):
    corners = (perlin_noise(x-1, y-1, seed) + perlin_noise(x+1, y-1, seed) +
               perlin_noise(x-1, y+1, seed) + perlin_noise(x+1, y+1, seed)) / 16
    sides = (perlin_noise(x-1, y, seed) + perlin_noise(x+1, y, seed) +
             perlin_noise(x, y-1, seed) + perlin_noise(x, y+1, seed)) / 8
    center = perlin_noise(x, y, seed) / 4
    return corners + sides + center

def turbulence(x, y, size, seed):
    """Layered noise for turbulent motion"""
    value = 0.0
    initial_size = size
    while size >= 1:
        value += smooth_noise(x / size, y / size, seed) * size
        size /= 2.0
    return (128.0 * value / initial_size)

# --------------------------------------------------------
# DUST PARTICLE CLASS
# --------------------------------------------------------
class DustParticle:
    def __init__(self, layer):
        self.layer = layer
        self.reset(random.uniform(0, SCREEN_WIDTH),
                   random.uniform(0, SCREEN_HEIGHT))
        self.alpha = random.uniform(0.2, 1.0)
        self.pulse_phase = random.random() * math.pi * 2
        self.pulse_speed = random.uniform(0.01, 0.03)

    def reset(self, x, y):
        self.x = x
        self.y = y
        self.z = self.layer + random.random()
        self.radius = random.uniform(MIN_RADIUS, MAX_RADIUS) * (1.0 / self.z)
        self.speed = random.uniform(MIN_SPEED, MAX_SPEED) * (1.0 / self.z)
        self.angle = random.uniform(0, math.pi * 2)
        self.color = (
            random.randint(180, 255),
            random.randint(180, 255),
            random.randint(180, 255)
        )
        self.life = random.uniform(0.5, 1.0)
        self.seed = random.randint(0, 9999)

    def update(self, dt, time, mouse_x, mouse_y):
        # Calculate direction to mouse
        dx = mouse_x - self.x
        dy = mouse_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # Apply force towards the mouse based on distance (scaled by sensitivity)
        force = MOUSE_SENSITIVITY / distance if distance > 0 else 0
        self.x += dx * force
        self.y += dy * force
        
        # Turbulence for swirling movement (wind)
        wind_x = (turbulence(self.x * NOISE_SCALE, self.y * NOISE_SCALE, 32, self.seed) - 64) * WIND_INTENSITY
        wind_y = (turbulence(self.y * NOISE_SCALE, self.x * NOISE_SCALE, 32, self.seed + 100) - 64) * WIND_INTENSITY
        
        # Update position with wind
        self.x += wind_x
        self.y += wind_y

        # Random angular drift
        self.angle += (random.random() - 0.5) * 0.02

        # Wrap around edges
        if self.x < -50: self.x = SCREEN_WIDTH + 50
        if self.x > SCREEN_WIDTH + 50: self.x = -50
        if self.y < -50: self.y = SCREEN_HEIGHT + 50
        if self.y > SCREEN_HEIGHT + 50: self.y = -50

        # Pulsing glow effect
        self.pulse_phase += self.pulse_speed
        pulse = (math.sin(self.pulse_phase) + 1.0) * 0.5
        self.alpha = clamp(pulse, 0.1, 1.0)

        # Aging
        self.life -= FADE_RATE * dt
        if self.life <= 0:
            self.reset(random.uniform(0, SCREEN_WIDTH),
                       random.uniform(0, SCREEN_HEIGHT))

    def draw(self, surface):
        # Glow intensity based on alpha
        intensity = int(self.alpha * GLOW_INTENSITY)
        color = (
            clamp(int(self.color[0] * self.alpha), 0, 255),
            clamp(int(self.color[1] * self.alpha), 0, 255),
            clamp(int(self.color[2] * self.alpha), 0, 255)
        )

        # Create glow circle
        for glow_radius in range(int(self.radius * 3), 0, -1):
            glow_alpha = int((glow_radius / (self.radius * 3)) * 50)
            glow_color = (*color, glow_alpha)
            glow_surface = pygame.Surface((glow_radius * 4, glow_radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, glow_color, (glow_radius * 2, glow_radius * 2), glow_radius)
            surface.blit(glow_surface, (self.x - glow_radius * 2, self.y - glow_radius * 2), special_flags=pygame.BLEND_ADD)

        # Draw main dust mote
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.radius))

# --------------------------------------------------------
# CREATE PARTICLES
# --------------------------------------------------------
particles = []
for layer in range(DEPTH_LAYERS):
    for _ in range(NUM_DUST_PARTICLES // DEPTH_LAYERS):
        particles.append(DustParticle(layer + 1))

# --------------------------------------------------------
# MAIN LOOP
# --------------------------------------------------------
time = 0
running = True
while running:
    dt = clock.tick(60)
    time += dt * 0.001

    mouse_x, mouse_y = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BACKGROUND_COLOR)

    # Render particles per layer (depth sorting)
    for layer in range(1, DEPTH_LAYERS + 1):
        for p in [x for x in particles if x.layer == layer]:
            p.update(dt, time, mouse_x, mouse_y)
            p.draw(screen)

    # Overlay faint haze for atmosphere
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(15)
    overlay.fill((20, 20, 40))
    screen.blit(overlay, (0, 0))

    # Update display
    pygame.display.flip()

pygame.quit()
sys.exit()
