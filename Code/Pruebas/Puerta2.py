import pygame
import sys
import math

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

# --- OPCIONES DE BISAGRA ---
# 'left', 'right', 'top', 'bottom'
HINGE_SIDE = 'left'  # Cambia esto para cambiar el lado de la bisagra

door_angle = 0           # 0 = cerrada, 90 = abierta
opening = False
closing = False
speed = 3                # grados por frame

# --- SUPERFICIE DE PUERTA (vista aérea) ---
door_surface = pygame.Surface((door_length, door_thickness), pygame.SRCALPHA)
pygame.draw.rect(door_surface, COLOR_PUERTA, (0, 0, door_length, door_thickness))
pygame.draw.rect(door_surface, COLOR_BORDE, (0, 0, door_length, door_thickness), 2)

def get_pivot_position(hinge_side):
    """Obtiene la posición del pivote en coordenadas locales de la superficie."""
    if hinge_side == 'left':
        return (0, door_thickness / 2)  # Lado izquierdo, centro vertical
    elif hinge_side == 'right':
        return (door_length, door_thickness / 2)  # Lado derecho, centro vertical
    elif hinge_side == 'top':
        return (door_length / 2, 0)  # Parte superior, centro horizontal
    elif hinge_side == 'bottom':
        return (door_length / 2, door_thickness)  # Parte inferior, centro horizontal
    else:
        return (0, door_thickness / 2)  # Por defecto: izquierda

def draw_door(angle, hinge_side='left'):
    """Dibuja la puerta rotando sobre el lado especificado."""
    # Rotar la superficie
    rotated = pygame.transform.rotate(door_surface, -angle)
    
    # Obtener la posición del pivote en coordenadas locales
    pivot_local = get_pivot_position(hinge_side)
    
    # Convertir ángulo a radianes
    angle_rad = math.radians(-angle)
    
    # Centro de la superficie original
    center_x, center_y = door_length / 2, door_thickness / 2
    
    # Vector desde el centro hasta el pivote
    pivot_rel_to_center = (pivot_local[0] - center_x, pivot_local[1] - center_y)
    
    # Aplicar rotación al vector relativo
    rotated_pivot_x = (pivot_rel_to_center[0] * math.cos(angle_rad) - 
                       pivot_rel_to_center[1] * math.sin(angle_rad))
    rotated_pivot_y = (pivot_rel_to_center[0] * math.sin(angle_rad) + 
                       pivot_rel_to_center[1] * math.cos(angle_rad))
    
    # Nueva posición del pivote después de rotar (en coordenadas de la superficie original)
    new_pivot_x = center_x + rotated_pivot_x
    new_pivot_y = center_y + rotated_pivot_y
    
    # Obtener el rectángulo de la superficie rotada
    rotated_rect = rotated.get_rect()
    
    # Calcular la posición de dibujo para que el pivote quede en (pivot_x, pivot_y)
    draw_x = pivot_x - new_pivot_x
    draw_y = pivot_y - new_pivot_y
    
    screen.blit(rotated, (draw_x, draw_y))
    
    # Dibujar un punto en el pivote para visualización (opcional)
    pygame.draw.circle(screen, (255, 0, 0), (int(pivot_x), int(pivot_y)), 3)

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
            
            # Cambiar el lado de la bisagra con las teclas 1, 2, 3, 4
            elif event.key == pygame.K_1:
                HINGE_SIDE = 'left'
                door_angle = 0  # Resetear ángulo al cambiar bisagra
            elif event.key == pygame.K_2:
                HINGE_SIDE = 'right'
                door_angle = 0
            elif event.key == pygame.K_3:
                HINGE_SIDE = 'top'
                door_angle = 0
            elif event.key == pygame.K_4:
                HINGE_SIDE = 'bottom'
                door_angle = 0

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
    draw_door(door_angle, HINGE_SIDE)

    # Mostrar información
    font = pygame.font.SysFont(None, 28)
    msg = font.render("ESPACIO: abrir/cerrar | 1-4: cambiar bisagra", True, (255, 255, 255))
    screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 20))
    
    hinge_text = font.render(f"Bisagra: {HINGE_SIDE.upper()}", True, (255, 255, 0))
    screen.blit(hinge_text, (WIDTH//2 - hinge_text.get_width()//2, 50))

    pygame.display.flip()