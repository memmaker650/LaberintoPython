import pygame
import random

# Definir colores
NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
GRIS_CLARO = (200, 200, 200)
AMARILLO = (255, 255, 0)

# Definir la ventana
ANCHO = 800
ALTO = 600
ventana = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Ejemplo de luces con Pygame")

# Cargar imágenes
imagen_personaje = pygame.image.load("assets/player.png").convert_alpha()
imagen_linterna = pygame.image.load("assets/linterna.png").convert_alpha()
imagen_pared = pygame.image.load("assets/level.png").convert_alpha()

# Definir la linterna
linterna = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA, 32)
linterna.fill((0, 0, 0, 255))
linterna.blit(imagen_linterna, (0, 0))

# Definir las paredes
paredes = []
for i in range(5):
    x = random.randint(0, ANCHO - imagen_pared.get_width())
    y = random.randint(0, ALTO - imagen_pared.get_height())
    paredes.append(pygame.Rect(x, y, imagen_pared.get_width(), imagen_pared.get_height()))

# Definir el personaje
x_personaje = ANCHO / 2
y_personaje = ALTO / 2
rect_personaje = pygame.Rect(x_personaje, y_personaje, imagen_personaje.get_width(), imagen_personaje.get_height())

# Definir el reloj
reloj = pygame.time.Clock()

# Bucle principal
while True:
    # Procesamiento de eventos
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            exit()

    # Actualizar la posición del personaje
    teclas = pygame.key.get_pressed()
    if teclas[pygame.K_LEFT] and rect_personaje.left > 0:
        rect_personaje.move_ip(-5, 0)
    if teclas[pygame.K_RIGHT] and rect_personaje.right < ANCHO:
        rect_personaje.move_ip(5, 0)
    if teclas[pygame.K_UP] and rect_personaje.top > 0:
        rect_personaje.move_ip(0, -5)
    if teclas[pygame.K_DOWN] and rect_personaje.bottom < ALTO:
        rect_personaje.move_ip(0, 5)

    # Limpiar la pantalla
    ventana.fill(NEGRO)

    # Dibujar las paredes
    for pared in paredes:
        pygame.draw.rect(ventana, GRIS_CLARO, pared)

    # Dibujar la linterna
    linterna_rect = linterna.get_rect()
    linterna_rect.center = rect_personaje.center
    ventana.blit(linterna, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    # Dibujar el personaje
    ventana.blit(imagen_personaje, rect_personaje)

    # Actualizar la ventana
    pygame.display.update()

    # Esperar un tiempo para mantener la tasa de frames
    reloj.tick(60)
