import mates
import player

import logging
import statistics
import random
import os
import sys

import json


import pygame
from pygame.locals import *
import sqlite3

from plyer import notification

# -----------
# Constantes
# -----------

SCREEN_WIDTH = 864
SCREEN_HEIGHT = 864
CASILLA_PIXEL = 32
NUM_CASILLAS = 27
IMG_DIR = "Resources"
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

# ------------------------------
# Clases y Funciones utilizadas
# ------------------------------
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


def load_sound(nombre, dir_sonido):
    ruta = os.path.join(dir_sonido, nombre)

    print("Intentar cargar el sonido.")

    try:
        sonido = pygame.mixer.Sound("../" + ruta)
    except (pygame.error) as message:
        print("No se pudo cargar el sonido:", ruta)
        logging.error("Error, no se puede cargar el sonido: " + ruta)
        sonido = None
    return sonido

class estadisticasSquid:
    tiempoNivel = 0
    EnemigosMuertos = 0
    puntos = 0

class partidaGuardada:
    nivel = 0
    puntos = 0
    enemigosMuertos = 0
    llavesRojas = 0
    llavesAmarillos = 0
    llavesNegras = 0

class posicion:
    x = 0
    y = 0

    def __init__(self, valorX, valorY):
        x = valorX
        y = valorY

class Maze:
    M = NUM_CASILLAS
    N = NUM_CASILLAS
    MazeParedes = pygame.sprite.Group()
    MazeExtra = pygame.sprite.Group()
    imageHuesos = pygame.image.load("./Resources/Bone.png")
    imagePilaHuesos = pygame.image.load("./Resources/PileOfBones.png")
    imageFinNivel = pygame.image.load("./Resources/banderaPirataRoja2.png")
       

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
            0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 2, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 2, 1, 1, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0,
            0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0,
            0, 3, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0,
            0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0,
            0, 1, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,
            0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 0,
            0, 1, 1, 1, 1, 1, 2, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        ]
        self.MazeParedes = pygame.sprite.Group()
        self._crear_paredes()
        notification.notify(title='Maze created', message='X', app_name='OctoPussy', app_icon='./Resources/player.icns')

    def _crear_paredes(self):
        bx = 0
        by = 0
        for i in range(0, self.M * self.N):
            if self.maze[bx + (by * self.M)] == 1:
                rectSuelo = pygame.sprite.Sprite()
                rectSuelo.image = pygame.Surface([CASILLA_PIXEL, CASILLA_PIXEL])
                rectSuelo.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL, CASILLA_PIXEL, CASILLA_PIXEL)
                self.MazeParedes.add(rectSuelo)
                
            bx = bx + 1
            if bx > self.M - 1:
                bx = 0
                by = by + 1

    def addText(self, texto, x, y):
        self.font = pygame.font.SysFont('Arial', 25)
        self.font.render(texto, True, (255, 0, 0))

    def draw(self, display_surf, image_surf, w_surf):
        bx = 0
        by = 0

        xfont = pygame.font.SysFont('Corbel', 13)

        textWallDebug = pygame.sprite.Group()
        # rendering a text written in Corbel font.

        for i in range(0, self.M * self.N):
            if self.maze[bx + (by * self.M)] == 1:
                display_surf.blit(image_surf, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL))
                self.rect = image_surf.get_rect()
            else:
                display_surf.blit(w_surf, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL))
                rectSuelo = pygame.sprite.Sprite()
                rectSuelo.image = pygame.Surface([bx * CASILLA_PIXEL, by * CASILLA_PIXEL])
                rectSuelo.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL, 32, 32)
                # pygame.draw.rect(display_surf, ROJO, rectSuelo)
                # textWallMark = xfont.render(str(i), True, (0, 80, 0))
                # X = pygame.sprite
                # X = textWallMark
                # textWallDebug.add(X)

            if self.mazeDataExtra[bx + (by * self.M)] == 2:
                display_surf.blit(self.imageHuesos, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL))
                huesos = pygame.sprite.Sprite()
                huesos.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL, 32, 32)
                self.MazeExtra.add(huesos) 

            if self.mazeDataExtra[bx + (by * self.M)] == 3:
                display_surf.blit(self.imagePilaHuesos, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL))
                Pilahuesos = pygame.sprite.Sprite()
                Pilahuesos.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL, 32, 32)
                self.MazeExtra.add(Pilahuesos) 

            if self.mazeDataExtra[bx + (by * self.M)] == 4:
                display_surf.blit(self.imageFinNivel, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL))
                Bandera = pygame.sprite.Sprite()
                Bandera.rect = pygame.Rect(bx * CASILLA_PIXEL, by * CASILLA_PIXEL, 32, 32)
                self.MazeExtra.add(Bandera) 

            bx = bx + 1
            if bx > self.M - 1:
                bx = 0
                by = by + 1
        #return textWallDebug

    @staticmethod
    def calcularCasilla(valorX, valorY):
        casilla = (valorX / CASILLA_PIXEL) + ((valorY / CASILLA_PIXEL)*NUM_CASILLAS)
        casilla = int(casilla)
        logging.info("Valor calculado: %s", casilla)

        logging.debug("calcularCasilla:posición: X %s and Y %s ==> Casilla: %s", valorX, valorY, int(casilla))
        return casilla

    @staticmethod
    def calcularPixelPorCasilla(Casilla):
        posicion.x = (Casilla % 10) * CASILLA_PIXEL
        posicion.y = (Casilla / 10) * NUM_CASILLAS
        logging.debug("calcularPixelPorCasilla: Casilla %s a posición: X %s and Y %s", Casilla, posicion.x, posicion.y)

        return posicion

    @staticmethod
    def esAlcanzable(x, y):
        logging.info("Dentro Método alcanzable")

        if x > NUM_CASILLAS or y > NUM_CASILLAS:
            logging.info("esAlcanzble : X= %s and Y= %s", x, y)
            return False

        if Maze.calcularCasilla(x, y) == 1:
            return True
        else:
            return False

