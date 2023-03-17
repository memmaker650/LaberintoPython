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

    def moveLeft(self):
        self.x = self.x - self.speed

    def moveUp(self):
        self.y = self.y - self.speed

    def moveDown(self):
        self.y = self.y + self.speed

    def getPosicion(self):
        return self.casilla


class Enemigo(personaje):
    x = 100
    y = 100
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
    x = 44
    y = 44
    speed = 1

    def __init__(self):
        logging.info("Init Player")

    def pintarEnemigo(self, posicion):
        logging.info("Pintamos Jugador")