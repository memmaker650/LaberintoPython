import pygame

# Definir el tamaño de la ventana
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Inicializar Pygame
pygame.init()

# Crear la ventana
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Definir los colores
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# Definir el personaje
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 5

    def update(self):
        # Controlar el movimiento del personaje con las teclas de flechas
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed

# Definir los elementos del nivel
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Level():
    def __init__(self):
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()

        # Crear las plataformas del nivel
        platform = Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50)
        platform2 = Platform(0, 0, SCREEN_WIDTH, 50)
        platform3 = Platform(0, 0, 50, SCREEN_HEIGHT)
        platform4 = Platform(SCREEN_WIDTH-50, 0, 50, SCREEN_HEIGHT)

        # Añadir las plataformas al grupo de sprites y al grupo de plataformas
        self.all_sprites.add(platform)
        self.platforms.add(platform)
        self.all_sprites.add(platform2)
        self.platforms.add(platform2)
        self.all_sprites.add(platform3)
        self.platforms.add(platform3)
        self.all_sprites.add(platform4)
        self.platforms.add(platform4)

    def draw(self, screen):
        # Dibujar todos los sprites del nivel en la pantalla
        self.all_sprites.draw(screen)

    def collide_with_platforms(self, player):
        # Verificar si el jugador colisiona con alguna plataforma
        for platform in self.platforms:
            if player.rect.colliderect(platform.rect):
                return True
        return False

# Crear un objeto del nivel y del personaje
level = Level()
player = Player(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)

# Añadir el personaje al grupo de sprites del nivel
level.all_sprites.add(player)

# Bucle principal del juego
running = True
while running:
    # Procesar eventos del teclado y la ventana
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Actualizar el personaje
    level.all_sprites.update()

    # Verificar si el jugador colisiona con alguna plataforma
    if level.collide_with_platforms(player):
        player.rect.bottom = level.platforms.sprites()[0].rect.top

    # Dibujar el nivel y el personaje en la pantalla
    screen.fill(WHITE)
    level.draw(screen)
    pygame.display.flip()

# Salir del juego
pygame.quit()