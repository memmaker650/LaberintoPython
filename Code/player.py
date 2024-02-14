import mates
import KerberosIA

import logging
import statistics
import random
import os
import sys

import pygame
from pygame.locals import *

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

class Player(pygame.sprite.Sprite):
    x = 23
    y = 23
    casilla = 0

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

    def getPosicion(self):
        return self.casilla

    def logMovimiento(self, direccion, finalx, finaly):
        logging.info('Movimiento %s hasta x: %s, y %s', direccion, finalx, finaly)

    def pintarJugador(self):
        logging.info("Pintamos Jugador")
        self.image = load_image("player_modif.png", IMG_DIR, alpha=True)
        self.image = pygame.transform.scale(self.image, (25, 25))
        self.rect = self.image.get_rect()

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

    def definirMunicion(self, valor):
        self.municion = valor

    def updateMunicion(self, valor, sentido):  # 0 restar y 1 sumar
        if (sentido == 0):
            self.municion -= valor
        elif (sentido == 1):
            self.municion += valor

class Enemigo(pygame.sprite.Sprite):
    x = 12
    y = 12
    casilla = 0

    orientacion = str
    visionImage = None
    speedV = 1
    speedH = 1
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

    def vision(self):
        logging.info("Pintamos cono de visión")
        self.visionImage = load_image("linterna.png", '/Code/assets/', alpha=True)
        self.visionImage = pygame.transform.scale(self.visionImage, (60, 60))
        self.visionImage.set_alpha(128)
        self.rect = self.visionImage.get_rect()

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



