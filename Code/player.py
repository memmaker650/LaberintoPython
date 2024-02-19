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

IMG_DIR = "Resources"
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
        image = pygame.image.load("../" + ruta)
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


class Player(pygame.sprite.Sprite):
    x = 23
    y = 23
    casilla = 0

    vida = int

    speedV = 1
    speedH = 1
    image = None
    rect = None
    balas = pygame.sprite.Group

    def __init__(self):
        logging.info("Init Player")
        super().__init__()


    def stop(self):
        self.speedH = 0
        self.speedV = 0

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
        self.image = load_image("player_modif.png", IMG_DIR, alpha=True)
        self.image = pygame.transform.scale(self.image, (25, 25))
        self.rect = self.image.get_rect()

    def update(self):
        logging.debug('Dentro Update JUGADOR.')

    def rotar(self, angulo):
        return pygame.transform.rotate(self.imagen, angulo)

    def escalaGrises(self):
        return pygame.transform.grayscale(self.imagen)

    def disparo(self):
        bala = Disparos(self.rect.centerx, self.rect.top)
        self.balas.add(bala)

class Disparos(pygame.sprite.Sprite):
    municion = int

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.transform.scale(pygame.image.load("../assets/disparo.png").convert(),(10,20))
        self.image.set_colorkey(NEGRO)
        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.municion = 10

    def definirMunicion(self, valor):
        self.municion = valor

    def actualizarMunicion(self, valor, sentido):  # 0 restar y 1 sumar
        if (sentido == 0):
            self.municion -= valor
        elif (sentido == 1):
            self.municion += valor

    def update(self):
        self.rect.y -= 25
        if self.rect.bottom < 0:
            self.kill()

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

    orientacion = str
    visionImage = None
    visionPos = Vector2
    speedV = 1
    speedH = 1
    angle = int
    image = None
    rect = None
    balas = pygame.sprite.Group
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

    def inicio(self, vx, vy):
        logging.info("Inicio Enemigos")
        self.x = random.randint(0, vx)
        self.y = random.randint(0, vy)

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
        self.visionImage = load_image("linterna.png", '/Code/assets/', alpha=True)
        self.visionImage = pygame.transform.scale(self.visionImage, (60, 60))
        self.visionImage.set_alpha(128)
        self.rect = self.visionImage.get_rect(center=pos)
        self.visionPos = Vector2(pos)
        self.offset = Vector2(200, 0)
        self.angle = -45

    # TODO Crear el método UPDATE para gestionar todos los movimientos.
    def visionRotar(self):
        logging.info("Pintamos cono de visión")
        self.angle = self.angle - 2
        # Add the rotated offset vector to the pos vector to get the rect.center.
        self.rect.center = self.visionPos.rotate(self.angle)

    def update(self):
        logging.debug('Dentro Update ENEMIGOS.')
        self.visionRotar()
        self.moveDown()

    def logMovimiento(self, direccion, finalx, finaly):
        logging.info('Movimiento %s hasta x: %s, y %s', direccion, finalx, finaly)

    def pintarEnemigo(self):
        logging.info("Pintamos Enemigo")
        self.image = load_image("wilber-eeek.png", IMG_DIR, alpha=True)
        self.image = pygame.transform.scale(self.image, (40, 40))
        self.rect = self.image.get_rect()

    def pintarJefeEnemigo(self):
        logging.info("Pintamos Enemigo")
        self.image = load_image("Chainsaw.png", IMG_DIR, alpha=True)
        self.image = pygame.transform.scale(self.image, (40, 40))
        self.rect = self.image.get_rect()

    def rotar(self, angulo):
        return pygame.transform.rotate(self.imagen, angulo)

    def escalaGrises(self):
        return pygame.transform.grayscale(self.imagen)

    def disparo(self):
        bala = Disparos(self.rect.centerx, self.rect.top)
        self.balas.add(bala)



