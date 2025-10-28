"""
Plutón y sus 5 lunas — script corregido
Controles:
  - ARRIBA / ABAJO : aumentar / reducir velocidad de simulación
  - T : alternar trails (trazas)
  - ESC : salir
"""
import pygame, sys, math

pygame.init()
WIDTH, HEIGHT = 900, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Plutón y sus lunas — corregido")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 18)

cx, cy = WIDTH // 2, HEIGHT // 2
pluto_radius = 22
pluto_color = (180, 180, 200)

# moons: (name, color, orbital_radius_px, body_radius_px, orbital_period_days)
moons = [
    ("Charon",   (200,200,255),  90,  10, 6.387),   # Caronte ~6.387 days
    ("Styx",     (200,160,255), 150,   4, 20.16),
    ("Nix",      (255,220,120), 210,   6, 24.85),
    ("Kerberos", (200,200,120), 270,   5, 32.17),
    ("Hydra",    (180,255,220), 330,   7, 38.20),
]

# Convert periods (days -> seconds) for convenience
for i in range(len(moons)):
    name, col, r_px, br, period_days = moons[i]
    period_seconds = period_days * 24.0 * 3600.0
    moons[i] = (name, col, r_px, br, period_seconds)

# phases to avoid alignment
phases = [i * 0.8 for i in range(len(moons))]

# Simulation state
time_sim = 0.0                # segundos de simulación
speed_multiplier = 200000.0   # multiplica dt para que veas movimiento (ajusta si quieres)
show_trails = True
trail_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
trail_fade_alpha = 18

def angle_for_moon(time_seconds, period_seconds, phase=0.0):
    """Devuelve ángulo en radianes para la posición orbital."""
    return 2.0 * math.pi * (time_seconds / period_seconds) + phase

def draw_orbits():
    for _, _, r_px, _, _ in moons:
        pygame.draw.circle(screen, (90, 90, 90), (cx, cy), r_px, 1)

def draw_pluto():
    pygame.draw.circle(screen, pluto_color, (cx, cy), pluto_radius)
    label = font.render("Plutón", True, (200,200,200))
    screen.blit(label, (cx - label.get_width()//2, cy + pluto_radius + 6))

def draw_sync_marker(x, y, angle_to_center, size=6, color=(120,120,255)):
    """
    Dibuja una pequeña marca (triángulo) en la luna que indique su 'cara'.
    angle_to_center -> ángulo (radianes) desde la luna hacia el centro (Plutón).
    Queremos que la marca quede en la cara que mira al centro.
    """
    # El vector que apunta hacia el centro es: (-cos, -sin) si el ángulo es de la órbita
    # Para dibujar la marca en la superficie de la luna hacia el centro:
    ang = angle_to_center  # ángulo desde centro hacia luna; la dirección luna->centro = ang + pi
    # Calculamos punto en la circunferencia hacia el centro
    px = x + math.cos(ang + math.pi) * (size + 2)
    py = y + math.sin(ang + math.pi) * (size + 2)
    # dibujamos un pequeño triángulo orientado hacia el centro
    # triángulo con vértice en (px,py) y base perpendicular
    base_ang = ang + math.pi / 2.0
    p1 = (px, py)
    p2 = (px + math.cos(base_ang) * (size/1.6), py + math.sin(base_ang) * (size/1.6))
    p3 = (px - math.cos(base_ang) * (size/1.6), py - math.sin(base_ang) * (size/1.6))
    pygame.draw.polygon(screen, color, [p1, p2, p3])

# Main loop
running = True
while running:
    dt_ms = clock.tick(60)
    dt_seconds = dt_ms / 1000.0

    # Incrementamos tiempo de simulación en segundos, con multiplicador
    time_sim += dt_seconds * speed_multiplier

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_UP:
                speed_multiplier *= 2.0
            elif event.key == pygame.K_DOWN:
                speed_multiplier /= 2.0
            elif event.key == pygame.K_t:
                show_trails = not show_trails
                if not show_trails:
                    trail_surf.fill((0,0,0,0))  # limpiar trazas

    # --- dibujo ---
    screen.fill((14, 18, 23))
    draw_orbits()
    draw_pluto()

    # fade trails
    if show_trails:
        fade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fade.fill((0,0,0,trail_fade_alpha))
        trail_surf.blit(fade, (0,0))

    # dibujar lunas
    for i, (name, col, r_px, br, period_s) in enumerate(moons):
        ang = angle_for_moon(time_sim, period_s, phases[i])  # radianes
        x = cx + r_px * math.cos(ang)
        y = cy + r_px * math.sin(ang)

        # dibujar traza en trail_surf
        if show_trails:
            pygame.draw.circle(trail_surf, col + (90,), (int(x), int(y)), max(1, br//2))

        # dibujar luna
        pygame.draw.circle(screen, col, (int(x), int(y)), br)

        # etiqueta
        nm_surf = font.render(name, True, (220,220,220))
        screen.blit(nm_surf, (int(x) - nm_surf.get_width()//2, int(y) - br - 12))

        # línea radial opcional
        pygame.draw.line(screen, (60,60,60), (cx, cy), (int(x), int(y)), 1)

        # rotación sincrónica para Caron (Caronte): dibujar marca que mira siempre al centro
        if name.lower().startswith("char") or name.lower().startswith("caro") or name == "Charon" or name == "Caronte":
            # angle from center to moon is 'ang' (center->moon). Pass it so mark faces center
            draw_sync_marker(x, y, ang, size=br+2)

    # blit trails below moons (opcional)
    if show_trails:
        screen.blit(trail_surf, (0,0))

    # HUD
    txt = font.render(f"Velocidad simulación mult x{speed_multiplier:.0f}  |  Trails: {'ON' if show_trails else 'OFF'}", True, (240,240,240))
    screen.blit(txt, (8,8))
    info2 = font.render("ARRIBA/ABAJO = velocidad  T = trails  ESC = salir", True, (200,200,200))
    screen.blit(info2, (8, 28))

    pygame.display.flip()

pygame.quit()
sys.exit()
