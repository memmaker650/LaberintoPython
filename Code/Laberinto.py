import mates
import player
import infoPantalla

import logging
import statistics
import MazeLab
import Sonido
import random
import os
import sys
import math

import pygame
from pygame.locals import *
import sqlite3

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
    pintaVision = bool = True

    casillaObjetosTocados = set()

    # Valores Cabecera
    HeadGunAmmo = infoPantalla.infoArmasMunicion()
    HeadNivel = infoPantalla.infoNivel()
    HeadBarraDeVida = infoPantalla.barraDeVida()
    HeadReloj = infoPantalla.relojPantalla()
    HeadPuntuacion = infoPantalla.panelPuntuacion()
    HeadHuesos = infoPantalla.infoHuesos()
    # Tiempo / Iteracion
    tiempo_inicio = None
    iteracion = int = 0

    Sound = None
    canalmusicaFondo = None

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

        self.Sound = Sonido.Sonido()

        self.visionEnemigos = True
        self.tiempo_inicio = pygame.time.get_ticks()

        self.salir = False

        # Cargando el escenario
        self.maze = MazeLab.Maze()
        logging.info("Cargado el escenario")

        # Llenar el vector de enemigos
        for i in range(0, self.numEnemigos):
            self.enemigo = player.Enemigo()
            self.enemigo.inicio(SCREEN_WIDTH, SCREEN_HEIGHT)
            self.enemigo.casilla = MazeLab.Maze.calcularCasilla(self.enemigo.x, self.enemigo.y)
            resultado = self.maze.esAlcanzableCasilla(self.enemigo.casilla)
            pos = posicion(0, 0)
            pos = MazeLab.Maze.calcularPixelPorCasilla(self.enemigo.casilla)
            while not self.maze.esAlcanzableCasilla(self.enemigo.casilla):
                self.enemigo.inicio(SCREEN_WIDTH, SCREEN_HEIGHT)
                self.enemigo.casilla = MazeLab.Maze.calcularCasilla(self.enemigo.x, self.enemigo.y)
                pos = posicion(0, 0)
                pos = MazeLab.Maze.calcularPixelPorCasilla(self.enemigo.casilla)
                resultado = self.maze.esAlcanzableCasilla(self.enemigo.casilla)
            
            self.enemigo.x = pos.x
            self.enemigo.y = pos.y
            self.enemigosArray.append(self.enemigo)
            self.EnemigosGroup.add(self.enemigo)
        
        # Ubicar al jefe enemigo.
        self.JefeEnemigo.inicio(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.JefeEnemigo.casilla = MazeLab.Maze.calcularCasilla(self.JefeEnemigo.x, self.JefeEnemigo.y)
        pos = posicion(0, 0)
        pos = MazeLab.Maze.calcularPixelPorCasilla(self.JefeEnemigo.casilla)
        resultado = self.maze.esAlcanzableCasilla(self.JefeEnemigo.casilla)
        while not self.maze.esAlcanzableCasilla(self.JefeEnemigo.casilla):
            self.JefeEnemigo.inicio(SCREEN_WIDTH, SCREEN_HEIGHT)
            self.JefeEnemigo.casilla = MazeLab.Maze.calcularCasilla(self.JefeEnemigo.x, self.JefeEnemigo.y)
            pos = posicion(0, 0)
            pos = MazeLab.Maze.calcularPixelPorCasilla(self.JefeEnemigo.casilla)
            resultado = self.maze.esAlcanzableCasilla(self.JefeEnemigo.casilla)

        self.JefeEnemigo.x = pos.x
        self.JefeEnemigo.y = pos.y
        # Cargamos Jefe enemigo

    def verInfoEnemigos(self):
        enemy = player.Enemigo()

        for i in range(1, self.numEnemigos):
            enemy = self.enemigosArray[i]
            enemy.logPosicionEnemigo()

    def dibujar_cruz(self, surface, x:int, y:int, tamaño=10, color=(255, 165, 0), grosor=4):
        mitad = tamaño // 2
        pygame.draw.line(surface, color, (x - mitad, y), (x + mitad, y), grosor)
        pygame.draw.line(surface, color, (x, y - mitad), (x, y + mitad), grosor)

    def menu(self):
        color = (255, 255, 255)

        print("Dentro del Menú!!")

        # Color for the buttons
        # light shade of the button
        color_light = (170, 170, 170)
        # dark shade of the button
        color_dark = (100, 100, 100)
        color_darkorange = (255, 140, 0)
        color_darkgreen = (0, 64, 0)
        color_darkblue = (0, 47, 66)
        color_overblue = (80, 30, 255)
        color_otherorange = (216, 75, 32)
        color_rojobrillante = (255, 35, 1)
        

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

                if ev.type == pygame.QUIT | ev.type == pygame.K_ESCAPE:
                    self.salir = True
                    pygame.quit()

                # Chequeamos click del ratón
                if ev.type == pygame.MOUSEBUTTONDOWN:

                    # Chequeamos si click en algún botón
                    # Botón 1 - Nuevo Juego
                    if mates.dentroBoton(mouse, int(width / 2), int((height / 2)) - 60, 230, 40):
                        self.tocaMenu = False
                        self.on_execute()

                    # Botón 4 - Cargar partida
                    #TO DO Programación botón cargar partida.

                    # Botón 3 - Opciones
                    if mates.dentroBoton(mouse, int(width / 2), int(height / 2) + 40, 230, 40):
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
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +190, 230, 40])
                # Botón 2 - Cargar partida
                elif mates.dentroBoton(mouse, width / 2, (height / 2)-10, 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int(height / 2) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +190, 230, 40])
                # Botón 3 - Opciones
                elif mates.dentroBoton(mouse, width / 2, (height / 2)+50 , 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int(height / 2) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +190, 230, 40])
                # Botón 4 - Salir del juego
                elif mates.dentroBoton(mouse, width / 2, (height / 2) +190, 230, 40):
                    pygame.draw.rect(self.pantalla, color_rojobrillante, [int(width / 2), int((height / 2)) + 190, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
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
        color_darkblue = (0, 47, 66)
        color_overblue = (80, 30, 255)

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

                    if mates.dentroBoton(mouse,  int(width / 2), int((height / 2)) + 290, 230, 40):
                        logging.info("Pulsado Botón Voler al Menú Principal")
                        self.tocaMenu = False
                        self.menu()
                    
                    if mates.dentroBoton(mouse,  int(width / 2), int((height / 2)) + 400, 230, 40):
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
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_darkblue, [int(width / 2), int((height / 2)) +190, 230, 40])
                # Botón 2 - Cargar partida
                elif mates.dentroBoton(mouse, width / 2, (height / 2)-10, 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int(height / 2) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_darkblue, [int(width / 2), int((height / 2)) +190, 230, 40])
                # Botón 3 - Opciones
                elif mates.dentroBoton(mouse, width / 2, (height / 2)+50 , 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int(height / 2) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_darkblue, [int(width / 2), int((height / 2)) +190, 230, 40])
                # Botón 4 - Salir del juego
                elif mates.dentroBoton(mouse, width / 2, (height / 2) +190, 230, 40):
                    pygame.draw.rect(self.pantalla, color_overblue, [int(width / 2), int((height / 2)) + 190, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                else:
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_darkblue, [int(width / 2), int((height / 2)) +190, 230, 40])

                # superimposing the text onto our button
                self.pantalla.blit(textTitle, ((width / 2) - 400, (height / 2) - 400))
                self.pantalla.blit(text1, ((width / 2) + 50, (height / 2) - 50))
                self.pantalla.blit(text2, ((width / 2) + 50, (height / 2)))
                self.pantalla.blit(text3, ((width / 2) + 50, (height / 2) + 50))
                self.pantalla.blit(text4, ((width / 2) + 50, (height / 2) + 200))

                # updates the frames of the game
                pygame.display.update()
                
    def seleccionNivel (self):
        color = (255, 255, 255)

        print("Dentro de Selecciona Nivel!!")

        # Color for the buttons
        # light shade of the button
        color_light = (170, 170, 170)
        # dark shade of the button
        color_dark = (100, 100, 100)
        color_darkorange = (255, 140, 0)
        color_otherorange = (216,75, 32)
        color_darkgreen = (0, 64, 0)
        color_darkblue = (0, 47, 66)
        color_overblue = (80, 30, 255)
        

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
        text1 = smallfont.render('Nivel 1: x1', True, color)
        text2 = smallfont.render('Nivel 2: y2', True, color)
        text3 = smallfont.render('Nivel 3: z3', True, color)
        text4 = smallfont.render('Nivel 4: a4', True, color)
        text5 = smallfont.render('Nivel 5: B5', True, color)
        text6 = smallfont.render('Volver', True, color)

        while True:
            for ev in pygame.event.get():

                if ev.type == pygame.QUIT:
                    self.salir = True
                    pygame.quit()

                # Chequeamos click del ratón
                if ev.type == pygame.MOUSEBUTTONDOWN:

                    # Chequeamos si click en algún botón
                    # Botón 1 - Nivel 1
                    if mates.dentroBoton(mouse, int(width / 2), int((height / 2)) - 50, 230, 40):
                        logging.info("Pulsado Botón Selección de Nivel.")
                        self.tocaMenu = False
                        self.seleccionNivel()

                    # Botón 2 - Nivel 3
                    if mates.dentroBoton(mouse, int(width / 2), int(height / 2), 230, 40):
                        logging.info("Pulsado entrar al Inventario del Juego")
                        self.tocaMenu = False
                        self.inventarioJuego()

                    # Botón 3 - Nivel 2
                    if mates.dentroBoton(mouse, int(width / 2), int((height / 2)) + 50, 230, 40):
                        logging.info("Pulsado Botón : Estadísticas de Juego del Jugadr.")
                        self.tocaMenu = False
                        self.seleccionNivel()

                    # Botón 4 - Nivel 4
                    if mates.dentroBoton(mouse,  int(width / 2), int((height / 2)) + 100, 230, 40):
                        logging.info("Pulsado Botón Voler al Menú Principal")
                        self.tocaMenu = False
                        self.menu()

                    # Botón 5 - Nivel 5
                    if mates.dentroBoton(mouse,  int(width / 2), int((height / 2)) + 150, 230, 40):
                        logging.info("Pulsado Botón Voler al Menú Principal")
                        self.tocaMenu = False
                        self.menu()
                    
                    # Botón 5 - Volver al menú principal del Juego
                    if mates.dentroBoton(mouse,  int(width / 2), int((height / 2)) + 210, 230, 40):
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
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +90, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +140, 230, 40])
                    pygame.draw.rect(self.pantalla, color_darkblue, [int(width / 2), int((height / 2)) +200, 230, 40])
                # Botón 2 - Cargar partida
                elif mates.dentroBoton(mouse, width / 2, (height / 2)-10, 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int(height / 2) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +90, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +140, 230, 40])
                    pygame.draw.rect(self.pantalla, color_darkblue, [int(width / 2), int((height / 2)) +200, 230, 40])
                # Botón 3 - Opciones
                elif mates.dentroBoton(mouse, width / 2, (height / 2)+50 , 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int(height / 2) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +90, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +140, 230, 40])
                    pygame.draw.rect(self.pantalla, color_darkblue, [int(width / 2), int((height / 2)) +200, 230, 40])
                # Botón 4 - Nivel 
                elif mates.dentroBoton(mouse, width / 2, (height / 2) +100, 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int((height / 2)) + 90, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +140, 230, 40])
                    pygame.draw.rect(self.pantalla, color_darkblue, [int(width / 2), int((height / 2)) +200, 230, 40])
                # Botón 5 - Nivel
                elif mates.dentroBoton(mouse, width / 2, (height / 2) +150, 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int((height / 2)) + 140, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +90, 230, 40])
                    pygame.draw.rect(self.pantalla, color_darkblue, [int(width / 2), int((height / 2)) +200, 230, 40])
                # Botón Volver
                elif mates.dentroBoton(mouse, width / 2, (height / 2) +210, 230, 40):
                    pygame.draw.rect(self.pantalla, color_overblue, [int(width / 2), int((height / 2)) + 200, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +90, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +140, 230, 40])
                else:
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +90, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +140, 230, 40])
                    pygame.draw.rect(self.pantalla, color_darkblue, [int(width / 2), int((height / 2)) +200, 230, 40])

                # superimposing the text onto our button
                self.pantalla.blit(textTitle, ((width / 2) - 400, (height / 2) - 400))
                self.pantalla.blit(text1, ((width / 2) + 50, (height / 2) - 50))
                self.pantalla.blit(text2, ((width / 2) + 50, (height / 2)))
                self.pantalla.blit(text3, ((width / 2) + 50, (height / 2) + 50))
                self.pantalla.blit(text4, ((width / 2) + 50, (height / 2) + 100))
                self.pantalla.blit(text5, ((width / 2) + 50, (height / 2) + 150))
                self.pantalla.blit(text6, ((width / 2) + 50, (height / 2) + 210))

                # updates the frames of the game
                pygame.display.update()

    def on_init(self):
        pygame.init()

        pygame.display.set_caption('Laberinto SquidCastle 2025, Aurora.')
        logging.info("Inicio del juego.")

        logging.info("Pintamos el menú del juego.")
        if self.tocaMenu:
            self.menu()
        
        self.Sound.musica = pygame.mixer.Sound("./Resources/Sonidos/sobrecarga-cibernetica.mp3")

        logging.info("Empezamos un juego nuevo.")
        self._running = True
        self.player.pintarJugador()
        self._jugador = self.player.image
        self.rect = self._jugador.get_rect()  # rectángulo Sprite Player
        self.PlayerGroup.add(self.player)
        logging.info("Pintado Jugador")

        self._enemigo = self.enemigo.imageEnemigo
        self._JefeEnemigo = self.enemigo.imageJefeEnemigo
        print(len(self.enemigosArray))

        i = 0
        for i in range(0, self.numEnemigos):
            enemy = self.enemigosArray[i]
            self.EnemigosGroup.add(enemy)
            self.rect = enemy.imageEnemigo.get_rect()  # rectángulo Sprite Player
            # Asignar grupo de paredes al enemigo para que pueda consultarlo
            enemy.MazeInfo = self.maze.MazeLaberinto

        logging.info('Plot Enemigo')

        logging.info('Pintar Jefe Enemigo')
        self.EnemigosGroup.add(self.JefeEnemigo)
        self.rect = self.JefeEnemigo.imageJefeEnemigo.get_rect()  # rectángulo Sprite Jefe Enemigo

        # Asignar grupo de paredes al Jefe Enemigo
        self.JefeEnemigo.MazeInfo = self.maze.MazeLaberinto
        self.JefeEnemigo.kia.Laberinto = self.JefeEnemigo.MazeInfo

        self.floor_surf = pygame.image.load("./Resources/floor.png").convert()
        self.wall_surf = pygame.image.load("./Resources/Wall.png").convert()
        # self.wall_surf = pygame.image.load("./Resources/WallBricks.png").convert()

    def on_loop(self):
        self.player.update()

        self.JefeEnemigo.updateJefe()
        ksilla = self.maze.calcularCasilla(self.enemigo.x, self.enemigo.y)
        self.enemigo.cargarCasillaRecorrido(ksilla)

        i = 0
        for i in range(0, self.numEnemigos):
            self.enemigo = self.enemigosArray[i]
            ksilla = self.maze.calcularCasilla(self.enemigo.x, self.enemigo.y)
            self.enemigo.cargarCasillaRecorrido(ksilla)
            self.enemigo.update()
            # if self.enemigo.flagDisparo == True:
                # self.enemigo.balas.update()

        if self.player.flagDisparo == True:
            self.player.balas.update()

        if self.JefeEnemigo.flagDisparo == True:
            self.JefeEnemigo.balas.update()

        # Colisiones entre enemigo y escenario.
        logging.info('VERIFICACIÓN COLISIONES.')
        
        # Debug: verificar posiciones
        logging.info(f"Player en posición: ({self.player.x}, {self.player.y}) - Rect: {self.player.rect}")
        
        # Colisión del jugador con paredes
        colision_player = pygame.sprite.spritecollide(self.player, self.maze.MazeParedes, False)
        if colision_player:
            logging.info(f'COLISION PLAYER DETECTADA - num ELem ({len(colision_player)})')
            # print(f'COLISION PLAYER DETECTADA - num ELem ({len(colision_player)})')

            self.player.x = self.player.prev_x
            self.player.y = self.player.prev_y

            for cl in colision_player:
                logging.info(f'PLAYER colisionó con paRED')

        # Colisión de enemigos con paredes
        colision_enemigos = pygame.sprite.groupcollide(self.EnemigosGroup, self.maze.MazeParedes, False, False)
        if colision_enemigos:
            logging.info('COLISION Enemigo DETECTADA %s', len(colision_enemigos))
            # Opcional: procesar cada enemigo que colisionó
            for enemigo, paredes in colision_enemigos.items():
                logging.info(f'Enemigo en ({enemigo.x}, {enemigo.y}) colisionó con {len(paredes)} paredes')
                # Revertir y cambiar dirección solo del enemigo que colisiona
                if hasattr(enemigo, 'revertir_movimiento'):
                    enemigo.revertir_movimiento()
                if hasattr(enemigo, 'cambiar_direccion'):
                    enemigo.cambiar_direccion()
        
        # Colisión de Extras Escenario con Player
        colision_PlayerConExtra = pygame.sprite.spritecollide(self.player, self.maze.MazeExtra, False)
        if colision_PlayerConExtra:
            logging.info('Huesos  IMPACTADA')
            # print('Huesos  IMPACTADA')
            # Opcional: procesar cada enemigo que colisionó
            for cpcE in colision_PlayerConExtra:
                logging.info(f'Huesos tocados')

        # Colisión Player con llave puerta
        colision_PlayerConLlavePuerta = pygame.sprite.spritecollide(self.player, self.maze.MazeLlavePuerta, True)
        if colision_PlayerConLlavePuerta:
            logging.info('Llave PUERTA cogida')
            print('Llave PUERTA cogida')
            self.player.llavePuerta = True
            self.maze.MazeLlavePuerta.empty()
            self.maze.flagLlavePuerta = False
            # Opcional: procesar cada enemigo que colisionó
            for cpcE in colision_PlayerConLlavePuerta:
                logging.info(f'Llave PUERTA tocados')

        # Colisión Player con Champi
        colision_PlayerConChampi = pygame.sprite.spritecollide(self.player, self.maze.MazeChampi, True)
        if colision_PlayerConChampi:
            logging.info('Champi cogidO')
            print('Champi cogida')
            self.player.champi = True
            self.maze.MazeChampi.empty()
            self.maze.flagChampi = False
            # Opcional: procesar cada enemigo que colisionó
            for cpcE in colision_PlayerConChampi:
                logging.info(f'Champi tocadO')
        
        # Colisión Player con Granada
        colision_PlayerConGranada = pygame.sprite.spritecollide(self.player, self.maze.MazeGranada, True)
        if colision_PlayerConGranada:
            logging.info('Granada cogidA')
            print('Granada cocogidAgida')
            self.player.granada = True
            self.maze.MazeGranada.empty()
            self.maze.flagGranada = False
            # Opcional: procesar cada enemigo que colisionó
            for cpcE in colision_PlayerConGranada:
                logging.info(f'Granada tocadA')

        # Colisión de Player con Llave fin de pantalla.
        colision_PlayerConLlaveFinal = pygame.sprite.spritecollide(self.player, self.maze.MazeLlave, True)
        if colision_PlayerConLlaveFinal:
            logging.info('Llave FINAL IMPACTADA')
            print('Llave FINAL cogida')
            self.player.llaveFinNivel = True
            self.maze.MazeLlave.empty()
            self.maze.flagLlave = False
            # Opcional: procesar cada enemigo que colisionó
            for cpcE in colision_PlayerConLlaveFinal:
                logging.info(f'Llave PUERTA tocados')
        
        # Colisión de Player con Hueso.
        colision_PlayerConHueso = pygame.sprite.spritecollide(self.player, self.maze.MazeHueso, True)
        if colision_PlayerConHueso:
            logging.info('Hueso simple IMPACTADO')
            print('HuesO o BONE: ', len(colision_PlayerConHueso))
            self.HeadPuntuacion.puntos += 10
            self.HeadHuesos.NumeroHuesos += 1
            # Opcional: procesar cada enemigo que colisionó
            for cpcE in colision_PlayerConHueso:
                logging.info(f'Hueso Sólo tocado')
                self.casillaObjetosTocados.add(self.maze.calcularCasilla(cpcE.rect.x, cpcE.rect.y))
                cpcE.kill()

        # Colisión de Player con Oro.
        colision_PlayerConOro = pygame.sprite.spritecollide(self.player, self.maze.MazeOro, True)
        if colision_PlayerConOro:
            logging.info('Oro IMPACTADO')
            print('Oro cogida')
            self.HeadPuntuacion.puntos += 100
            for cpcE in colision_PlayerConOro:
                logging.info(f'Oro tocado')
                self.casillaObjetosTocados.add(self.maze.calcularCasilla(cpcE.rect.x, cpcE.rect.y))
                cpcE.kill()

            # self.maze.flagHuesos = False
            # Opcional: procesar cada enemigo que colisionó
            for cpcE in colision_PlayerConOro:
                logging.info(f'Oro tocado')
        
        # Colisión de Player con Pila de Huesos.
        colision_PlayerConPilaHueso = pygame.sprite.spritecollide(self.player, self.maze.MazePilaHuesos, True)
        if colision_PlayerConPilaHueso:
            logging.info('Pila de Huesos IMPACTADA')
            print('Pila de Huesos cogida')
            self.maze.MazePilaHuesos.empty()
            self.maze.flagPilaHuesos = False
            self.HeadPuntuacion.puntos += 50
            self.HeadHuesos.NumeroHuesos += 10
            # Opcional: procesar cada enemigo que colisionó
            for cpcE in colision_PlayerConPilaHueso:
                logging.info(f'Pila de Huesos  tocado')
        
        # Colisión de Player con Botiquin.
        colision_PlayerConBotiquin = pygame.sprite.spritecollide(self.player, self.maze.MazeBotiquin, True)
        if colision_PlayerConBotiquin:
            logging.info('Botiquin IMPACTADo')
            print('Botiquin cogida')
            self.maze.MazeBotiquin.empty()
            self.maze.flagBotiquin = False
            self.HeadBarraDeVida.vida += 30
            # Opcional: procesar cada enemigo que colisionó
            for cpcE in colision_PlayerConBotiquin:
                logging.info(f'Botiquin tocado')

        # Colisión de Bandera FIN Pantalla del Escenario con Player
        colision_PlayerConBandera = pygame.sprite.spritecollide(self.player, self.maze.MazeBandera, False)
        if colision_PlayerConBandera:
            logging.info('Bandera Final IMPACTADA')
            print('Bandera Final IMPACTADA')
            # Opcional: procesar cada enemigo que colisionó
            for cpcE in colision_PlayerConBandera:
                logging.info('Bandera tocada')

    def on_render(self):
        if self.pause == False:
            self.pantalla.fill((0, 0, 0))
            #Defino el laberinto
            logging.debug("Pintamos laberinto.")
            self.maze.draw(self.pantalla, self.floor_surf, self.wall_surf, self.casillaObjetosTocados)

            if self.iteracion == 35:
                self.iteracion = 0

            # Aquí busco lugar suelo para Jugador
            # Llamada a la IA
            if self.flagInit == True:
                self.flagInit = False
                print("Casilla Inicial Jugador: ", self.maze.posicionInitJugador)
                self.player.casilla = self.maze.posicionInitJugador    
                pos = MazeLab.Maze.calcularPixelPorCasilla(self.player.casilla)
                self.player.x = pos.x
                self.player.y = pos.y
                self.pantalla.blit(self._jugador, (self.player.x, self.player.y))
            else:
                self.pantalla.blit(self._jugador, (self.player.x, self.player.y))
            
            if self.pintaRectángulos == True:
                pygame.draw.rect(self.pantalla, (0, 255, 0), self.player.rect, 2)

            # self.dibujar_cruz(self.pantalla, 202, 702, 20)

            smallfont = pygame.font.SysFont('Corbel', 35)
            
            """
            position = self.maze.calcularPixelPorCasilla(665)
            if self.maze.esAlcanzable(position.x, position.y):
                text1 = smallfont.render('X', True, (255, 165, 0))
            else:
                text1 = smallfont.render('X', True, (255, 255, 255))
            self.pantalla.blit(text1, (position.x, position.y))

             
            position = self.maze.calcularPixelPorCasilla(36)
            if self.maze.esAlcanzable(position.x, position.y):
                text1 = smallfont.render('36', True, (255, 165, 0))
            else:
                text1 = smallfont.render('36', True, (255, 255, 255))
            self.pantalla.blit(text1, (position.x, position.y))

            position = self.maze.calcularPixelPorCasilla(41)
            if self.maze.esAlcanzable(position.x, position.y):
                text1 = smallfont.render('41', True, (255, 165, 0))
            else:
                text1 = smallfont.render('41', True, (255, 255, 255))
            self.pantalla.blit(text1, (position.x, position.y))

            position = self.maze.calcularPixelPorCasilla(134)
            if self.maze.esAlcanzableCasilla(134):
                text1 = smallfont.render('134', True, (255, 165, 0))
            else:
                text1 = smallfont.render('134', True, (255, 255, 255))
            self.pantalla.blit(text1, (position.x, position.y))

            position = self.maze.calcularPixelPorCasilla(24)
            if self.maze.esAlcanzableCasilla(24):
                text1 = smallfont.render('24', True, (255, 165, 0))
            else:
                text1 = smallfont.render('24', True, (255, 255, 255))
            self.pantalla.blit(text1, (position.x, position.y)) """

            # Aquí busco lugar suelo para Enemigo y Jefe Enemigo.
            logging.debug("Pintamos los enemigos.")
            i = 0
            for i in range(0, self.numEnemigos):
                self.enemigo = self.enemigosArray[i]
                if(self.enemigo.isJefeEnemigo):
                    print('---Posición DRAW LORD: ',self.JefeEnemigo.x, self.JefeEnemigo.y)
                    self.pantalla.blit(self._JefeEnemigo, (self.JefeEnemigo.x, self.JefeEnemigo.y))
                else:
                    # print('---Posición DRAW ENEMIGO: ',i, self.enemigo.x, self.enemigo.y)
                    self.pantalla.blit(self._enemigo, (self.enemigo.x, self.enemigo.y))
                    if self.pintaRectángulos == True:
                        pygame.draw.rect(self.pantalla, (255, 0, 0), self.enemigo.rect, 2)

            # for nemesis in self.EnemigosGroup:
                # nemesis.balas.draw(self.pantalla)

            # Jefe Enemigo + VISIÓN
            logging.debug('Pintamos el JEFE enemigo.')
            self.pantalla.blit(self.JefeEnemigo.imageJefeEnemigo, (self.JefeEnemigo.x, self.JefeEnemigo.y))
            if self.pintaRectángulos == True:
                pygame.draw.rect(self.pantalla, (0, 0, 255), self.JefeEnemigo.rect, 2)
            # VISION
            if (self.visionEnemigos == True):
                self.JefeEnemigo.visionRotar()
                self.JefeEnemigo.vision(self.JefeEnemigo.imageJefeEnemigo.get_rect().center)
                centro = (self.JefeEnemigo.x+10, self.JefeEnemigo.y+10)
                radio = 20
                x = centro[0] + radio * math.cos(math.radians(self.JefeEnemigo.angle))
                y = centro[1] + radio * math.sin(math.radians(self.JefeEnemigo.angle))
                # Calculamos el ángulo de rotación: la cruz debe mirar hacia afuera
                # → sumamos 90° para que apunte al exterior en lugar de al centro
                rot_angle = -self.JefeEnemigo.angle + 90
                # Rotamos la imagen
                rotated = pygame.transform.rotate(self.JefeEnemigo.visionImage, rot_angle)
                rect = rotated.get_rect(center=(x, y))
                # Dibujamos la cruz rotada en su posición orbital
                self.pantalla.blit(rotated, rect)

            if(self.JefeEnemigo.alarma):
                # --- Control del tiempo del bocadillo ---
                current_time = pygame.time.get_ticks()
                elapsed = current_time - self.JefeEnemigo.bubble_start_time
                if elapsed < self.JefeEnemigo.bubble_duration:
                    # Calculamos opacidad
                    if elapsed > self.JefeEnemigo.bubble_duration - self.JefeEnemigo.fade_duration:
                        # Fase de desvanecimiento (alpha entre 255 → 0)
                        alphaBTexto = int(255 * (1 - (elapsed - (self.JefeEnemigo.bubble_duration - self.JefeEnemigo.fade_duration)) / self.JefeEnemigo.fade_duration))
                    else:
                        alphaBTexto = 255

                    self.JefeEnemigo.bocadilloTexto(self.pantalla, "¡ ALARMA !", (int(self.JefeEnemigo.x), int(self.JefeEnemigo.y) - 10), alpha=alphaBTexto)
                else:
                    self.JefeEnemigo.alarma = False
                    self.JefeEnemigo.restarRelojBocadilloTexto()
    
            # Maze Extra --> Recuadros
            if self.pintaRectángulos == True:
                for extra in self.maze.MazeExtra:
                    pygame.draw.rect(self.pantalla, (255, 0, 255), extra.rect, 2)

            # Pintar disparos del Player
            if self.player.flagDisparo == True:
                logging.debug('DISPARO DeL Player.')
                self.player.balas.draw(self.pantalla)

            # Pintar disparos de Jefe Enemigo
            if self.JefeEnemigo.flagDisparo == True:
                logging.debug('Pintamos Disparo DEL JEFE enemigo.')
                self.JefeEnemigo.balas.draw(self.pantalla)

        self.iteracion += 1

        self.HeadGunAmmo.armaSeleccionada = 2
        self.HeadGunAmmo.municionArmaSeleccionada = self.player.municion
        self.HeadGunAmmo.update()

        # Actualizo valores del HUB.
        self.HeadBarraDeVida.crearBarraDeVida()
        self.HeadBarraDeVida.conversionTexto()
        self.HeadNivel.conversionTexto()
        self.HeadReloj.conversionTexto()
        self.HeadPuntuacion.conversionTexto()
        self.HeadGunAmmo.conversionTexto()
        self.HeadHuesos.conversionTexto()

        # Pinto los valores del HUB o cabecera de valores.
        logging.debug("Pintando la Cabecera de Valores")

        # Objetos adquiridos (Llaves & Armas)
        if self.player.llavePuerta:
            imagenPanel1 = pygame.image.load("./Resources/llave_puerta.png")
            imagen_escalada = pygame.transform.scale(imagenPanel1, (7, 21))
            self.pantalla.blit(imagen_escalada, (620, 110))

        if self.player.llaveFinNivel:
            imagenPanel2 = pygame.image.load("./Resources/llave.png")
            imagen_escalada = pygame.transform.scale(imagenPanel2, (20, 20))
            self.pantalla.blit(imagen_escalada, (660, 110))
        
        if self.player.pistola:
            imagenPanel3 = pygame.image.load("./Resources/pistola.png")
            imagen_escalada = pygame.transform.scale(imagenPanel3, (25, 25))
            self.pantalla.blit(imagen_escalada, (700, 110))

        if self.player.granada:
            imagenPanel4 = pygame.image.load("./Resources/granada-de-mano.png")
            imagen_escalada = pygame.transform.scale(imagenPanel4, (20, 20))
            self.pantalla.blit(imagen_escalada, (740, 110))
        
        if self.player.laser:
            imagenPanel5 = pygame.image.load("./Resources/pistola-laser.png")
            imagen_escalada = pygame.transform.scale(imagenPanel5, (20, 20))
            self.pantalla.blit(imagen_escalada, (780, 110))

        # Puntuación
        font = pygame.font.SysFont('Arial', 32)
        puntos_text = font.render(f"Puntos: {self.HeadPuntuacion.textoPuntos}", True, (255, 255, 0))  # Amarillo
        self.pantalla.blit(puntos_text, (600, 10))

        # Arma y Munición
        font = pygame.font.SysFont('Arial', 32)
        puntos_text = font.render(f"Arma: ", True, (100, 100, 100))  # Azul
        self.pantalla.blit(puntos_text, (600, 40))
        puntos_text = font.render(f"{self.HeadGunAmmo.textoArma}", True, (255, 255, 255))  # Azul
        self.pantalla.blit(puntos_text, (720, 40))
        puntos_text = font.render(f"Munición: ", True, (100, 100, 100))  # Azul
        self.pantalla.blit(puntos_text, (600, 70))
        puntos_text = font.render(f"{self.HeadGunAmmo.textoMunicion}", True, (255, 255, 255))  # Azul
        self.pantalla.blit(puntos_text, (750, 70))

        # Reloj
        # Calculos
        tiempo_actual = pygame.time.get_ticks()
        segundos_transcurridos = (tiempo_actual - self.tiempo_inicio) // 1000
        tiempo_restante = max(0, self.HeadReloj.maxTiempo - segundos_transcurridos)
        self.HeadReloj.tiempoInteger = int(tiempo_restante)

        # Si llega a cero, puedes hacer algo (ej. fin del juego)
        if self.HeadReloj.tiempoInteger == 0:
            # Aquí podrías mostrar mensaje "¡Tiempo agotado!"
            pass
        imagenPanel3 = pygame.image.load("./Resources/clock.png")
        imagen_escalada = pygame.transform.scale(imagenPanel3, (40, 40))
        self.pantalla.blit(imagen_escalada, (360, 10))
        font = pygame.font.SysFont('Arial', 40)
        puntos_text = font.render(f"{self.HeadReloj.textoReloj}", True, (255, 255, 255))  # Blanco
        self.pantalla.blit(puntos_text, (420, 10))

        # Nivel
        font = pygame.font.SysFont('Arial', 40)
        puntos_text = font.render(f"Level: ", True, (100, 100, 100))  # Azúl
        self.pantalla.blit(puntos_text, (360, 50))
        puntos_text = font.render(f"{self.HeadNivel.textoNivel}", True, (0, 0, 255))  # Azúl
        self.pantalla.blit(puntos_text, (480, 50))

        # Huesos
        font = pygame.font.SysFont('Arial', 32)
        puntos_text = font.render(f"Huesos:", True, (100, 100, 100))  # Azúl
        self.pantalla.blit(puntos_text, (360, 90))
        puntos_text = font.render(f"{self.HeadHuesos.textoHuesos}", True, (255, 255, 255))  # Azúl
        self.pantalla.blit(puntos_text, (485, 90))

        # Nombre Jugador
        font = pygame.font.SysFont('Arial', 32)
        puntos_text = font.render(f"Memmaker650", True, (100, 100, 100))  # Azúl
        self.pantalla.blit(puntos_text, (10, 10))

        # Barra de Vida
        self.pantalla.blit(self.HeadBarraDeVida.spriteBarraDeVida, (10, 50))
        # Barra de Vida (Porcentaje)
        font = pygame.font.SysFont('Arial', 27)
        puntos_text = font.render(f"{self.HeadBarraDeVida.textoVida}", True, (255, 255, 255))  # Blanco
        self.pantalla.blit(puntos_text, (85, 60))

        #FPS
        fps = int(self.clock.get_fps())
        font = pygame.font.SysFont('Arial', 20)
        fps_text = font.render(f"FPS: {fps}", True, (255, 255, 0))  # Amarillo
        logging.debug("FPS de pintado : %i", fps)
        self.pantalla.blit(fps_text, (10, 110))

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
                    if event.key == pygame.K_RETURN:
                        logging.info('¡¡¡ INTRO !!!')
                        self.JefeEnemigo.alarma = True
                        for x in self.EnemigosGroup:
                            x.flagDisparo == True
                            x.disparo()
                    if event.key == pygame.K_c:
                        print("Tecla C presionada")
                        if self.pintaRectángulos == True:
                           self.pintaRectángulos = False
                        else:
                            self.pintaRectángulos = True 
                    if event.key == pygame.K_k:
                        logging.info('Tecla K presionada')
                    if event.key == pygame.K_v:
                        logging.info('Tecla V presionada')
                        if self.pintaVision == True:
                           self.pintaVision = False
                        else:
                            self.pintaVision = True 
                    if event.key == pygame.K_s:
                        logging.info('Tecla S apretada')
                        if self.Sound.reproducirMusica == False:
                           self.canalmusicaFondo = self.Sound.musica.play()  # 🔊 Reproduce el sonido una vez
                           # musicaFondo.play(loops=-1)  # Si quieres que se repita indefinidamente
                           self.Sound.musica.set_volume(0.7)
                           self.Sound.reproducirMusica = True
                        else:
                            self.reproducirMusica = False
                            self.canalmusicaFondo.stop()
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

            if self.movimiento == True:
                if(self.player.orientacion == 1):
                    self.player.moveLeft()
                elif(self.player.orientacion == 2):
                    self.player.moveUp()
                elif(self.player.orientacion == 3):
                    self.player.moveRight()
                elif(self.player.orientacion == 4):
                    self.player.moveDown()
                else:
                    logging.info('¡¡¡ What !!!')
                    print('¡¡¡ What !!!')

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

    try:
        parser = LevelParser("./Levels")
        level_data = parser.load_by_name("Level_2.json")
        logging.info("Level loaded: %s (%dx%d)", os.path.basename(level_data.path), level_data.width, level_data.height)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logging.error("Error cargando nivel JSON: %s", e)
        level_data = None

    notification.notify(title="Inicio", message="Inicio Juego", app_name="OctoPussy", app_icon="/assets/player.png")

    # App principal
    theApp = App()
    theApp.on_execute()

    #Cerramos base de datos
    sqliteConnection.close()
    logging.info("The SQLite connection is closed")

    logging.info("JUEGO ¡¡ Se acabo !!")
