import pygame
import sys

pygame.init()

# --- CONFIGURACIÓN BÁSICA ---
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Puerta vista desde arriba - Maze")
clock = pygame.time.Clock()

# --- COLORES ---
COLOR_SUELO = (70, 70, 70)
COLOR_PARED = (40, 40, 40)
COLOR_PUERTA = (160, 110, 60)
COLOR_BORDE = (90, 60, 40)

# --- PARÁMETROS DE LA PUERTA ---
door_length = 80
door_thickness = 15
door_x = WIDTH // 2
door_y = HEIGHT // 2

pivot_x = door_x
pivot_y = door_y

door_angle = 0           # 0 = cerrada, 90 = abierta
opening = False
closing = False
speed = 3                # grados por frame

# --- SUPERFICIE DE PUERTA (vista aérea) ---
door_surface = pygame.Surface((door_length, door_thickness), pygame.SRCALPHA)
pygame.draw.rect(door_surface, COLOR_PUERTA, (0, 0, door_length, door_thickness))
pygame.draw.rect(door_surface, COLOR_BORDE, (0, 0, door_length, door_thickness), 2)

def draw_maze_background():
    """Dibuja un fondo tipo laberinto simple."""
    screen.fill(COLOR_PARED)
    for i in range(0, WIDTH, 40):
        pygame.draw.line(screen, (50, 50, 50), (i, 0), (i, HEIGHT))
    for j in range(0, HEIGHT, 40):
        pygame.draw.line(screen, (50, 50, 50), (0, j), (WIDTH, j))

    # paredes laterales
    pygame.draw.rect(screen, (90, 90, 90), (0, 0, WIDTH, 10))
    pygame.draw.rect(screen, (90, 90, 90), (0, HEIGHT-10, WIDTH, 10))
    pygame.draw.rect(screen, (90, 90, 90), (0, 0, 10, HEIGHT))
    pygame.draw.rect(screen, (90, 90, 90), (WIDTH-10, 0, 10, HEIGHT))

def draw_door(angle):
    """Dibuja la puerta rotando sobre su bisagra izquierda."""
    rotated = pygame.transform.rotate(door_surface, -angle)
    rect = rotated.get_rect(midleft=(pivot_x, pivot_y))
    screen.blit(rotated, rect.topleft)

# --- BUCLE PRINCIPAL ---
while True:
    dt = clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # alternar entre abrir y cerrar
                if door_angle <= 0:
                    opening = True
                    closing = False
                elif door_angle >= 90:
                    closing = True
                    opening = False

    # --- ACTUALIZACIÓN ---
    if opening:
        door_angle += speed
        if door_angle >= 90:
            door_angle = 90
            opening = False
    elif closing:
        door_angle -= speed
        if door_angle <= 0:
            door_angle = 0
            closing = False

    # --- DIBUJADO ---
    draw_maze_background()
    draw_door(door_angle)

    font = pygame.font.SysFont(None, 28)
    msg = font.render("Pulsa ESPACIO para abrir/cerrar puerta", True, (255, 255, 255))
    screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 20))

    pygame.display.flip()
