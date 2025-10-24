import pygame
pygame.init()

# Configuración
screen = pygame.display.set_mode((600, 400))
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 20)

def draw_speech_bubble(surface, text, pos, alpha=255, color=(255, 255, 255), text_color=(0, 0, 0)):
    """Dibuja un bocadillo de texto con transparencia controlada por alpha."""
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect()

    padding = 10
    bubble_width = text_rect.width + padding * 2
    bubble_height = text_rect.height + padding * 2

    bubble_rect = pygame.Rect(0, 0, bubble_width, bubble_height)
    bubble_rect.midbottom = (pos[0], pos[1] - 10)

    # Superficie con canal alfa
    bubble_surf = pygame.Surface((bubble_width, bubble_height + 10), pygame.SRCALPHA)

    # Color con opacidad (alpha)
    bubble_color = (*color[:3], alpha)

    # Cuerpo del bocadillo
    pygame.draw.rect(bubble_surf, bubble_color, (0, 0, bubble_width, bubble_height), border_radius=10)

    # Punta
    pygame.draw.polygon(bubble_surf, bubble_color, [
        (bubble_width // 2 - 8, bubble_height),
        (bubble_width // 2 + 8, bubble_height),
        (bubble_width // 2, bubble_height + 10)
    ])

    # Texto (se aplica opacidad igual al bocadillo)
    text_with_alpha = text_surf.copy()
    text_with_alpha.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)

    bubble_surf.blit(text_with_alpha, (padding, padding))
    surface.blit(bubble_surf, bubble_rect.topleft)


# ---- Bucle principal ----
running = True
angle = 0

bubble_start_time = pygame.time.get_ticks()
bubble_duration = 10000  # 10 segundos
fade_duration = 2000     # últimos 2 segundos para desvanecerse

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((30, 30, 30))

    # Simulamos un personaje en movimiento
    x = 300 + 100 * pygame.math.Vector2(1, 0).rotate(angle).x
    y = 200
    pygame.draw.circle(screen, (0, 120, 255), (int(x), int(y)), 20)

    # --- Control del tiempo del bocadillo ---
    current_time = pygame.time.get_ticks()
    elapsed = current_time - bubble_start_time

    if elapsed < bubble_duration:
        # Calculamos opacidad
        if elapsed > bubble_duration - fade_duration:
            # Fase de desvanecimiento (alpha entre 255 → 0)
            alpha = int(255 * (1 - (elapsed - (bubble_duration - fade_duration)) / fade_duration))
        else:
            alpha = 255

        draw_speech_bubble(screen, "¡Hola mundo!", (int(x), int(y) - 30), alpha=alpha)

    pygame.display.flip()
    clock.tick(60)
    angle += 1

pygame.quit()