class App:
    windowWidth = SCREEN_WIDTH
    windowHeight = SCREEN_HEIGHT
    player = 0
    enemigo = 0
    JefeEnemigo = 0
    flagInit = True
    numEnemigos = 5
    enemigosArray = []
    PlayerGroup = pygame.sprite.Group()
    EnemigosGroup = pygame.sprite.Group() #Incluirá también al jefe Enemigo.
    paredesGroup = pygame.sprite.Group()
    visionEnemigos = bool
    pintaRectángulos = bool = True

    salir = bool = False

    # Inicio el reloj y el Sonido.
    clock = pygame.time.Clock()
    pygame.mixer.init()

    #Definimos el icono del juego.
    gameIcon = pygame.image.load("./Resources/player.png")
    pygame.display.set_icon(gameIcon)

    def __init__(self):
        self.pantalla = pygame.display.set_mode((self.windowWidth, self.windowHeight), pygame.HWSURFACE)
        self._running = True
        self.tocaMenu = True
        self.movimiento = False
        self.pause = False
        self._jugador = None
        self._enemigo = None
        self._JefeEnemigo = None
        self.floor_surf = None
        self.wall_surf = None
        self.player = player.Player()  # damos los valores por defecto.
        self.enemigo = player.Enemigo()
        self.JefeEnemigo = player.Enemigo()

        self.visionEnemigos = True
        self.salir = False

        # Llenar el vector de enemigos
        for i in range(0, self.numEnemigos):
            self.enemigo = player.Enemigo()
            self.enemigo.inicio(SCREEN_WIDTH, SCREEN_HEIGHT)
            self.enemigo.casilla = Maze.calcularCasilla(self.enemigo.x, self.enemigo.y)
            self.enemigosArray.append(self.enemigo)
            self.EnemigosGroup.add(self.enemigo)

        logging.info("Contenido grupo Sprites: %s", len(self.EnemigosGroup))
        logging.info("Cagados todos los enemigos")

        self.JefeEnemigo.inicio(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.JefeEnemigo.casilla = Maze.calcularCasilla(self.JefeEnemigo.x, self.JefeEnemigo.y)
        pos = posicion(0, 0)
        pos = Maze.calcularPixelPorCasilla(self.JefeEnemigo.casilla)
        self.JefeEnemigo.x = pos.x
        self.JefeEnemigo.y = pos.y
        logging.debug('POsición Jefe ENEMY --> x: %i e y: %i', self.JefeEnemigo.x, self.JefeEnemigo.y)
        # Cargamos Jefe enemigo
        
        self.maze = Maze()
        self.paredesGroup = self.maze.MazeParedes
        logging.info("Cargado el escenario")
        logging.info(f"Número de paredes creadas: {len(self.maze.MazeParedes)}")
        
        # Debug: imprimir algunas posiciones de paredes
        paredes_list = list(self.maze.MazeParedes)
        if paredes_list:
            logging.info(f"Primera pared en posición: {paredes_list[0].rect}")
            logging.info(f"Última pared en posición: {paredes_list[-1].rect}")

    def verInfoEnemigos(self):
        enemy = player.Enemigo()

        for i in range(1, self.numEnemigos):
            enemy = self.enemigosArray[i]
            enemy.logPosicionEnemigo()

    def menu(self):
        color = (255, 255, 255)

        print("Dentro del Menú!!")

        # Color for the buttons
        # light shade of the button
        color_light = (170, 170, 170)
        # dark shade of the button
        color_dark = (100, 100, 100)
        color_darkorange = (255, 140, 0)
        color_otherorange = (216,75, 32)
        color_darkgreen = (0, 64, 0)

        # stores the width of the
        # screen into a variable
        width = self.pantalla.get_width()

        # stores the height of the
        # screen into a variable
        height = self.pantalla.get_height()

        # defining a font
        smallfont = pygame.font.SysFont('Corbel', 35)
        Titlefont = pygame.font.SysFont('Impact', 150)

        # rendering a text written in Corbel font.
        textTitle = Titlefont.render('Octopussy', True, color_otherorange)
        text1 = smallfont.render('Nuevo Juego', True, color)
        text2 = smallfont.render('Opciones', True, color)
        text3 = smallfont.render('Cargar Partida', True, color)
        text4 = smallfont.render('Salir', True, color)

        while True:
            for ev in pygame.event.get():

                if ev.type == pygame.QUIT:
                    self.salir = True
                    pygame.quit()

                # Chequeamos click del ratón
                if ev.type == pygame.MOUSEBUTTONDOWN:

                    # Chequeamos si click en algún botón
                    # Botón 1 - Nuevo Juego
                    if mates.dentroBoton(mouse, int(width / 2), int((height / 2)) - 50, 230, 40):
                        self.tocaMenu = False
                        self.on_execute()

                    # Botón 4 - Cargar partida
                    #TO DO Programación botón cargar partida.

                    # Botón 3 - Opciones
                    if mates.dentroBoton(mouse, int(width / 2), int(height / 2), 230, 40):
                        print("Opciones del juego, pulsada.")
                        self.tocaMenu = False
                        self.menuOpciones()

                    # Botón 4 - Salir del juego
                    if mates.dentroBoton(mouse,  int(width / 2), int((height / 2)) + 190, 230, 40):
                        self.tocaMenu = False
                        self.salir = True
                        pygame.quit()

            if self.salir == False:
                # fills the screen with a color
                self.pantalla.fill((60, 25, 60))

                # stores the (x,y) coordinates into
                # the variable as a tuple
                mouse = pygame.mouse.get_pos()

                # Compruebo si el ratón está dentro de botón.
                # width / 2 <= mouse[0] <= width / 2 + 140 and height / 2 <= mouse[1] <= height / 2 + 40:
                if mates.dentroBoton(mouse, width / 2, (height / 2) - 60, 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [width / 2, (height / 2) - 60, 230, 40])
                # Botón 2 - Cargar partida
                elif mates.dentroBoton(mouse, width / 2, (height / 2)-10, 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int(height / 2) -10, 230, 40])
                # Botón 3 - Opciones
                elif mates.dentroBoton(mouse, width / 2, (height / 2)+50 , 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int(height / 2) +40, 230, 40])
                # Botón 4 - Salir del juego
                elif mates.dentroBoton(mouse, width / 2, (height / 2) +190, 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int((height / 2)) + 190, 230, 40])
                else:
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +190, 230, 40])

                # superimposing the text onto our button
                self.pantalla.blit(textTitle, ((width / 2) - 400, (height / 2) - 400))
                self.pantalla.blit(text1, ((width / 2) + 50, (height / 2) - 50))
                self.pantalla.blit(text2, ((width / 2) + 50, (height / 2)))
                self.pantalla.blit(text3, ((width / 2) + 50, (height / 2) + 50))
                self.pantalla.blit(text4, ((width / 2) + 50, (height / 2) + 200))

                # updates the frames of the game
                pygame.display.update()

    def menuOpciones(self):
        color = (255, 255, 255)

        print("Dentro de Opciones!!")

        # Color for the buttons
        # light shade of the button
        color_light = (170, 170, 170)
        # dark shade of the button
        color_dark = (100, 100, 100)
        color_darkorange = (255, 140, 0)
        color_otherorange = (216,75, 32)
        color_darkgreen = (0, 64, 0)

        # stores the width of the
        # screen into a variable
        width = self.pantalla.get_width()

        # stores the height of the
        # screen into a variable
        height = self.pantalla.get_height()

        # defining a font
        smallfont = pygame.font.SysFont('Corbel', 35)
        Titlefont = pygame.font.SysFont('Impact', 150)

        # rendering a text written in Corbel font.
        textTitle = Titlefont.render('Octopussy', True, color_otherorange)
        text1 = smallfont.render('Seleccionar Nivel', True, color)
        text2 = smallfont.render('Estadísticas', True, color)
        text3 = smallfont.render('Inventario Juego', True, color)
        text4 = smallfont.render('Volver', True, color)

        while True:
            for ev in pygame.event.get():

                if ev.type == pygame.QUIT:
                    self.salir = True
                    pygame.quit()

                # Chequeamos click del ratón
                if ev.type == pygame.MOUSEBUTTONDOWN:

                    # Chequeamos si click en algún botón
                    # Botón 1 - Seleccion Nivel
                    if mates.dentroBoton(mouse, int(width / 2), int((height / 2)) - 50, 230, 40):
                        logging.info("Pulsado Botón Selección de Nivel.")
                        self.tocaMenu = False
                        self.seleccionNivel()

                    # Botón 4 - Estadísticas Juego
                    if mates.dentroBoton(mouse, int(width / 2), int((height / 2)) + 100, 230, 40):
                        logging.info("Pulsado Botón : Estadísticas de Juego del Jugador.")
                        self.tocaMenu = False
                        self.seleccionNivel()

                    # Botón 3 - Inventario Juego
                    if mates.dentroBoton(mouse, int(width / 2), int(height / 2), 230, 40):
                        logging.info("Pulsado entrar al Inventario del Juego")
                        self.tocaMenu = False
                        self.inventarioJuego()

                    # Botón 4 - Volver al menú principal del Juego
                    if mates.dentroBoton(mouse,  int(width / 2), int((height / 2)) + 190, 230, 40):
                        logging.info("Pulsado Botón Voler al Menú Principal")
                        self.tocaMenu = False
                        self.menu()

            if self.salir == False:
                # fills the screen with a color
                self.pantalla.fill((60, 25, 60))

                # stores the (x,y) coordinates into
                # the variable as a tuple
                mouse = pygame.mouse.get_pos()

                # Compruebo si el ratón está dentro de botón.
                # width / 2 <= mouse[0] <= width / 2 + 140 and height / 2 <= mouse[1] <= height / 2 + 40:
                if mates.dentroBoton(mouse, width / 2, (height / 2) - 60, 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [width / 2, (height / 2) - 60, 230, 40])
                # Botón 2 - Cargar partida
                elif mates.dentroBoton(mouse, width / 2, (height / 2)-10, 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int(height / 2) -10, 230, 40])
                # Botón 3 - Opciones
                elif mates.dentroBoton(mouse, width / 2, (height / 2)+50 , 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int(height / 2) +40, 230, 40])
                # Botón 4 - Salir del juego
                elif mates.dentroBoton(mouse, width / 2, (height / 2) +190, 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int((height / 2)) + 190, 230, 40])
                else:
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +190, 230, 40])

                # superimposing the text onto our button
                self.pantalla.blit(textTitle, ((width / 2) - 400, (height / 2) - 400))
                self.pantalla.blit(text1, ((width / 2) + 50, (height / 2) - 50))
                self.pantalla.blit(text2, ((width / 2) + 50, (height / 2)))
                self.pantalla.blit(text3, ((width / 2) + 50, (height / 2) + 50))
                self.pantalla.blit(text4, ((width / 2) + 50, (height / 2) + 200))

                # updates the frames of the game
                pygame.display.update()

    def on_init(self):
        pygame.init()

        pygame.display.set_caption('Laberinto SquidCastle 2025, Aurora.')
        logging.info("Inicio del juego.")

        logging.info("Pintamos el menú del juego.")
        if self.tocaMenu:
            self.menu()

        logging.info("Asignar los Sprite Groups")
        

        logging.info("Empezamos un juego nuevo.")
        self._running = True
        self.player.pintarJugador()
        self._jugador = self.player.image
        self.rect = self._jugador.get_rect()  # rectángulo Sprite Player
        self.PlayerGroup.add(self.player)
        logging.info("Pintado Jugador")

        self.enemigo.pintarEnemigo()
        self._enemigo = self.enemigo.imageEnemigo
        self._JefeEnemigo = self.enemigo.imageJefeEnemigo
        print(len(self.enemigosArray))

        i = 0
        for i in range(0, self.numEnemigos):
            enemy = self.enemigosArray[i]
            self.EnemigosGroup.add(enemy)
            enemy.pintarEnemigo()
            self.rect = enemy.imageEnemigo.get_rect()  # rectángulo Sprite Player
            # Asignar grupo de paredes al enemigo para que pueda consultarlo
            enemy.MazeParedes = self.maze.MazeParedes

        logging.info('Plot Enemigo')

        logging.info('Pintar Jefe Enemigo')
        self.EnemigosGroup.add(self.JefeEnemigo)
        self.JefeEnemigo.pintarJefeEnemigo()
        self.rect = self.JefeEnemigo.imageJefeEnemigo.get_rect()  # rectángulo Sprite Jefe Enemigo
        self.JefeEnemigo.vision(self.JefeEnemigo.imageJefeEnemigo.get_rect().center)

        # Asignar grupo de paredes al Jefe Enemigo
        self.JefeEnemigo.MazeParedes = self.maze.MazeParedes

        self.floor_surf = pygame.image.load("./Resources/floor.png").convert()
        self.wall_surf = pygame.image.load("./Resources/Wall.png").convert()
        # self.wall_surf = pygame.image.load("./Resources/WallBricks.png").convert()

    def on_loop(self):
        self.JefeEnemigo.visionRotar()
        self.player.update()
        self.JefeEnemigo.update()

        i = 0
        for i in range(0, self.numEnemigos):
            self.enemigo = self.enemigosArray[i]
            self.enemigo.update()
            if self.enemigo.flagDisparo == True:
                self.enemigo.bala.update()

        if self.player.flagDisparo == True:
            self.player.bala.update()

        if self.JefeEnemigo.flagDisparo == True:
            self.JefeEnemigo.bala.update()

        # Colisiones entre enemigo y escenario.
        logging.info('VERIFICACIÓN COLISIONES.')
        
        # Debug: verificar posiciones
        logging.info(f"Player en posición: ({self.player.x}, {self.player.y}) - Rect: {self.player.rect}")
        
        # Colisión del jugador con paredes
        colision_player = pygame.sprite.spritecollide(self.player, self.maze.MazeParedes, False)
        if colision_player:
            logging.info('COLISION PLAYER DETECTADA')
            print('COLISION PLAYER DETECTADA')

        # Colisión de enemigos con paredes
        colision_enemigos = pygame.sprite.groupcollide(self.EnemigosGroup, self.maze.MazeParedes, False, False)
        if colision_enemigos:
            logging.info('COLISION Enemigo DETECTADA %s', len(colision_enemigos))
            print('COLISION Enemigo DETECTADA %s', len(colision_enemigos))
            # Opcional: procesar cada enemigo que colisionó
            for enemigo, paredes in colision_enemigos.items():
                logging.info(f'Enemigo en ({enemigo.x}, {enemigo.y}) colisionó con {len(paredes)} paredes')
                # Revertir y cambiar dirección solo del enemigo que colisiona
                if hasattr(enemigo, 'revertir_movimiento'):
                    enemigo.revertir_movimiento()
                if hasattr(enemigo, 'cambiar_direccion'):
                    enemigo.cambiar_direccion()
        
        # Colisión de Extras Escenario con Player
        colision_PlayerConExtra = pygame.sprite.spritecollide(self.player, self.maze.MazeExtra, True, )
        if colision_PlayerConExtra:
            logging.info('Huesos o Bandera Final IMPACTADA')
            print('Huesos o Bandera Final IMPACTADA')
            # Opcional: procesar cada enemigo que colisionó
            for jouer, extra in colision_PlayerConExtra.items():
                logging.info(f'Player en ({jouer.x}, {jouer.y}) colisionó con {len(extra)} paredes')

    def on_render(self):
        if self.pause == False:
            self.pantalla.fill((0, 0, 0))
            #Defino el laberinto
            logging.debug("Pintamos laberinto.")
            self.maze.draw(self.pantalla, self.floor_surf, self.wall_surf)

            # Aquí busco lugar suelo para Jugador
            # Llamada a la IA
            if self.flagInit == True:
                self.flagInit = False
                if self.maze.esAlcanzable(self.player.x, self.player.y):
                    self.pantalla.blit(self._jugador, (self.player.x, self.player.y))
                else:
                    self.player.x = random.randint(0, SCREEN_WIDTH)
                    self.player.y = random.randint(0, SCREEN_HEIGHT)
                    self.pantalla.blit(self._jugador, (self.player.x, self.player.y))
            else:
                self.pantalla.blit(self._jugador, (self.player.x, self.player.y))
            
            if self.pintaRectángulos == True:
                pygame.draw.rect(self.pantalla, (0, 255, 0), self.player.rect, 2)

            # Aquí busco lugar suelo para Enemigo y Jefe Enemigo.
            logging.debug("Pintamos los enemigos.")
            i = 0
            for i in range(0, self.numEnemigos):
                self.enemigo = self.enemigosArray[i]
                if(self.enemigo.isJefeEnemigo):
                    self.pantalla.blit(self._JefeEnemigo, (self.JefeEnemigo.x, self.JefeEnemigo.y))
                else:
                    self.pantalla.blit(self._enemigo, (self.enemigo.x, self.enemigo.y))
                    if self.pintaRectángulos == True:
                        pygame.draw.rect(self.pantalla, (255, 0, 0), self.enemigo.rect, 2)

                if (self.enemigo.flagDisparo == True):
                    self.pantalla.blit(self.enemigo.bala.image, (self.enemigo.bala.x, self.enemigo.bala.y))

            # Jefe Enemigo
            logging.debug('Pintamos el JEFE enemigo.')
            self.pantalla.blit(self.JefeEnemigo.imageJefeEnemigo, (self.JefeEnemigo.x, self.JefeEnemigo.y))
            if self.pintaRectángulos == True:
                pygame.draw.rect(self.pantalla, (0, 0, 255), self.JefeEnemigo.rect, 2)

            if (self.visionEnemigos == True):
                self.JefeEnemigo.vision(self.JefeEnemigo.imageJefeEnemigo.get_rect().center)
                self.pantalla.blit(self.JefeEnemigo.visionImage, (self.JefeEnemigo.x, self.JefeEnemigo.y - 40))

            # Pintar disparos del Player
            if(self.player.flagDisparo == True):
                logging.debug('DISPARO DeL Player.')
                self.pantalla.blit(self.player.bala.image, (self.player.bala.x, self.player.bala.y))
                self.player.balas.draw(self.pantalla)
                self.player.flagDisparo = False

            # Pintar disparos de Jefe Enemigo
            if (self.JefeEnemigo.flagDisparo == True):
                logging.debug('Pintamos Disparo DEL JEFE enemigo.')
                self.pantalla.blit(self.JefeEnemigo.bala.image, (self.JefeEnemigo.bala.x, self.JefeEnemigo.bala.y))
                
        fps = int(self.clock.get_fps())
        font = pygame.font.SysFont('Arial', 20)
        fps_text = font.render(f"FPS: {fps}", True, (255, 255, 0))  # Amarillo
        logging.debug("FPS de pintado : %i", fps)
        self.pantalla.blit(fps_text, (10, 10))

        pygame.display.flip() # Aquí es donde ploteamos todo.

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        self.clock.tick(60)

        print("Dentro de on_execute.")
        pygame.init()

        if self.on_init() == False:
            self._running = False

        milliseconds = self.clock.tick(FPS)  # milliseconds passed since last frame
        seconds = milliseconds / 1000.0  # seconds passed since last frame

        while (self._running):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False # pygame window closed by user
                    self.salir = True
                elif event.type == pygame.KEYDOWN:
                    self.player.speed = 1
                    if event.key == pygame.K_ESCAPE:
                        self._running = False  # user pressed ESC
                    if event.key == pygame.K_RIGHT:
                        self.movimiento = True
                        logging.info('¡¡¡ Pulsado flecha DERECHO !!!')
                        self.player.moveRight()
                    if event.key == pygame.K_LEFT:
                        self.movimiento = True
                        logging.info('¡¡¡ Pulsado flecha IZQUIERDO !!!')
                        self.player.moveLeft()
                    if event.key == pygame.K_UP:
                        self.movimiento = True
                        logging.info('¡¡¡ Pulsado flecha ARRIBA !!!')
                        self.player.moveUp()
                    if event.key == pygame.K_DOWN:
                        self.movimiento = True
                        logging.info('¡¡¡ Pulsado flecha ABAJO !!!')
                        self.player.moveDown()
                    if event.key == pygame.K_SPACE:
                        logging.info('¡¡¡ BARRA ESPACIADORA !!!')
                        logging.info('¡Disparo jugador!')
                        self.player.disparo()
                    if event.key == pygame.K_r:
                        print("Tecla R presionada")
                        if self.pintaRectángulos == True:
                           self.pintaRectángulos = False
                        else:
                            self.pintaRectángulos = True 
                    if event.key == pygame.K_v:
                        logging.info('Tecla V presionada')
                        if self.visionEnemigos == True:
                           self.visionEnemigos = False
                        else:
                            self.visionEnemigos = True
                    if event.key == pygame.K_p:
                        if self.Pause == False:
                            self.pause = True
                        else:
                            self.pause = False
                        logging.info('PAUSA PULSADA.')

                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_RIGHT:
                        self.movimiento = False
                        logging.info('¡¡¡ SOLtado cursor DERECHO !!!')
                        # print('¡¡¡ SOLtado cursor DERECHO !!!')
                        self.player.stop()

                    if event.key == pygame.K_LEFT:
                        self.movimiento = False
                        logging.info('¡¡¡ SOLtado cursor IZQUIERDO !!!')
                        # print('¡¡¡ SOLtado cursor IZQUIERDO !!!')
                        self.player.stop()

                    if event.key == pygame.K_UP:
                        self.movimiento = False
                        logging.info('¡¡¡ SOLtado cursor ARRIBA !!!')
                        # print('¡¡¡ SOLtado cursor ARRIBA !!!')
                        self.player.stop()

                    if event.key == pygame.K_DOWN:
                        self.movimiento = False
                        logging.info('¡¡¡ SOLtado cursor ABAJO !!!')
                        # print('¡¡¡ SOLtado cursor ABAJO !!!')
                        self.player.stop()

            self.on_loop()
            self.on_render()
            self.clock.tick(FPS)  # <--- Aquí, después de renderizar

        self.on_cleanup()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    logging.basicConfig(filename="./log/squidcastle.log", level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    logging.warning("Inicio LaberintoPy!!!")

    sqliteConnection = sqlite3.connect("./DB/tutorial.db")
    cursor = sqliteConnection.cursor()
    logging.info("Successfully Connected to SQLite")

    logging.info('Creación Base de Datos y Tablas principales.')
    #cursor.execute("""CREATE DATABASE OctoPussyDB""")
    try:
        # cursor.execute("""CREATE TABLE partida (id integer PRIMARY KEY, fecha Date, jugador text NOT NULL, puntuacion integer, nivel integer NOT NULL)""")
        # cursor.execute("""CREATE TABLE estadisticas (id interger PRIMARY KEY, jugador text NOT NULL, partida integer, disparos integer, nivelmax integer NOT NULL, enemigosmuertos integer, vidasusadas integer)""")
        # sqliteConnection.commit()
        logging.info('Ejecución SQL creación tablas.')
    except sqlite3.Error as error:
        logging.error("Failed to Tables in SQLite", error)
    finally:
        logging.info('Tablas DB creadas')

    logging.info('Fin acciones Base de Datos')


    # Parseo de fichero JSON
    logging.info('Start PARSEO JSON.')
    try:
        with open('./Levels/Level_2.json', 'r') as file:
            data = json.load(file)
        logging.info("JSON File data =", data)
    
    except FileNotFoundError:
        logging.error("Error: The file 'Level2.json' was not found.")

    except json.JSONDecodeError:
        logging.error("Error: Failed to decode JSON from the file.")


    notification.notify(title="Inicio", message="Inicio Juego", app_name="OctoPussy", app_icon="/assets/player.png")

    # App principal
    theApp = App()
    theApp.on_execute()

    #Cerramos base de datos
    sqliteConnection.close()
    logging.info("The SQLite connection is closed")

    logging.info("JUEGO ¡¡ Se acabo !!")
