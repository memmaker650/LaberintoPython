import mates

import logging
import statistics
import random
import os
import sys
import math

import pygame
from pygame.locals import *

import json
from plyer import notification
from levels_parser import LevelParser

# -----------
# Constantes
# -----------

SCREEN_WIDTH = 864
SCREEN_HEIGHT = 1000
BIAS = 136
CASILLA_PIXEL = 32
NUM_CASILLAS_H = 40
NUM_CASILLAS_VERTI = 27
NUM_CASILLAS_CAMARA = 27
IMG_DIR = "Resources"
EXPLOSION_DIR = "assets/explosions/images/explosion/"
SONIDO_DIR = "Resources/Sonidos"
FPS = 60 # desired framerate in frames per second.

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
COLOR_PUERTA = (160, 110, 60)

class posicion:
    x = 0
    y = 0

    def __init__(self, valorX=0, valorY=0):
        self.x = valorX
        self.y = valorY

class Maze:
    M = NUM_CASILLAS_H
    N = NUM_CASILLAS_VERTI

    posicionCamara = int = 13
    movimientoCamara = int = 0
    flagCamara = bool = True
    flagCamaraCambio = bool = False

    posicionInitJugador = int = 0

    posicionPuerta = [] # Casilla y orientación de la puerta 1 vertical 4 horizontal.

    MazeLaberinto = []
    MazeParedes = pygame.sprite.Group()
    MazeExtra = pygame.sprite.Group()
    
    MazeHueso = pygame.sprite.Group()
    MazePilaHuesos = pygame.sprite.Group()
    MazeBandera = pygame.sprite.Group()
    MazeLlave = pygame.sprite.Group()
    MazeLlavePuerta = pygame.sprite.Group()
    MazeChampi = pygame.sprite.Group()
    MazeRedStar = pygame.sprite.Group()
    MazeOro = pygame.sprite.Group()
    MazeTunnel = pygame.sprite.Group()
    MazeGranada = pygame.sprite.Group()
    MazeBotiquin = pygame.sprite.Group()
    MazePuertas = pygame.sprite.Group()
    
    imageHuesos = pygame.image.load("./Resources/Bone.png")
    imagePilaHuesos = pygame.image.load("./Resources/PileOfBones.png")
    imageFinNivel = pygame.image.load("./Resources/banderaPirataRoja2.png")
    imageLlave = pygame.image.load("./Resources/llave.png")
    imageLlavePuerta = pygame.image.load("./Resources/llave_puerta.png")
    imageChampi = pygame.image.load("./Resources/powerMushroom.png")
    imageRedStar = pygame.image.load("./Resources/redstar.png")
    imageTunnel = pygame.image.load("./Resources/CompuertaTunnel.png")
    imageGranada = pygame.image.load("./Resources/granada-de-mano.png")
    imageOro = pygame.image.load("./Resources/Oro.png")
    imageTNT = pygame.image.load("./Resources/TNT.png")
    imageTNTAbajo = pygame.image.load("./Resources/TNTAbajo.png")
    imageBotiquin = pygame.image.load("./Resources/medical-box.png")
       
    flagHuesos = bool = True
    flagPilaHuesos = bool = True
    flagBanderaFinNivel = bool = True
    flagLlave = bool = True
    flagLlavePuerta = bool = True
    flagChampi = bool = True
    flagRedStar = bool = True
    flagTunnel = bool = True
    flagGranada = bool = True
    flagOro = bool = True
    flagTNT = bool = True
    flagBotiquin = bool = True

    flagCentroCasillaJefeEnemigo = bool = True
    PosicionCruz = posicion
    flagPintarCasilla = bool = True
    pintaKasillaNumSuelo = True
    PosicionPintarCasilla = posicion

    # Valores de la puerta
    door_length = 32
    door_thickness = 10
    door_x = int
    door_y = int
    pivot_x = door_x
    pivot_y = door_y
    door_angle = 0           # Apertura animada: 0 = cerrada, 90 = abierta

    Doorspeed = int = 3                # grados por frame
    door_surface = pygame.Surface((32, 32))  # ✅ CORRECTO

    ObjetosNoPintar = []

    def __init__(self):
        self.M = NUM_CASILLAS_H
        self.N = NUM_CASILLAS_VERTI

        self.maze = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0,
            0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0,
            0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        ]
        self.mazeDataExtra = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 11, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,
            0, 2, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,
            0, 1, 9, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 15, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0,
            0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 2, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0,
            0, 13, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 33, 1, 1, 0, 0,
            0, 1, 1, 0, 1, 0, 11, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 33, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 3, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 8, 1, 1, 0, 1, 0, 1, 11, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 1, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 7, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 33, 1, 1, 1, 1, 1, 1, 1, 0, 1, 44, 1, 1, 1, 1, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1, 6, 1, 1, 1, 2, 0, 1, 1, 1, 1, 1, 1, 1, 0, 8, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        ]
        self.MazeLaberinto = self.maze
        self._crear_paredes()
        notification.notify(title='Maze created', message='X', app_name='OctoPussy', app_icon='./Resources/player.icns')

    def _crear_paredes(self):
        bx = 0
        by = 0
        for i in range(0, self.M * self.N):
            if self.maze[bx + (by * self.M)] == 0:
                rectSuelo = pygame.sprite.Sprite()
                rectSuelo.image = pygame.Surface([CASILLA_PIXEL, CASILLA_PIXEL])
                rectSuelo.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL + BIAS, CASILLA_PIXEL, CASILLA_PIXEL)
                self.MazeParedes.add(rectSuelo)
                
            bx = bx + 1
            if bx > self.M - 1:
                bx = 0
                by = by + 1

    def addText(self, texto, x, y):
        self.font = pygame.font.SysFont('Arial', 25)
        self.font.render(texto, True, (255, 0, 0))

    def draw(self, display_surf, image_surf, w_surf, casillasObjetos={}):
        bx = 0
        by = 0

        xfont = pygame.font.SysFont('Corbel', 14)

        textWallDebug = pygame.sprite.Group()
        # rendering a text written in Corbel font.

        self.movimientoCamara = self.posicionCamara - 13

        for i in range(0, self.M * self.N):
            if (self.movimientoCamara == 0 and bx <= 27) or (self.movimientoCamara > 0 and bx >= self.movimientoCamara and bx <= 26 + self.movimientoCamara): 
                rectSuelo = pygame.sprite.Sprite()
                rectSuelo.image = pygame.Surface([(bx-self.movimientoCamara) * CASILLA_PIXEL, by * CASILLA_PIXEL + BIAS])
                rectSuelo.rect = pygame.Rect((bx-self.movimientoCamara) * CASILLA_PIXEL, by * CASILLA_PIXEL + BIAS, 32, 32)

                if self.maze[bx + (by * self.M)] == 1:
                    display_surf.blit(image_surf, ((bx-self.movimientoCamara) * CASILLA_PIXEL, by * CASILLA_PIXEL + BIAS))
                    self.rect = image_surf.get_rect()
                else:
                    display_surf.blit(w_surf, ((bx-self.movimientoCamara) * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                    
                # Pintar el número de casilla en el suelo.
                # -------------------------------------------------
                if self.pintaKasillaNumSuelo:
                    # print("Dentro Pintar NumKasilla.")
                    textWallMark = xfont.render(str(i), True, (255, 0, 0))
                    display_surf.blit(textWallMark, rectSuelo.rect.center)

                casiya = bx + (by * self.M)
                # if not len(casillasObjetos) == 0:
                    # print("CASIYA: ", casiya)
                    # print("SET: ", *casillasObjetos)
                
                # Hueso
                if self.mazeDataExtra[bx + (by * self.M)] == 2 and self.flagHuesos and not (casiya in casillasObjetos):
                    display_surf.blit(self.imageHuesos, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                    huesos = pygame.sprite.Sprite()
                    huesos.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL +BIAS, 32, 32)
                    self.MazeHueso.add(huesos) 

                # Pila de Huesos
                if self.mazeDataExtra[bx + (by * self.M)] == 3 and self.flagPilaHuesos:
                    display_surf.blit(self.imagePilaHuesos, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                    Pilahuesos = pygame.sprite.Sprite()
                    Pilahuesos.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                    self.MazePilaHuesos.add(Pilahuesos) 

                # Bandera Fin Nivel
                if self.mazeDataExtra[bx + (by * self.M)] == 4:
                    display_surf.blit(self.imageFinNivel, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                    Bandera = pygame.sprite.Sprite()
                    Bandera.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                    self.MazeBandera.add(Bandera)
                    # self.MazeBandera.image = self.imageFinNivel
                    # self.MazeBandera.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                    # self.MazeBandera.mask = pygame.mask.from_surface(self.imageFinNivel)

                # Accesorios del nivel.
                #------------------------
                # Llave dorada
                if self.mazeDataExtra[bx + (by * self.M)] == 6 and self.flagLlave:
                    imagen_escalada = pygame.transform.scale(self.imageLlave, (20, 20))
                    display_surf.blit(imagen_escalada, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                    key = pygame.sprite.Sprite()
                    key.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                    self.MazeLlave.add(key)

                # Llave Puerta
                if self.mazeDataExtra[bx + (by * self.M)] == 7 and self.flagLlavePuerta:
                    imagen_escalada = pygame.transform.scale(self.imageLlavePuerta, (9, 21))
                    display_surf.blit(imagen_escalada, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                    Doorkey = pygame.sprite.Sprite()
                    Doorkey.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                    self.MazeLlavePuerta.add(Doorkey)

                # Champiñón
                if self.mazeDataExtra[bx + (by * self.M)] == 8 and self.flagChampi:
                    imagen_escalada = pygame.transform.scale(self.imageChampi, (20, 20))
                    display_surf.blit(imagen_escalada, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                    Champi = pygame.sprite.Sprite()
                    Champi.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                    self.MazeChampi.add(Champi)

                # Estrella Roja poderosa
                if self.mazeDataExtra[bx + (by * self.M)] == 9 and self.flagRedStar:
                    imagen_escalada = pygame.transform.scale(self.imageRedStar, (20, 20))
                    display_surf.blit(imagen_escalada, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                    redStar = pygame.sprite.Sprite()
                    redStar.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                    self.MazeRedStar.add(redStar)

                # Tunel
                if self.mazeDataExtra[bx + (by * self.M)] == 10:
                    rect_surf = pygame.Surface((32, 32))
                    rect_surf.set_alpha(128)  # Transparencia 50%
                    rect_surf.fill((200, 200, 200))  # Gris claro
                    display_surf.blit(rect_surf, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                    imagen_escalada = pygame.transform.scale(self.imageTunnel, (35, 35))
                    display_surf.blit(imagen_escalada, (bx * CASILLA_PIXEL-2, by * CASILLA_PIXEL+BIAS-2))
                    Tunnel = pygame.sprite.Sprite()
                    Tunnel.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                    self.MazeTunnel.add(Tunnel)

                # Monedas de Oro
                if self.mazeDataExtra[bx + (by * self.M)] == 11 and self.flagOro and not (casiya in casillasObjetos): 
                    imagen_escalada = pygame.transform.scale(self.imageOro, (20, 20))
                    display_surf.blit(imagen_escalada, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                    Oro = pygame.sprite.Sprite()
                    Oro.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                    self.MazeOro.add(Oro)

                # Granada
                if self.mazeDataExtra[bx + (by * self.M)] == 13 and self.flagGranada:
                    rect_surf = pygame.Surface((15, 15))
                    rect_surf.set_alpha(128)  # Transparencia 50%
                    rect_surf.fill((200, 200, 200))  # Gris claro
                    display_surf.blit(rect_surf, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                    imagen_escalada = pygame.transform.scale(self.imageGranada, (15, 15))
                    display_surf.blit(imagen_escalada, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                    granada = pygame.sprite.Sprite()
                    granada.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                    self.MazeGranada.add(granada)

                if self.mazeDataExtra[bx + (by * self.M)] == 44:
                    self.posicionInitJugador = bx + (by * self.M)  # Casilla

                # Botiquín
                if self.mazeDataExtra[bx + (by * self.M)] == 15 and self.flagBotiquin:
                    imagen_escalada = pygame.transform.scale(self.imageBotiquin, (20, 20))
                    display_surf.blit(imagen_escalada, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                    Botiquin = pygame.sprite.Sprite()
                    Botiquin.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                    self.MazeBotiquin.add(Botiquin)

                # Puerta/s
                #------------------------
                if self.mazeDataExtra[bx + (by * self.M)] == 33:
                    kasylla = bx + (by * self.M)

                    self.posicionPuerta.append([kasylla, 1])

                    x = bx * CASILLA_PIXEL
                    y = by * CASILLA_PIXEL + BIAS

                    # Determinar orientación
                    if not self.esAlcanzableCasilla(kasylla - 1) and \
                       not self.esAlcanzableCasilla(kasylla + 1):

                        orientacion = 4
                        Maze.posicionPuerta.append((kasylla, 4))
                    else:
                        orientacion = 1
                        Maze.posicionPuerta.append((kasylla, 1))

                    # 🔥 CREAS TU CLASE PUERTA REAL
                    puerta = Puerta(x, y, orientacion)

                    self.MazePuertas.add(puerta)

            bx = bx + 1
            if bx > self.M - 1:
                bx = 0
                by = by + 1

    def pintarDetallesCasillaEnemigo(self, display_surface):
        # Cruz Posición
        #------------------------
        if self.flagCentroCasillaJefeEnemigo:
            tam = 5
            # Color verde chillón
            VERDE = (0, 255, 0)
            # Dibujar la X
            pygame.draw.line(display_surface, VERDE, (self.PosicionCruz.x - tam, self.PosicionCruz.y - tam), (self.PosicionCruz.x + tam, self.PosicionCruz.y + tam), 3)
            pygame.draw.line(display_surface, VERDE, (self.PosicionCruz.x - tam, self.PosicionCruz.y + tam), (self.PosicionCruz.x + tam, self.PosicionCruz.y - tam), 3)

        # Pintar rect Casilla
        #------------------------
        if self.flagPintarCasilla:
            Naranja = (244, 127, 38)
            pygame.draw.rect(display_surface, Naranja, (self.PosicionPintarCasilla.x, self.PosicionPintarCasilla.y, CASILLA_PIXEL, CASILLA_PIXEL), 1)

    def moverCamara(self, posicionX, posicionY):
        # Debo calcular cuando el player está en la columna 27 y en una casilla de suelo.
        # print("Mov Cámara", self.movimientoCamara)
        UbicacionX = int(posicionX / CASILLA_PIXEL) 

        if UbicacionX >= 26 and self.flagCamara and self.posicionCamara >= 13:
            if(self.esAlcanzable(posicionX, posicionY)):
                self.posicionCamara += 1
                self.movimientoCamara += 1
                self.flagCamara = False
                self.flagCamaraCambio = True
                # print("Condición CUMPLIDA cámara")
        
        if UbicacionX <= 1 and self.flagCamara and self.posicionCamara > 13:
            self.posicionCamara -= 1
            self.movimientoCamara -= 1
            self.flagCamara = False
            self.flagCamaraCambio = True
            # print("Condición IZQ cámara")

    # Calcular las conexiones de las casillas de SUELO solamente.
    @staticmethod
    def precalcular_conexiones(laberinto, ancho, alto):
        conexiones = {}

        for casilla in range(len(laberinto)):

            if laberinto[casilla] != 1:
                continue

            dirs = []

            fila = casilla // ancho
            col = casilla % ancho

            # ARRIBA
            if fila > 0:
                arriba = casilla - ancho
                if laberinto[arriba] == 1:
                    dirs.append(0)

            # DERECHA
            if col < ancho - 1:
                derecha = casilla + 1
                if laberinto[derecha] == 1:
                    dirs.append(1)

            # ABAJO
            if fila < alto - 1:
                abajo = casilla + ancho
                if laberinto[abajo] == 1:
                    dirs.append(2)

            # IZQUIERDA
            if col > 0:
                izquierda = casilla - 1
                if laberinto[izquierda] == 1:
                    dirs.append(3)

            conexiones[casilla] = dirs

        return conexiones
    
    def nuevaCasillaTrasCamaraMovida(self, casilla: int) -> int:
        # La pantalla original 
        columna = casilla % self.N
        fila = casilla // self.N
        nuevaCasilla = (fila*self.N) + columna

        return nuevaCasilla

    def nuevaPosicionXYTrasCamaraMovida(self, x: int, y: int) -> int:
        # La pantalla original 
        x_final = x - 32
        posi=posicion(x_final, y)
        
        return posi

    # Método ESTÁTICO para saber si está o no en el CENTRO de la CASILLA, para cálculos de posición.
    @staticmethod
    def estaCentroCasilla(x, y) -> bool:
        celda = Maze.calcularCasilla(x, y)
        pos = Maze.centroCasilla(celda)

        if (x > pos.x) or (y > pos.y):
            return True   
        else:
            return False

    @staticmethod
    def elementoVisibleCasilla(kasiya) -> bool:
        value = kasiya % 40
        if value < 27:
            return True
        else: 
            return False

    @staticmethod
    def elementoVisiblePosicion(posx, posy) -> bool:
        casillas = Maze.calcularCasilla(posx, posy)
        return Maze.elementoVisibleCasilla(casillas)        
        
    @staticmethod
    def calcularCasilla(valorX, valorY) -> int:
        columna = valorX // CASILLA_PIXEL
        fila = (valorY - BIAS) // CASILLA_PIXEL

        casilla = columna + fila * NUM_CASILLAS_H
        # logging.info(f"Valor calculado: {casilla}")

        logging.debug(f"calcularCasilla:posición: X {valorX} and Y {valorY} ==> Casilla: {int(casilla)}")
        # print(f"calcularCasilla: posición: X {valorX} and Y {valorY} ==> Casilla: {int(casilla)}")

        return casilla

    @staticmethod
    def calcularPixelPorCasilla(Casilla):
        pos = posicion()
        pos.x = (Casilla % NUM_CASILLAS_H) * CASILLA_PIXEL 
        pos.y = ((Casilla // NUM_CASILLAS_H) * CASILLA_PIXEL) + BIAS 
        # logging.debug(f"calcularPixelPorCasilla: Casilla {Casilla} a posición: X {pos.x} and Y {pos.y}")
        
        return pos

    @staticmethod
    def centroCasilla(Casilla) -> posicion:
        position = posicion()
        position.x = (Casilla % NUM_CASILLAS_H) * CASILLA_PIXEL + (CASILLA_PIXEL // 2)
        position.y = ((Casilla // NUM_CASILLAS_H) * CASILLA_PIXEL) + BIAS + (CASILLA_PIXEL // 2)
        
        Maze.PosicionCruz = posicion()
        Maze.PosicionCruz = position
        # Se pinta a partir de la esquina superior izquierda.
        Maze.PosicionPintarCasilla = posicion()
        Maze.PosicionPintarCasilla.x = position.x - (CASILLA_PIXEL // 2)   # // 2 es división entera de 2.
        Maze.PosicionPintarCasilla.y = position.y - (CASILLA_PIXEL // 2)
        
        # logging.debug(f" Centro Casilla: K {Casilla} a posición: X {position.x} and Y {position.y}")
        # print(" Centro Casilla: K {Casilla} a posición: X {position.x} and Y {position.y}")

        return position

    # Casilla de suelo. Cambiar y chequear
    def esAlcanzable(self, x, y) -> bool:
        logging.info("Dentro Método alcanzable")
        eqCasilla = None

        eqCasilla = Maze.calcularCasilla(x, y)

        if x > SCREEN_WIDTH or y > SCREEN_HEIGHT or x < 0 or y < 0:
            logging.info("esAlcanzble : X= %s and Y= %s", x, y)
            if x > SCREEN_WIDTH or x < 0 :
                logging.info("esAlcanzble : X fuera de rango.", x)
                return False
            elif y > SCREEN_HEIGHT or y < 0:
                logging.info("esAlcanzble : Y fuera de rango.", y)
                return False
            else:
                logging.info("Raro en esAlcanzble ")
            
        if self.maze[eqCasilla] == 0:
            return False
        elif self.maze[eqCasilla] == 1: 
            return True
        else: 
            return False

    def esAlcanzableCasilla(self, casilla) -> bool:
        logging.info("Dentro Método alcanzable KASILLA")
        # print("MazeLab:", casilla)

        #if casilla > (NUM_CASILLAS*NUM_CASILLAS) or casilla < 0: 
        #    if casilla < 0 :
        #        logging.info("esAlcanzble : casilla fuera de rango.")
        #        return False
        #    elif casilla > NUM_CASILLAS*NUM_CASILLAS :
        #        logging.info("esAlcanzble : casilla fuera de rango.")
        #        return False
        #    else:
        #        logging.info("Raro en esAlcanzble KSY")
            
        if self.maze[casilla] == 0:
            return False
        elif self.maze[casilla] == 1: 
            return True
        else: 
            return False

    # MÉTODOs para las puertas
    #-------------------------------------------
    #def inicioPuertas(self):
    #    i = 0
    #    for porte in self.MazePuertas:
    #        CasillaPuerta = self.maze.calcularCasilla(porte.rect.x, porte.rect.y)
    #        # print(f"KASIYA ubicación puerta: ", CasillaPuerta, " pos : ", porte.rect.x,", ", porte.rect.y, "* Se Pintan ?: ", MazeLab.Maze.elementoVisiblePosicion(porte.rect.x, porte.rect.y))
#
    #        door_orient = 4
    #        for x in self.posicionPuerta:
    #            if x[0] == CasillaPuerta:
    #                door_orient = x[1]
    #                break
#
    #        if self.flagPrint_info:
    #           print("Puerta pivote: ", self.pivot_x, self.pivot_y,
    #                 " Orientación: ", door_orient, " Apertura: ", self.door_angle)
#
    #        i += 1
#
    #def updatePuertas(self):
    #    self.JefeEnemigo.vision(self.JefeEnemigo.imageJefeEnemigo.get_rect().center)
    #    centro = (self.JefeEnemigo.x+10, self.JefeEnemigo.y+10)
    #    radio = 20
    #    x = centro[0] + radio * math.cos(math.radians(self.JefeEnemigo.angle))
    #    y = centro[1] + radio * math.sin(math.radians(self.JefeEnemigo.angle))
    #    rot_angle = -self.JefeEnemigo.angle + 90
    #    rotated = pygame.transform.rotate(self.JefeEnemigo.visionImage, rot_angle)
    #    rect = rotated.get_rect(center=(x, y))
    #    self.pantalla.blit(rotated, rect)
#
    #def draw_Puerta(self, pantalla, rectaP):
    #    """
    #    Rota la puerta alrededor de la bisagra (círculo gris).
    #    El lado corto junto al pivote permanece fijo; el largo barre 90°.
    #    """
    #    print("Dentro dRaW PUERTA.")
#
    #    pygame.draw.rect(
    #        pantalla,
    #        (0, 0, 0),
    #        rectaP,
    #        2
    #    )
#
    #    pygame.draw.circle(
    #        self.pantalla, (128, 128, 128),
    #        (int(self.pivot_x), int(self.pivot_y)), 3
    #    )
    #
    #def draw_Puertas(self, pantalla):
    #    """
    #    Rota la puerta alrededor de la bisagra (círculo gris).
    #    El lado corto junto al pivote permanece fijo; el largo barre 90°.
    #    """
    #    print("Dentro dRaW PUERTA.")
#
    #    for porte in self.MazePuertas:
    #        pygame.draw.rect(
    #            pantalla,
    #            COLOR_PUERTA,
    #            porte.rect,
    #            2
    #        )
#
    #        pygame.draw.circle(
    #            self.pantalla, (128, 128, 128),
    #            (int(self.pivot_x), int(self.pivot_y)), 3
    #        )
#
#-------------------------------------
#   ***    E X P L O S I Ó N 
#-------------------------------------
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()

        # Cargar frames
        self.frames = []

        for i in range(21):
            ruta = os.path.join(
                "Code",
                EXPLOSION_DIR,
                f"expl_04_00{i:02}.png"
            )
            print(f"Ruta file Explosiones: {ruta}")

            imagen = pygame.image.load(ruta).convert_alpha()

            # Opcional: escalar
            imagen = pygame.transform.scale(imagen, (128, 128))

            self.frames.append(imagen)

        # Frame actual
        self.frame_actual = 0

        # Imagen inicial
        self.image = self.frames[self.frame_actual]

        # Posición
        self.rect = self.image.get_rect(center=(x, y))

        # Tiempo
        self.tiempo_ultimo_frame = pygame.time.get_ticks()

        # 2.5 segundos / 21 frames
        self.duracion_frame = 150  # milisegundos

    def update(self):
        ahora = pygame.time.get_ticks()
        print(" --> Explosion INTO.")

        # Cambiar frame
        if ahora - self.tiempo_ultimo_frame > self.duracion_frame:

            self.tiempo_ultimo_frame = ahora

            self.frame_actual += 1

            # ¿Se acabó la animación?
            if self.frame_actual >= len(self.frames):
                self.kill()
                return

            self.image = self.frames[self.frame_actual]


#-------------------------------------
#  ***   N U B E    DE     H U M O
#-------------------------------------
class Smoke(pygame.sprite.Sprite):
    # Cache global
    FRAMES = None

    def __init__(self, x, y, alfa=120):

        super().__init__()

        # Cargar imágenes una sola vez
        if Smoke.FRAMES is None:
            Smoke.FRAMES = []

            for i in range(31):

                ruta = os.path.join(
                    "Code",
                    EXPLOSION_DIR,
                    f"puff_smoke_01_00{i:02}.png"
                )

                img = pygame.image.load(ruta).convert_alpha()

                # -----------------------------
                # ESCALAR
                img = pygame.transform.scale(img, (140, 140))

                # TEÑIR DE GRIS
                # -----------------------------
                # RGB más bajos = gris más apagado
                img.fill(
                    (110, 110, 110, 255),
                    special_flags=pygame.BLEND_RGBA_MULT
                )

                # -----------------------------
                # TRANSPARENCIA
                img.set_alpha(alfa)

                Smoke.FRAMES.append(img)

        self.frames = Smoke.FRAMES

        # Frame inicial
        self.frame_actual = 0
        self.image = self.frames[self.frame_actual]

        # Centrado
        self.rect = self.image.get_rect(center=(x, y))

        # Tiempo
        self.tiempo_ultimo_frame = pygame.time.get_ticks()

        # Más lento que explosión
        self.duracion_frame = 90

    def update(self):
        ahora = pygame.time.get_ticks()

        if ahora - self.tiempo_ultimo_frame > self.duracion_frame:

            self.tiempo_ultimo_frame = ahora

            self.frame_actual += 1

            # Final animación
            if self.frame_actual >= len(self.frames):
                self.kill()
                return

            # Crecimiento progresivo
            escala = 140 + self.frame_actual

            # Fade out progresivo
            nuevo_alpha = max(0, 210 - self.frame_actual * 3)

            # Escalar frame actual
            self.image = pygame.transform.scale(
                self.frames[self.frame_actual],
                (escala, escala)
            )

            # Aplicar nueva transparencia
            self.image.set_alpha(nuevo_alpha)

            # Mantener el centro estable
            centro = self.rect.center
            self.rect = self.image.get_rect(center=centro)

class Puerta(pygame.sprite.Sprite):

    def __init__(self, x, y, orientacion):
        super().__init__()

        self.orientacion = orientacion

        self.ancho = 15
        self.alto = 32

        self.image_original = pygame.Surface(
            (self.ancho, self.alto),
            pygame.SRCALPHA
        )

        # Color base
        self.image_original.fill((160, 90, 30))

        # Borde negro
        pygame.draw.rect(
           self.image_original,
           (0, 0, 0),
           (0, 0, self.ancho, self.alto),
           2
        )

        pygame.draw.rect(
            self.image_original,
            (160, 90, 30),
            (0, 0, self.ancho, self.alto)
        )

        # Línea vertical central
        pygame.draw.line(
            self.image_original,
            (0, 0, 0),
            (self.ancho // 2, 0),
            (self.ancho // 2, self.alto),
            1
        )

        # Línea horizontal opcional (refuerzo visual)
        pygame.draw.line(
            self.image_original,
            (0, 0, 0),
            (0, self.alto // 2),
            (self.ancho, self.alto // 2),
            1
        )

        vertices = [
            (0, 0),
            (self.ancho, 0),
            (self.ancho, self.alto),
            (0, self.alto)
        ]
        
        pygame.draw.lines(
            self.image_original,
            (0, 0, 0),
            True,
            vertices,
            1
        )

        self.image_original.fill((170, 100, 40))

        for i in range(3):
            x = (i + 1) * self.ancho // 4

            pygame.draw.line(
                self.image_original,
                (90, 50, 20),
                (x, 2),
                (x, self.alto - 2),
                1
            )

        self.image = self.image_original

        self.angle = 0
        self.abierta = False
        self.velocidad = 2

        # 🔥 POSICIÓN BASE (bisagra)
        self.x = x
        self.y = y

        # radio de apertura (IMPORTANTE)
        self.radio = self.alto  # o CASILLA_PIXEL si quieres más exagerado

        # pivot fijo
        self.pivot = (x, y)

        self.rect = self.image.get_rect(center=self.pivot)
    
    def update(self):
        if self.abierta:
            if self.angle < 90:
                self.angle += self.velocidad
        else:
            if self.angle > 0:
                self.angle -= self.velocidad

        self.rotar()
    
    def rotar(self):
        # Ángulo en radianes
        rad = math.radians(self.angle)

        # Posición desplazada desde la bisagra
        x = self.x + self.radio * math.cos(rad)
        y = self.y + self.radio * math.sin(rad)

        # Rotación visual
        rot_angle = -self.angle + 90

        self.image = pygame.transform.rotate(
            self.image_original,
            rot_angle
        )

        self.rect = self.image.get_rect(center=(x, y))
    
    def draw(self, pantalla):
        pantalla.blit(self.image, self.rect)

        # bisagra
        pygame.draw.circle(
            pantalla,
            (128, 128, 128),
            (int(self.x), int(self.y)),
            3
        )