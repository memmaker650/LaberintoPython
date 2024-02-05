import mates

import logging
import statistics
import random
import os
import sys

import pygame
from pygame.locals import *


class personaje:
    casilla = 0

    def moveRight(self):
        self.x = self.x + self.speed
        self.logMovimiento('Derecha', self.x, self.y)

    def moveLeft(self):
        self.x = self.x - self.speed
        self.logMovimiento('Izquierda', self.x, self.y)

    def moveUp(self):
        self.y = self.y - self.speed
        self.logMovimiento('Arriba', self.x, self.y)

    def moveDown(self):
        self.y = self.y + self.speed
        self.logMovimiento('Abajo', self.x, self.y)

    def getPosicion(self):
        return self.casilla

    def logMovimiento(self, direccion, finalx, finaly):
        logging.info('Movimiento %s hasta %s', direccion, finalx, finaly)


class Enemigo(personaje):
    x = 12
    y = 12
    speed = 1

    def __init__(self):
        logging.info("Init Enemigo")

    def __init__(self, vx, vy):
        logging.info("")
        self.x = random.randint(0, vx)
        self.y = random.randint(0, vy)
    def pintarEnemigo(self, posicion):
        logging.info("Pintamos Enemigo")

class Player(personaje):
    x = 23
    y = 23
    speed = 1

    def __init__(self):
        logging.info("Init Player")

    def pintarEnemigo(self, posicion):
        logging.info("Pintamos Jugador")