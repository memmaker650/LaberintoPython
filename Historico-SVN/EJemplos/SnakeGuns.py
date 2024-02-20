import pygame,sys
from pygame.locals import *
from random import randint


ancho = 1280
alto = 720


class Snake(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("../../Resources/DogDown1.png")
        self.rect = self.image.get_rect()
        self.rect.centerx = 80
        self.rect.centery = 80

        self.vel = 1
        self.vidas = 3
        self.viviendo = True

    def update(self):
        keys = pygame.key.get_pressed()

        if keys[K_DOWN]:
           self.rect.y += self.vel
           if self.rect.bottom > 720:
              self.rect.bottom = 720

        if keys[K_UP]:
           self.rect.y -= self.vel
           if self.rect.top < 0:
              self.rect.top = 0

        if keys[K_RIGHT]:
           self.rect.x += self.vel
           if self.rect.right > 1280:
              self.rect.right = 1280

        if keys[K_LEFT]:
           self.rect.x -= self.vel
           if self.rect.left < 0:
              self.rect.left = 0

        if keys[K_SPACE] and not bullets:
            bullet = Bullet(self.rect.right, self.rect.centery)

            all_sprites.add(bullet)
            bullets.add(bullet)


class ZombieN1(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load("../../Resources/Chainsaw.png")
        self.rect = self.image.get_rect()

        self.s = Snake()
        self.y = self.s.rect.top
        self.x = randint(1016,1280)

        self.rect.top = self.y
        self.rect.right = self.x
        self.vel = 1

    def update(self):
        self.rect.left = self.rect.left - self.vel


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("../../Code/assets/disparo.png")
        self.image = pygame.transform.rotate(self.image, 90)
        self.rect = self.image.get_rect()
        self.rect.centery = y
        self.rect.centerx = x
        self.vel = 3

    def update(self):
        self.rect.right += self.vel
        # Destruir cuando se salga de la ventana (lado derecho)
        if self.rect.right > 1280:
            self.kill()

all_sprites = pygame.sprite.Group()
bullets = pygame.sprite.Group()
zombies = pygame.sprite.Group()

def Game():
    pygame.init()
    pygame.key.set_repeat(1,25)

    ventana = pygame.display.set_mode((ancho, alto))
    pygame.display.set_caption("Game")

    player = Snake()
    enemy1 = ZombieN1()
    all_sprites.add(enemy1)
    zombies.add(enemy1)
    all_sprites.add(player)

    BG = pygame.image.load("../../Code/assets/level.jpg")

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
               pygame.quit()
               sys.exit()

        # Comprobamos si algún disparo colisiona con algún enemigo
        ## En caso afirmativo se destruyen ambos
        pygame.sprite.groupcollide(zombies, bullets, True, True)

        # Actualizamos todos los sprites del juego
        all_sprites.update()
        ventana.fill((205,69,159))
        # Dibujamos todos los sprites
        all_sprites.draw(ventana)
        pygame.display.flip()

    pygame.quit()

Game()