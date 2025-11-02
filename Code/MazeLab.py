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
NUM_CASILLAS = 27
IMG_DIR = "Resources"
SONIDO_DIR = "Resources/Sonidos"
FPS = 60 # desired framerate in frames per second.

class posicion:
    x = 0
    y = 0

    def __init__(self, valorX, valorY):
        x = valorX
        y = valorY

class Maze:
    M = NUM_CASILLAS
    N = NUM_CASILLAS

    posicionInitJugador = int = 0

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

    ObjetosNoPintar = []

    def __init__(self):
        self.M = NUM_CASILLAS
        self.N = NUM_CASILLAS

        self.maze = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0,
            0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0,
            0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        ]
        self.mazeDataExtra = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 11, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 2, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 9, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 15, 1, 1, 0,
            0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 2, 1, 1, 1, 1, 0,
            0, 13, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 11, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0,
            0, 3, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 8, 1, 1, 0, 1, 0, 1, 11, 1, 0, 1, 1, 0,
            0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0,
            0, 1, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 7, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 10, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 44, 1, 1, 1, 1, 2, 1, 1, 1, 0,
            0, 1, 6, 1, 1, 1, 2, 0, 1, 1, 1, 1, 1, 1, 1, 0, 8, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
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

        xfont = pygame.font.SysFont('Corbel', 13)

        textWallDebug = pygame.sprite.Group()
        # rendering a text written in Corbel font.


        for i in range(0, self.M * self.N):
            if self.maze[bx + (by * self.M)] == 1:
                display_surf.blit(image_surf, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL + BIAS))
                self.rect = image_surf.get_rect()
            else:
                display_surf.blit(w_surf, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                rectSuelo = pygame.sprite.Sprite()
                rectSuelo.image = pygame.Surface([bx * CASILLA_PIXEL, by * CASILLA_PIXEL + BIAS])
                rectSuelo.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL + BIAS, 32, 32)

            casiya = bx + (by * self.M)
            # if not len(casillasObjetos) == 0:
                # print("CASIYA: ", casiya)
                # print("SET: ", *casillasObjetos)

            if self.mazeDataExtra[bx + (by * self.M)] == 2 and self.flagHuesos and not (casiya in casillasObjetos):
                display_surf.blit(self.imageHuesos, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                huesos = pygame.sprite.Sprite()
                huesos.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL +BIAS, 32, 32)
                self.MazeHueso.add(huesos) 

            if self.mazeDataExtra[bx + (by * self.M)] == 3 and self.flagPilaHuesos:
                display_surf.blit(self.imagePilaHuesos, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                Pilahuesos = pygame.sprite.Sprite()
                Pilahuesos.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                self.MazePilaHuesos.add(Pilahuesos) 

            if self.mazeDataExtra[bx + (by * self.M)] == 4:
                display_surf.blit(self.imageFinNivel, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                Bandera = pygame.sprite.Sprite()
                Bandera.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                self.MazeBandera.add(Bandera)
                # self.MazeBandera.image = self.imageFinNivel
                # self.MazeBandera.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                # self.MazeBandera.mask = pygame.mask.from_surface(self.imageFinNivel)

            # Accesorios del nivel.
            if self.mazeDataExtra[bx + (by * self.M)] == 6 and self.flagLlave:
                imagen_escalada = pygame.transform.scale(self.imageLlave, (20, 20))
                display_surf.blit(imagen_escalada, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                key = pygame.sprite.Sprite()
                key.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                self.MazeLlave.add(key)

            if self.mazeDataExtra[bx + (by * self.M)] == 7 and self.flagLlavePuerta:
                imagen_escalada = pygame.transform.scale(self.imageLlavePuerta, (9, 21))
                display_surf.blit(imagen_escalada, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                Doorkey = pygame.sprite.Sprite()
                Doorkey.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                self.MazeLlavePuerta.add(Doorkey)

            if self.mazeDataExtra[bx + (by * self.M)] == 8 and self.flagChampi:
                imagen_escalada = pygame.transform.scale(self.imageChampi, (20, 20))
                display_surf.blit(imagen_escalada, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                Champi = pygame.sprite.Sprite()
                Champi.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                self.MazeChampi.add(Champi)
            
            if self.mazeDataExtra[bx + (by * self.M)] == 9 and self.flagRedStar:
                imagen_escalada = pygame.transform.scale(self.imageRedStar, (20, 20))
                display_surf.blit(imagen_escalada, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                redStar = pygame.sprite.Sprite()
                redStar.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                self.MazeRedStar.add(redStar)
            
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
            
            if self.mazeDataExtra[bx + (by * self.M)] == 11 and self.flagOro and not (casiya in casillasObjetos): 
                imagen_escalada = pygame.transform.scale(self.imageOro, (20, 20))
                display_surf.blit(imagen_escalada, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                Oro = pygame.sprite.Sprite()
                Oro.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                self.MazeOro.add(Oro)

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
            
            if self.mazeDataExtra[bx + (by * self.M)] == 15 and self.flagBotiquin:
                imagen_escalada = pygame.transform.scale(self.imageBotiquin, (20, 20))
                display_surf.blit(imagen_escalada, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS))
                Botiquin = pygame.sprite.Sprite()
                Botiquin.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL+BIAS, 32, 32)
                self.MazeBotiquin.add(Botiquin)

            bx = bx + 1
            if bx > self.M - 1:
                bx = 0
                by = by + 1

    @staticmethod
    def calcularCasilla(valorX, valorY):
        casilla = int(valorX / CASILLA_PIXEL) + (int((valorY-BIAS) / CASILLA_PIXEL))* NUM_CASILLAS
        logging.info("Valor calculado: %s", casilla)

        logging.debug("calcularCasilla:posición: X %s and Y %s ==> Casilla: %s", valorX, valorY, int(casilla))

        return casilla

    @staticmethod
    def calcularPixelPorCasilla(Casilla):
        posicion.x = (Casilla % NUM_CASILLAS) * CASILLA_PIXEL
        posicion.y = (int(Casilla / NUM_CASILLAS) * CASILLA_PIXEL) + BIAS
        logging.debug("calcularPixelPorCasilla: Casilla %s a posición: X %s and Y %s", Casilla, posicion.x, posicion.y)

        return posicion

    # Casilla de suelo. Cambiar y chequear
    def esAlcanzable(self, x, y):
        logging.info("Dentro Método alcanzable")
        eqCasilla = None

        eqCasilla = Maze.calcularCasilla(x, y)

        if x > SCREEN_WIDTH | y > SCREEN_HEIGHT | x < 0 | y < 0:
            logging.info("esAlcanzble : X= %s and Y= %s", x, y)
            if x > SCREEN_WIDTH | x < 0 :
                logging.info("esAlcanzble : X fuera de rango.", x)
                return False
            elif y > SCREEN_HEIGHT | y < 0:
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

    def esAlcanzableCasilla(self, casilla):
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