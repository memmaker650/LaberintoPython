import pygame, math, sys

pygame.init()
screen = pygame.display.set_mode((600, 600))
clock = pygame.time.Clock()

# Centro de la órbita (el planeta)
centro = (300, 300)
radio = 40
angulo = 0

# ======= Crear el triángulo (satélite) =======
satellite_img = pygame.Surface((40, 60), pygame.SRCALPHA)

# Coordenadas del triángulo (vértice arriba, base abajo)
# Vértice cerca del planeta, base en el exterior
p1 = (20, 5)   # vértice
p2 = (5, 55)   # esquina izquierda base
p3 = (35, 55)  # esquina derecha base

# Dibujamos triángulo amarillo con alpha 50%
color = (199,180,70, 128)  # RGBA → alpha=128 (50%)
pygame.draw.polygon(satellite_img, color, [p1, p2, p3])

# ======= Bucle principal =======
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((0, 0, 0))
    pygame.draw.circle(screen, (100, 100, 255), centro, 20)  # planeta

    # Calculamos posición orbital
    x = centro[0] + radio * math.cos(math.radians(angulo))
    y = centro[1] + radio * math.sin(math.radians(angulo))

    # El triángulo debe "apuntar" al planeta (vértice hacia dentro)
    rot_angle = -angulo + 90  # ajustamos sentido para que mire al centro

    # Rotamos el triángulo
    rotated = pygame.transform.rotate(satellite_img, rot_angle)
    rect = rotated.get_rect(center=(x, y))

    # Dibujamos el triángulo rotado
    screen.blit(rotated, rect)

    pygame.display.flip()
    clock.tick(60)
    angulo = (angulo + 1) % 360
