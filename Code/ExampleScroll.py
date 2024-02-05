import pygame
import os

# Definir el tamaño de la ventana
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# Definir el tamaño del nivel
LEVEL_WIDTH = 1024
LEVEL_HEIGHT = 768

# Inicializar Pygame
pygame.init()

# Crear la ventana
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Definir los colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Cargar los recursos del jugador y el nivel
PLAYER_IMAGE = pygame.image.load(os.path.join('assets', 'player.png')).convert_alpha()
PLAYER_IMAGE = pygame.transform.scale(PLAYER_IMAGE, (64, 64))

LEVEL_IMAGE = pygame.image.load(os.path.join('assets', 'level.png')).convert_alpha()
LEVEL_IMAGE = pygame.transform.scale(LEVEL_IMAGE, (LEVEL_WIDTH, LEVEL_HEIGHT))

# Definir la clase del jugador
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = PLAYER_IMAGE
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, dx, dy):
        # Actualizar la posición del jugador
        self.rect.x += dx
        self.rect.y += dy

        # Limitar la posición del jugador al nivel
        if self.rect.x < 0:
            self.rect.x = 0
        elif self.rect.right > LEVEL_WIDTH:
            self.rect.right = LEVEL_WIDTH
        if self.rect.y < 0:
            self.rect.y = 0
        elif self.rect.bottom > LEVEL_HEIGHT:
            self.rect.bottom = LEVEL_HEIGHT

# Crear el jugador
player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

# Crear un grupo de sprites para el jugador
player_group = pygame.sprite.Group()
player_group.add(player)

# Bucle principal del juego
running = True
clock = pygame.time.Clock()
while running:
    # Procesar eventos del teclado y la ventana
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Obtener las teclas pulsadas
    keys = pygame.key.get_pressed()

    # Actualizar la posición del jugador
    dx = 0
    dy = 0
    if keys[pygame.K_LEFT]:
        dx = -5
    elif keys[pygame.K_RIGHT]:
        dx = 5
    if keys[pygame.K_UP]:
        dy = -5
    elif keys[pygame.K_DOWN]:
        dy = 5
    player.update(dx, dy)

    # Desplazar la ventana según la posición del jugador
    x_offset = SCREEN_WIDTH // 2 - player.rect.centerx
    y_offset = SCREEN_HEIGHT // 2 - player.rect.centery
    x_offset = max(SCREEN_WIDTH - LEVEL_WIDTH, x_offset)
    y_offset = max(SCREEN_HEIGHT - LEVEL_HEIGHT, y_offset)
    screen.blit(LEVEL_IMAGE, (x_offset, y_offset))
    player_group.draw(screen)

    # Actualizar la ventana
    pygame.display.flip()

    # Limitar la tasa de fotogramas
    clock.tick(60)

# Salir de Pygame
pygame.quit()
