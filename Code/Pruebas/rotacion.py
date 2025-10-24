import pygame, math, sys

pygame.init()
screen = pygame.display.set_mode((600, 600))
clock = pygame.time.Clock()

centro = (300, 300)
radio = 100
angulo = 0

# ---- Crear triángulo orbitante ----
tri_img = pygame.Surface((40, 60), pygame.SRCALPHA)
pygame.draw.polygon(tri_img, (255, 240, 60, 180), [(40, 10), (10, 110), (70, 110)])

# ---- Crear cuadrado fijo ----
square_rect = pygame.Rect(400, 250, 80, 80)
square_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
square_surface.fill((255, 0, 0, 128))  # rojo semitransparente

# ---- Máscara del cuadrado ----
square_mask = pygame.mask.from_surface(square_surface)

# ---- Bucle principal ----
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((0, 0, 0))
    pygame.draw.circle(screen, (100, 100, 255), centro, 20)  # planeta

    # Calcular posición orbital
    x = centro[0] + radio * math.cos(math.radians(angulo))
    y = centro[1] + radio * math.sin(math.radians(angulo))
    rot_angle = -angulo + 90
    tri_rot = pygame.transform.rotate(tri_img, rot_angle)
    tri_rect = tri_rot.get_rect(center=(x, y))

    # ---- Crear copia para modificar (triángulo visible) ----
    visible_tri = tri_rot.copy()

    # ---- Calcular intersección de máscaras ----
    tri_mask = pygame.mask.from_surface(tri_rot)
    offset = (square_rect.x - tri_rect.x, square_rect.y - tri_rect.y)
    overlap = tri_mask.overlap_mask(square_mask, offset)

    # ---- "Borrar" la parte solapada del triángulo ----
    for px in range(overlap.get_size()[0]):
        for py in range(overlap.get_size()[1]):
            if overlap.get_at((px, py)):
                visible_tri.set_at((px, py), (0, 0, 0, 0))  # píxel transparente

    # ---- Dibujar todo ----
    screen.blit(visible_tri, tri_rect)
    screen.blit(square_surface, square_rect)

    pygame.display.flip()
    clock.tick(60)
    angulo = (angulo + 1) % 360
