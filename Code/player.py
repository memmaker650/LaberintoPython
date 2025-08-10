import mates
import KerberosIA

import logging
import statistics
import random
import os
import sys

import pygame
from pygame.locals import *

import pygame as pg
from pygame.math import Vector2

IMG_DIR = "Resources"

# Especificación de la paleta de colores
BLANCO = (255, 255, 255)
GRIS = (155, 155, 155)
NEGRO = (0, 0, 0)
ROJO = (255, 0, 0)
VERDE = (0, 255, 0)
AZUL = (0, 0, 255)
AMARILLO = (255, 255, 0)
AMARILLO_CLARO = (253, 253, 150)
MARRON = (200, 100, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
HC74225 = (199, 66, 37)
H61CD35 = (97, 205, 53)

SCREEN_WIDTH = 864
SCREEN_HEIGHT = 864

# Directorio de imágenes principal
carpeta_imagenes = os.path.join(IMG_DIR, "imagenes")

# # Explosiones
# animacion_explosion1 = {'t1': [], 't2': [], 't3': [], 't4': []}
#
# for x in range(24):
#     archivo_explosiones = f'expl_01_00{x:02d}.png'
# 	imagenes = pygame.image.load(os.path.join(carpeta_imagenes_explosiones, archivo_explosiones)).convert()
# 	imagenes.set_colorkey(NEGRO)
# 	imagenes_t1 = pygame.transform.scale(imagenes, (32,32))
# 	animacion_explosion1['t1'].append(imagenes_t1)
# 	imagenes_t2 = pygame.transform.scale(imagenes, (64,64))
# 	animacion_explosion1['t2'].append(imagenes_t2)
# 	imagenes_t3 = pygame.transform.scale(imagenes, (128, 128))
# 	animacion_explosion1['t3'].append(imagenes_t3)
# 	imagenes_t4 = pygame.transform.scale(imagenes, (256, 256))
# 	animacion_explosion1['t4'].append(imagenes_t4)

IMG_DIR = "./Resources"
# Especificación de la paleta de colores
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
ROJO = (255, 0, 0)
VERDE = (0, 255, 0)
AZUL = (0, 0, 255)
HC74225 = (199, 66, 37)
H61CD35 = (97, 205, 53)

def load_image(nombre, dir_imagen, alpha=False):
    # Encontramos la ruta completa de la imagen
    ruta = os.path.join(dir_imagen, nombre)
    try:
        image = pygame.image.load(ruta)
    except:
        print("Error, no se puede cargar la imagen: " + ruta)
        logging.error("Error, no se puede cargar la imagen: " + ruta)
        sys.exit(1)

    # Comprobar si la imagen tiene "canal alpha" (como los png)
    if alpha is True:
        image = image.convert_alpha()
    else:
        image = image.convert()
    return image

class barraDeVida(pygame.sprite.Sprite):
    def __init__(self, x, y, valor, screen):
        pygame.draw.rect(screen, (255, 0, 0), (self.hitbox[0], self.hitbox[1] - 20, 50, 10))
        pygame.draw.rect(screen, (0, 128, 0), (self.hitbox[0], self.hitbox[1] - 20, 50 - (5 * (10 - self.valor)), 10))

class panelPuntuacion(pygame.sprite.Sprite):
    puntos = int
    reloj_min = int
    reloj_sec = int
    arma = int
    balasContador = int

    def __init__(self, screen):
        super.__init__()
        # This should go inside the redrawGameWindow function
        font = pygame.font.SysFont('comicsans', 30, True)
        text = font.render("Score: " + str(self.puntos), 1, (0, 0, 0))  # Arguments are: text, anti-aliasing, color
        screen.blit(text, (390, 10))

        self.puntos = 0
        self.reloj_min = 10
        self.reloj_sec = 00
        self.arma = 1
        self.balasContador = 0

class Disparos(pygame.sprite.Sprite):
    x = int
    y = int
    municion = 0

    def __init__(self, dx, dy):
        super().__init__()
        self.image = load_image("disparo.png", "assets", alpha=True)
        #self.image = pygame.transform.scale(pygame.image.load("assets/disparo.png").convert(), (10, 20))
        self.image = pygame.transform.scale(self.image, (10, 20))
        self.rect = self.image.get_rect()
        self.rect.x = dx
        self.rect.y = dy
        self.y = dy
        self.x = dx
        self.municion = 10

    def definirMunicion(self, valor):
        self.municion = valor

    def actualizarMunicion(self, valor, sentido):  # 0 restar y 1 sumar
        if (sentido == 0):
            self.municion -= valor
        elif (sentido == 1):
            self.municion += valor

    def rotarBala(self, angulo):
        return pygame.transform.rotate(self.imagen, angulo)

    def update(self):
        logging.info('Dentro UPDATE BALA.')
        self.rect.y -= 5

        if self.rect.x < 0:
            self.kill()
        elif self.rect.y < 0:
            self.kill()
        elif self.rect.x > SCREEN_WIDTH:
            self.kill()
        elif self.rect.y > SCREEN_HEIGHT:
            self.kill()


class Player(pygame.sprite.Sprite):
    x = 23
    y = 23
    casilla = 0

    vida = int

    flagDisparo = False
    orientacion = 1  # 1 arriba, 2 derecha, 3 abajo y 4 izquierda.
    speedV = 1
    speedH = 1
    image = None
    rect = None
    bala = Disparos
    balas = pygame.sprite.Group()
    MazeParedes = pygame.sprite.Group

    def __init__(self):
        logging.info("Init Player")
        super().__init__()
        self.flagDisparo = False
        self.image = load_image("player_modif.png", IMG_DIR, alpha=True)
        self.image = pygame.transform.scale(self.image, (25, 25))
        self.rect = self.image.get_rect()

    def stop(self):
        self.speedH = 0
        self.speedV = 0

    def andar(self):
        if(self.speedH < 6):
            self.speedH = self.speedH + 1

        if (self.speedV < 6):
            self.speedV = self.speedV + 1

    def moveRight(self):
        self.andar()
        self.x = self.x + self.speedH
        self.logMovimiento("Derecha", self.x, self.y)
        self.orientacion = 3

    def moveLeft(self):
        self.andar()
        self.x = self.x - self.speedH
        self.logMovimiento('Izquierda', self.x, self.y)
        self.orientacion = 1

    def moveUp(self):
        self.andar()
        self.y = self.y - self.speedV
        self.logMovimiento('Arriba', self.x, self.y)
        self.orientacion = 2

    def moveDown(self):
        self.andar()
        self.y = self.y + self.speedV
        self.logMovimiento('Abajo', self.x, self.y)
        self.orientacion = 4

    def asignarVida(self, valor):
        self.vida = valor

    def cambiarVida(self, valor):
        self.vida += valor

    def getPosicion(self):
        return self.casilla

    def logMovimiento(self, direccion, finalx, finaly):
        logging.info('Movimiento %s hasta x: %s, y %s', direccion, finalx, finaly)

    def pintarJugador(self):
        logging.info("Pintamos Jugador")

    def update(self):
        logging.debug('Dentro Update JUGADOR.')
        # Actualizar el rectángulo de colisión con la posición actual
        self.rect.x = self.x
        self.rect.y = self.y
        
        vieja_pos = self.rect.topleft

        # Si hay colisión, volvemos a la posición anterior
        #if pygame.sprite.spritecollideany(self, self.MazeParedes):
        #    logging.debug('Colisión JUGADOR con LABERINTO.')
        #    self.rect.topleft = vieja_pos

    def rotar(self, angulo):
        return pygame.transform.rotate(self.imagen, angulo)

    def escalaGrises(self):
        return pygame.transform.grayscale(self.imagen)

    def disparo(self):
        if self.bala.municion > 0:
            self.bala = Disparos(self.x, self.y)
            self.balas.add(self.bala)
            self.flagDisparo = True
            self.bala.municion -= 1

class Explosiones(pygame.sprite.Sprite):
    def __init__(self, centro, dimensiones):
        pygame.sprite.Sprite.__init__(self)
	    # self.dimensiones = dimensiones
	    # #self.image = animacion_explosion1[self.dimensiones][0]
	    # self.rect = self.image.get_rect()
	    # self.rect.center = centro
	    # self.fotograma = 0
	    # self.frecuencia_fotograma = 35
	    # self.actualizacion = pygame.time.get_ticks()

    # def update(self):
    #     ahora = pygame.time.get_ticks()
    #     if ahora - self.actualizacion > self.frecuencia_fotograma:
    #         self.actualizacion = ahora
    #         self.fotograma += 1
    #         if self.fotograma == len(animacion_explosion1[self.dimensiones]):
    #             self.kill()
    #         else:
    #             centro = self.rect.center
    #             self.image = animacion_explosion1[self.dimensiones][self.fotograma]
    #             self.rect = self.image.get_rect()
    #             self.rect.center = centro

class Enemigo(pygame.sprite.Sprite):
    x = 12
    y = 12
    casilla = 0

    vida = int
    flagDisparo = bool
    isJefeEnemigo = bool

    orientacion = str
    visionImage = None
    visionPos = Vector2
    speedV = 1
    speedH = 1
    angle = int
    imageEnemigo = None
    imageJefeEnemigo = None
    rect = None
    bala = Disparos
    balas = pygame.sprite.Group
    MazeParedes = pygame.sprite.Group
    balasArray = []
    kia = None

    def __init__(self):
        logging.info("Init Enemigo")
        super().__init__()
        self.orientacion = 'N'
        self.kia = KerberosIA.KerberosIA()
        self.vida = 100
        self.visionPos = Vector2 (0, 0)
        self.angle = 0
        self.flagDisparo = False
        self.imageEnemigo = load_image("Chainsaw.png", IMG_DIR, alpha=True)
        self.imageEnemigo = pygame.transform.scale(self.imageEnemigo, (40, 40))
        self.rect = self.imageEnemigo.get_rect()
        self.imageJefeEnemigo = load_image("wilber-eeek.png", IMG_DIR, alpha=True)
        self.imageJefeEnemigo = pygame.transform.scale(self.imageJefeEnemigo, (40, 40))
        self.rect = self.imageJefeEnemigo.get_rect()
        self.visionImage = load_image("linterna.png", "Code/assets", alpha=True)
        self.visionImage = pygame.transform.scale(self.visionImage, (60, 60))
        self.visionImage.set_alpha(128)
        self.isJefeEnemigo = False

    def inicio(self, vx, vy):
        logging.info("Inicio Enemigos")
        self.x = random.randint(0, vx)
        self.y = random.randint(0, vy)

    def definirJefeEnemigo(self):
        self.isJefeEnemigo = True

    def inicioCelda(self, cell):
        self.casilla = cell

    def logPosicionEnemigo(self):
        logging.info('Posición Enemigo: x: %s e y: %s con casilla --> %s', self.x, self.y, self.casilla)

    def moveRight(self):
        self.x = self.x + self.speedH
        self.logMovimiento('Derecha', self.x, self.y)

    def moveLeft(self):
        self.x = self.x - self.speedH
        self.logMovimiento('Izquierda', self.x, self.y)

    def moveUp(self):
        self.y = self.y - self.speedV
        self.logMovimiento('Arriba', self.x, self.y)

    def moveDown(self):
        self.y = self.y + self.speedV
        self.logMovimiento('Abajo', self.x, self.y)

    def getPosicion(self):
        return self.casilla

    def vision(self, pos):
        logging.info("Pintamos cono de visión")
        self.rect = self.visionImage.get_rect(center=pos)
        self.visionPos = Vector2(pos)
        self.offset = Vector2(200, 0)
        self.angle = -45


    def visionRotar(self):
        logging.info("visión Rotar")
        self.angle = self.angle - 2
        # Add the rotated offset vector to the pos vector to get the rect.center.
        self.rect.center = self.visionPos.rotate(self.angle)

    def update(self):
        logging.debug('Dentro Update ENEMIGOS.')
        # Guardar posición previa
        self.prev_x = getattr(self, 'prev_x', self.x)
        self.prev_y = getattr(self, 'prev_y', self.y)

        # Actualizar el rectángulo de colisión con la posición actual
        self.rect.x = self.x
        self.rect.y = self.y
        
        self.visionRotar()
        self.moveDown()
        
        # Actualizar rect tras mover
        self.rect.x = self.x
        self.rect.y = self.y

    def revertir_movimiento(self):
        # Revertir a la posición previa tras colisión
        if hasattr(self, 'prev_x') and hasattr(self, 'prev_y'):
            self.x = self.prev_x
            self.y = self.prev_y
            self.rect.x = self.x
            self.rect.y = self.y

    def cambiar_direccion(self):
        # Cambio simple de dirección: invertir velocidad vertical
        self.speedV = -self.speedV if self.speedV != 0 else -1
        # Pequeño desplazamiento para evitar quedarse pegado
        self.y += self.speedV
        self.rect.y = self.y

    def logMovimiento(self, direccion, finalx, finaly):
        logging.info('Movimiento %s hasta x: %s, y %s', direccion, finalx, finaly)

    def pintarEnemigo(self):
        logging.info("Pintamos Enemigo")
        

    def pintarJefeEnemigo(self):
        logging.info("Pintamos Enemigo")
        

    def rotar(self, angulo):
        return pygame.transform.rotate(self.imagen, angulo)

    def escalaGrises(self):
        return pygame.transform.grayscale(self.imagen)

    def disparo(self):
        self.bala = Disparos(self.rect.centerx, self.rect.top)
        self.balas.add(self.bala)
        self.flagDisparo = True


