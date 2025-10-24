import pygame, math, sys

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# --- Jugador ---
player_pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
player_speed = 3
player_angle = 0  # dirección en grados

# --- Superficie de niebla ---
fog_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

def draw_flashlight_mask(fog_surf, pos, angle, length=230, spread_deg=40):
    """
    Dibuja una niebla gris opaca y un triángulo transparente (agujero)
    que simula la luz de la linterna.
    """
    # Niebla gris oscura con opacidad alta
    fog_surf.fill((60, 60, 60, 235))  # gris con 92% opacidad

    # Cálculo del triángulo
    rad = math.radians(angle)
    half = math.radians(spread_deg / 2)
    p1 = (pos.x, pos.y)
    p2 = (pos.x + math.cos(rad - half) * length,
          pos.y + math.sin(rad - half) * length)
    p3 = (pos.x + math.cos(rad + half) * length,
          pos.y + math.sin(rad + half) * length)

    # Dibujamos el triángulo totalmente transparente
    pygame.draw.polygon(fog_surf, (0, 0, 0, 0), [p1, p2, p3])

    # Todo lo que sea (0,0,0,0) será transparente
    fog_surf.set_colorkey((0, 0, 0, 0))

    # Devolvemos las coordenadas del triángulo (para la luz amarilla)
    return [p1, p2, p3]

def draw_yellow_light(screen, tri_points, alpha=90):
    """
    Dibuja el triángulo amarillo translúcido encima del área iluminada.
    """
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(surf, (255, 240, 100, alpha), tri_points)
    screen.blit(surf, (0, 0))


# --- Bucle principal ---
running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    # Movimiento / rotación del jugador
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_angle -= 3
    if keys[pygame.K_RIGHT]:
        player_angle += 3
    if keys[pygame.K_UP]:
        player_pos.x += math.cos(math.radians(player_angle)) * player_speed
        player_pos.y += math.sin(math.radians(player_angle)) * player_speed
    if keys[pygame.K_DOWN]:
        player_pos.x -= math.cos(math.radians(player_angle)) * player_speed
        player_pos.y -= math.sin(math.radians(player_angle)) * player_speed

    # --- Fondo del mapa ---
    screen.fill((40, 80, 40))
    pygame.draw.rect(screen, (200, 100, 50), (100, 200, 200, 100))
    pygame.draw.rect(screen, (120, 40, 40), (500, 400, 150, 100))
    pygame.draw.circle(screen, (90, 150, 250), (650, 150), 40)

    # --- Jugador ---
    player_rect = pygame.Rect(0, 0, 30, 30)
    player_rect.center = player_pos
    pygame.draw.rect(screen, (50, 100, 255), player_rect)

    # --- Niebla y luz ---
    tri_points = draw_flashlight_mask(fog_surface, player_pos, player_angle)
    screen.blit(fog_surface, (0, 0))          # niebla gris
    draw_yellow_light(screen, tri_points, 110) # luz amarilla translúcida

    # --- Actualizar pantalla ---
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
