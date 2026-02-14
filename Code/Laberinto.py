from typing import Any
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
COLOR_PUERTA = (160, 110, 60)
COLOR_BORDE = (90, 60, 40)

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

    flagPrint_info = False

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

    # Valores de la puerta
    door_length = 32
    door_thickness = 10
    door_x = int
    door_y = int
    pivot_x = door_x
    pivot_y = door_y
    door_angle = 0           # 0 = cerrada, 90 = abierta
    openingDoor = bool = False
    closingDoor = bool = False
    Doorspeed = int = 3                # grados por frame
    door_surface = pygame.Surface((32, 32))  # ✅ CORRECTO

    # Gestión del Sonido.
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
        self.JefeEnemigo.isJefeEnemigo = True

        self.Sound = Sonido.Sonido()

        self.visionEnemigos = True
        self.tiempo_inicio = pygame.time.get_ticks()

        self.salir = False

        self.ia_update_interval = 500  # milisegundos (500ms = 0.5 segundos, o 1000ms = 1 segundo)
        self.ultimo_update_ia = pygame.time.get_ticks()
        self.ia_necesita_update = True  

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

        # Cargamos Jefe enemigo
        self.JefeEnemigo.x = pos.x
        self.JefeEnemigo.y = pos.y
        
        pygame.init()
        
        # PRECARGAR RECURSOS PARA EL HUD (UNA SOLA VEZ)
        # Imágenes del HUD
        self.imagen_llave_puerta = pygame.image.load("./Resources/llave_puerta.png")
        self.imagen_llave_puerta = pygame.transform.scale(self.imagen_llave_puerta, (7, 21))

        self.imagen_llave = pygame.image.load("./Resources/llave.png")
        self.imagen_llave = pygame.transform.scale(self.imagen_llave, (20, 20))

        self.imagen_pistola = pygame.image.load("./Resources/pistola.png")
        self.imagen_pistola = pygame.transform.scale(self.imagen_pistola, (25, 25))

        self.imagen_granada = pygame.image.load("./Resources/granada-de-mano.png")
        self.imagen_granada = pygame.transform.scale(self.imagen_granada, (20, 20))

        self.imagen_laser = pygame.image.load("./Resources/pistola-laser.png")
        self.imagen_laser = pygame.transform.scale(self.imagen_laser, (20, 20))

        self.imagen_clock = pygame.image.load("./Resources/clock.png")
        self.imagen_clock = pygame.transform.scale(self.imagen_clock, (40, 40))

        # Fuentes del HUD (crearlas una vez)
        self.font_hud = pygame.font.SysFont('Arial', 32)
        self.font_clock = pygame.font.SysFont('Arial', 40)
        self.font_nivel = pygame.font.SysFont('Arial', 40)
        self.font_vida = pygame.font.SysFont('Arial', 27)
        self.font_fps = pygame.font.SysFont('Arial', 20)

        # Superficie base para puertas (se crea una vez, se reutiliza)
        self.door_surface_base = pygame.Surface((self.door_length, self.door_thickness), pygame.SRCALPHA)
        pygame.draw.rect(self.door_surface_base, COLOR_PUERTA, (0, 0, self.door_length, self.door_thickness))
        pygame.draw.rect(self.door_surface_base, COLOR_BORDE, (0, 0, self.door_length, self.door_thickness), 2)

    def verInfoEnemigos(self):
        enemy = player.Enemigo()

        for i in range(1, self.numEnemigos):
            enemy = self.enemigosArray[i]
            enemy.logPosicionEnemigo()

    def dibujar_cruz(self, surface, x:int, y:int, tamaño=10, color=(255, 165, 0), grosor=4):
        mitad = tamaño // 2
        pygame.draw.line(surface, color, (x - mitad, y), (x + mitad, y), grosor)
        pygame.draw.line(surface, color, (x, y - mitad), (x, y + mitad), grosor)

    def dibujarCaminoEnemigo(self, nemesis):
        # Pintamos una cruz en el centro de cada casilla donde haya estado el enemigo.
        puntoPrevio = posicion(0, 0)
        flagInit = True
        smallfont = pygame.font.SysFont('Corbel', 15)
        position = self.maze.calcularPixelPorCasilla(977)

        if self.maze.esAlcanzable(nemesis.x, nemesis.y):
            text1 = smallfont.render('X', True, (255, 165, 0))
        else:
            text1 = smallfont.render('X', True, (255, 255, 255))
        
        self.pantalla.blit(text1, (position.x, position.y))
        # Y pintamos también una línea que una estas cruces.
        for elemento in reversed(nemesis.posicionesRecorridas):
            posi: posicion = self.maze.centroCasilla(elemento)
            if not flagInit:
                pygame.draw.line(self.pantalla, (255, 255, 0), posi.x, posi.y, 3)
                pygame.display.flip()
            else:
                flagInit = False

    def draw_door(self, angle):
        """Dibuja la puerta rotando sobre el lado especificado."""
        if self.flagPrint_info:
            print("Dentro de dibujar la puerta.")
        
        # Rotar la superficie
        rotated = pygame.transform.rotate(self.door_surface, -angle)

        # Obtener la posición del pivote en coordenadas locales
        pivot_local = (self.door_length / 2, self.door_thickness)

        # Convertir ángulo a radianes
        angle_rad = math.radians(-angle)

        # Centro de la superficie original
        center_x, center_y = self.door_length / 2, self.door_thickness / 2

        # Vector desde el centro hasta el pivote
        pivot_rel_to_center = (pivot_local[0] - center_x, pivot_local[1] - center_y)

        # Aplicar rotación al vector relativo
        rotated_pivot_x = (pivot_rel_to_center[0] * math.cos(angle_rad) - 
                           pivot_rel_to_center[1] * math.sin(angle_rad))
        rotated_pivot_y = (pivot_rel_to_center[0] * math.sin(angle_rad) + 
                           pivot_rel_to_center[1] * math.cos(angle_rad))

        # Nueva posición del pivote después de rotar (en coordenadas de la superficie original)
        new_pivot_x = center_x + rotated_pivot_x
        new_pivot_y = center_y + rotated_pivot_y

        # Obtener el rectángulo de la superficie rotada
        rotated_rect = rotated.get_rect()

        # Calcular la posición de dibujo para que el pivote quede en (pivot_x, pivot_y)
        draw_x = self.pivot_x - new_pivot_x
        draw_y = self.pivot_y - new_pivot_y

        self.pantalla.blit(rotated, (draw_x, draw_y))
    

    def menu(self):
        color = (255, 255, 255)

        if self.flagPrint_info:
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

        if self.flagPrint_info:
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

        if self.flagPrint_info:
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
        pygame.display.set_caption('Laberinto SquidCastle 2026, Aurora.')
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
        if self.flagPrint_info:
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

        # Jefe Enemigo - OPTIMIZACIÓN: IA solo cada X milisegundos
        tiempo_actual = pygame.time.get_ticks()
        tiempo_desde_ultimo_update = tiempo_actual - self.ultimo_update_ia

       # Detectar cambios importantes que requieren actualización inmediata
        cambio_importante = (
            self.JefeEnemigo.isColision or  # Colisión detectada
            self.JefeEnemigo.kia.colisionParedes or  # Chocó con pared
            self.JefeEnemigo.alarma  # Alarma activada
        )
    
        # Ejecutar IA solo si:
        # 1. Ha pasado el intervalo de tiempo O
        # 2. Hay un cambio importante (colisión, alarma, etc.)
        if tiempo_desde_ultimo_update >= self.ia_update_interval or cambio_importante or self.ia_necesita_update:
            self.JefeEnemigo.casilla = self.maze.calcularCasilla(self.JefeEnemigo.x, self.JefeEnemigo.y)
            self.JefeEnemigo.kia.casilla = self.JefeEnemigo.casilla
            self.JefeEnemigo.kia.definirPosicion(self.JefeEnemigo.x, self.JefeEnemigo.y)
            
            dir = self.JefeEnemigo.kia.update()
            self.JefeEnemigo.elegirDireccion(dir)
            
            self.ultimo_update_ia = tiempo_actual
            self.ia_necesita_update = False
        
        # Actualizar casilla y recorrido siempre (son operaciones rápidas)
        self.JefeEnemigo.casilla = self.maze.calcularCasilla(self.JefeEnemigo.x, self.JefeEnemigo.y)
        self.JefeEnemigo.cargarCasillaRecorrido(self.JefeEnemigo.casilla)

        # Resto de enemigos.
        i = 0
        for nemi in self.EnemigosGroup:
            nemi.casilla = self.maze.calcularCasilla(nemi.x, nemi.y)
            nemi.cargarCasillaRecorrido(nemi.casilla)
            nemi.update()
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

        # --- GESTIÓN PUERTA/S ---
        if self.openingDoor:
            self.door_angle += self.Doorspeed
            if self.door_angle >= 90:
                self.door_angle = 90
                self.openingDoor = False
        elif self.closingDoor:
            self.door_angle -= self.Doorspeed
            if self.door_angle <= 0:
                self.door_angle = 0
                self.closingDoor = False

        # Gestión del scroll de la pantalla.
        self.maze.moverCamara(self.player.x, self.player.y)
        if self.maze.movimientoCamara > 0 and self.maze.flagCamaraCambio:
            self.maze.flagCamaraCambio = False
            self.maze.flagCamara = True
            # Desplazamos todo a la izquierda (Paredes, Jugador, Enemigos, Puertas)
            for x in self.maze.MazeParedes:
                x.rect.x -= CASILLA_PIXEL

            self.player.x -= CASILLA_PIXEL

            for x in self.EnemigosGroup:
                x.rect.x -= CASILLA_PIXEL

            # Puertas
            for x in self.maze.MazePuertas:
                x.rect.x -= CASILLA_PIXEL
                logging.info("Desplazar puertas")
                print("Desplazar puertas")

            # Objetos Extra
            for x in self.maze.MazeBandera:
                x.rect.x -= CASILLA_PIXEL
            for x in self.maze.MazeBotiquin:
                x.rect.x -= CASILLA_PIXEL
            for x in self.maze.MazeChampi:
                x.rect.x -= CASILLA_PIXEL
            for x in self.maze.MazeGranada:
                x.rect.x -= CASILLA_PIXEL
            for x in self.maze.MazeHueso:
                x.rect.x -= CASILLA_PIXEL
            for x in self.maze.MazeLlave:
                x.rect.x -= CASILLA_PIXEL
            for x in self.maze.MazeLlavePuerta:
                x.rect.x -= CASILLA_PIXEL
                logging.info("Desplazar Llave Puertas")
                print("Desplazar Llave Puertas")
            for x in self.maze.MazeOro:
                x.rect.x -= CASILLA_PIXEL
            for x in self.maze.MazePilaHuesos:
                x.rect.x -= CASILLA_PIXEL
        
        # Colisión del jugador con paredes
        colision_player = pygame.sprite.spritecollide(self.player, self.maze.MazeParedes, False)
        if colision_player:
            logging.info(f'COLISION PLAYER DETECTADA - num ELem ({len(colision_player)})')
            if self.flagPrint_info:
                print(f'COLISION PLAYER DETECTADA - num ELem ({len(colision_player)})')

            self.player.x = self.player.prev_x
            self.player.y = self.player.prev_y

            for cl in colision_player:
                logging.info(f'PLAYER colisionó con paRED')

        # Colisión del jugador con Puerta
        colision_playerPuerta = pygame.sprite.spritecollide(self.player, self.maze.MazePuertas, False)
        if colision_playerPuerta:
            logging.info(f'COLISION PLAYER & DOOOOOR - num ELem ({len(colision_playerPuerta)})')
            if self.flagPrint_info:
                print(f'COLISION PLAYER & DOOOOOR - num ELem ({len(colision_playerPuerta)})')

            self.player.x = self.player.prev_x
            self.player.y = self.player.prev_y

            for cl in colision_playerPuerta:
                logging.info(f'PLAYER colisionó con paRED')

        # Colisión de enemigos con paredes
        colision_enemigos = pygame.sprite.groupcollide(self.EnemigosGroup, self.maze.MazeParedes, False, False)
        if colision_enemigos:
            logging.info('COLISION Enemigo DETECTADA %s', len(colision_enemigos))
            if self.flagPrint_info:
                print(f'COLISION Enemigo DETECTADA %s', len(colision_enemigos))
            # Opcional: procesar cada enemigo que colisionó
            for nemesis, paredes in colision_enemigos.items():
                if self.flagPrint_info:
                    print(f'Enemigo en ({nemesis.x}, {nemesis.y}) colisionó con {len(paredes)} paredes')
                logging.info(f'Enemigo en ({nemesis.x}, {nemesis.y}) colisionó con {len(paredes)} paredes')
                
                # Revertir y cambiar dirección solo del enemigo que colisiona
                if hasattr(nemesis, 'revertir_movimiento'):
                    nemesis.revertir_movimiento()

                if nemesis.isJefeEnemigo:
                    if self.flagPrint_info:
                        print("Colision Jefe Enemigo con PARED !!!")
                    nemesis.detectarColision()

                if hasattr(nemesis, 'cambiar_direccion'):
                    nemesis.cambiar_direccion()

        # Colisión de ENemigos con Puerta
        colision_playerPuerta = pygame.sprite.groupcollide(self.EnemigosGroup, self.maze.MazePuertas, False, False)
        if colision_playerPuerta:
            logging.info(f'COLISION Enemigo con Puerta DETECTADA - num ELem ({len(colision_playerPuerta)})')
            # Opcional: procesar cada enemigo que colisionó
            for enemigo, puertas in colision_enemigos.items():
                logging.info(f'Enemigo en ({enemigo.x}, {enemigo.y}) colisionó con {len(puertas)} paredes')
                # Revertir y cambiar dirección solo del enemigo que colisiona
                if hasattr(enemigo, 'revertir_movimiento'):
                    enemigo.revertir_movimiento()
                if hasattr(enemigo, 'cambiar_direccion'):
                    enemigo.cambiar_direccion()

        
        # Colisión de Extras Escenario con Player
        colision_PlayerConExtra = pygame.sprite.spritecollide(self.player, self.maze.MazeExtra, False)
        if colision_PlayerConExtra:
            logging.info('Huesos  IMPACTADA')
            if self.flagPrint_info:
                print('Huesos  IMPACTADA')
            # Opcional: procesar cada enemigo que colisionó
            for cpcE in colision_PlayerConExtra:
                logging.info(f'Huesos tocados')

        # Colisión Player con llave Puerta
        colision_PlayerConLlavePuerta = pygame.sprite.spritecollide(self.player, self.maze.MazeLlavePuerta, True)
        if colision_PlayerConLlavePuerta:
            logging.info('Llave PUERTA cogida')
            if self.flagPrint_info:
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
            if self.flagPrint_info:
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
            if self.flagPrint_info:
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
            if self.flagPrint_info:
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
            if self.flagPrint_info:
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
            if self.flagPrint_info:
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
            if self.flagPrint_info:
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
            if self.flagPrint_info:
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
            if self.flagPrint_info:
                print('Bandera Final IMPACTADA')
            # Opcional: procesar cada enemigo que colisionó
            for cpcE in colision_PlayerConBandera:
                logging.info('Bandera tocada')

        # Colisión de Balas Enemigos con Paredes
        for EnemyAmmo in self.EnemigosGroup:
            colision_EnemyBalasParedes = pygame.sprite.groupcollide(EnemyAmmo.balas, self.maze.MazeParedes, False, False)
            if colision_EnemyBalasParedes:
                logging.info('COLISION Blas Player DETECTADA %s', len(colision_EnemyBalasParedes))
                # Opcional: procesar cada enemigo que colisionó
                for muni, paredes in colision_EnemyBalasParedes.items():
                    logging.info(f'BalaEnemigo en ({muni.x}, {muni.y}) colisionó con {len(paredes)} paredes')
                    muni.kill()
        
        # Colisión de Balas Player con Paredes
        colision_PlayerBalasConParedes = pygame.sprite.groupcollide(self.player.balas, self.maze.MazeParedes, False, False)
        if colision_PlayerBalasConParedes:
            logging.info('COLISION Enemigo DETECTADA %s', len(colision_PlayerBalasConParedes))
            # Opcional: procesar cada enemigo que colisionó
            for muni, paredes in colision_PlayerBalasConParedes.items():
                logging.info(f'Bala Player en ({muni.x}, {muni.y}) colisionó con {len(paredes)} paredes')
                muni.kill()

    def on_render(self):
       if self.pause == False:
           self.pantalla.fill((0, 0, 0))
           # Defino el laberinto
           # logging.debug("Pintamos laberinto.")  # Comentado para mejorar rendimiento
           self.maze.draw(self.pantalla, self.floor_surf, self.wall_surf, self.casillaObjetosTocados)

           if self.iteracion == 35:
               self.iteracion = 0

           # Aquí busco lugar suelo para Jugador
           # Llamada a la IA
           if self.flagInit == True:
               self.flagInit = False
               # if self.flagPrint_info:
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

           # --- Dibujado PUERTA/S ---
           if self.flagPrint_info:
               print(f"Casillas con puerta  (visible): ", len(self.maze.posicionPuerta))
               
           # Defino las puertas - OPTIMIZADO: reutilizar superficie base
           i = 0
           for porte in self.maze.posicionPuerta:
               pos = self.maze.calcularPixelPorCasilla(porte[0])
               if i == 0:
                   self.door_y = pos.y+5
                   self.door_x = pos.x+30
               else:
                   self.door_y = pos.y
                   self.door_x = pos.x
               
               if self.flagPrint_info:
                   print("Posicion X e Y puerta: ", self.door_x, self.door_y)
               
               self.pivot_x = self.door_x
               self.pivot_y = self.door_y 

               # OPTIMIZACIÓN: Usar superficie precargada en lugar de crear nueva
               self.door_surface = self.door_surface_base.copy()
               self.draw_door(self.door_angle)
               i += 1

           # Aquí busco lugar suelo para Enemigo y Jefe Enemigo.
           # logging.debug("Pintamos los enemigos.")  # Comentado para mejorar rendimiento
           for i in range(0, self.numEnemigos):
               self.enemigo = self.enemigosArray[i]
               if(self.enemigo.isJefeEnemigo):
                   if self.flagPrint_info:
                       print('---Posición DRAW LORD: ',self.JefeEnemigo.x, self.JefeEnemigo.y)
                   self.pantalla.blit(self._JefeEnemigo, (self.JefeEnemigo.x, self.JefeEnemigo.y))
               else:   
                   if self.flagPrint_info:
                       print('---Posición DRAW ENEMIGO: ',i, self.enemigo.x, self.enemigo.y)
                   self.pantalla.blit(self._enemigo, (self.enemigo.x, self.enemigo.y))
                   if self.pintaRectángulos == True:
                       pygame.draw.rect(self.pantalla, (255, 0, 0), self.enemigo.rect, 2)

           # Jefe Enemigo + VISIÓN
           # logging.debug('Pintamos el JEFE enemigo.')  # Comentado para mejorar rendimiento
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
               rot_angle = -self.JefeEnemigo.angle + 90
               rotated = pygame.transform.rotate(self.JefeEnemigo.visionImage, rot_angle)
               rect = rotated.get_rect(center=(x, y))
               self.pantalla.blit(rotated, rect)

           if(self.JefeEnemigo.alarma):
               # --- Control del tiempo del bocadillo ---
               current_time = pygame.time.get_ticks()
               elapsed = current_time - self.JefeEnemigo.bubble_start_time
               if elapsed < self.JefeEnemigo.bubble_duration:
                   # Calculamos opacidad
                   if elapsed > self.JefeEnemigo.bubble_duration - self.JefeEnemigo.fade_duration:
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
               # logging.debug('DISPARO DeL Player.')  # Comentado para mejorar rendimiento
               self.player.balas.draw(self.pantalla)

           # Pintar disparos de Jefe Enemigo
           if self.JefeEnemigo.flagDisparo == True:
               # logging.debug('Pintamos Disparo DEL JEFE enemigo.')  # Comentado para mejorar rendimiento
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
       # logging.debug("Pintando la Cabecera de Valores")  # Comentado para mejorar rendimiento

       # Objetos adquiridos (Llaves & Armas) - OPTIMIZADO: usar imágenes precargadas
       if self.player.llavePuerta:
           self.pantalla.blit(self.imagen_llave_puerta, (620, 110))

       if self.player.llaveFinNivel:
           self.pantalla.blit(self.imagen_llave, (660, 110))
       
       if self.player.pistola:
           self.pantalla.blit(self.imagen_pistola, (700, 110))

       if self.player.granada:
           self.pantalla.blit(self.imagen_granada, (740, 110))
       
       if self.player.laser:
           self.pantalla.blit(self.imagen_laser, (780, 110))

       # Puntuación - OPTIMIZADO: usar fuente precargada
       puntos_text = self.font_hud.render(f"Puntos: {self.HeadPuntuacion.textoPuntos}", True, (255, 255, 0))
       self.pantalla.blit(puntos_text, (600, 10))

       # Arma y Munición - OPTIMIZADO: usar fuente precargada
       puntos_text = self.font_hud.render(f"Arma: ", True, (100, 100, 100))
       self.pantalla.blit(puntos_text, (600, 40))
       puntos_text = self.font_hud.render(f"{self.HeadGunAmmo.textoArma}", True, (255, 255, 255))
       self.pantalla.blit(puntos_text, (720, 40))
       puntos_text = self.font_hud.render(f"Munición: ", True, (100, 100, 100))
       self.pantalla.blit(puntos_text, (600, 70))
       puntos_text = self.font_hud.render(f"{self.HeadGunAmmo.textoMunicion}", True, (255, 255, 255))
       self.pantalla.blit(puntos_text, (750, 70))

       # Reloj - OPTIMIZADO: usar imágenes y fuentes precargadas
       tiempo_actual = pygame.time.get_ticks()
       segundos_transcurridos = (tiempo_actual - self.tiempo_inicio) // 1000
       tiempo_restante = max(0, self.HeadReloj.maxTiempo - segundos_transcurridos)
       self.HeadReloj.tiempoInteger = int(tiempo_restante)

       if self.HeadReloj.tiempoInteger == 0:
           pass
       
       self.pantalla.blit(self.imagen_clock, (360, 10))
       puntos_text = self.font_clock.render(f"{self.HeadReloj.textoReloj}", True, (255, 255, 255))
       self.pantalla.blit(puntos_text, (420, 10))

       # Nivel - OPTIMIZADO: usar fuente precargada
       puntos_text = self.font_nivel.render(f"Level: ", True, (100, 100, 100))
       self.pantalla.blit(puntos_text, (360, 50))
       puntos_text = self.font_nivel.render(f"{self.HeadNivel.textoNivel}", True, (0, 0, 255))
       self.pantalla.blit(puntos_text, (480, 50))

       # Huesos - OPTIMIZADO: usar fuente precargada
       puntos_text = self.font_hud.render(f"Huesos:", True, (100, 100, 100))
       self.pantalla.blit(puntos_text, (360, 90))
       puntos_text = self.font_hud.render(f"{self.HeadHuesos.textoHuesos}", True, (255, 255, 255))
       self.pantalla.blit(puntos_text, (485, 90))

       # Nombre Jugador - OPTIMIZADO: usar fuente precargada
       puntos_text = self.font_hud.render(f"Memmaker650", True, (100, 100, 100))
       self.pantalla.blit(puntos_text, (10, 10))

       # Barra de Vida
       self.pantalla.blit(self.HeadBarraDeVida.spriteBarraDeVida, (10, 50))
       # Barra de Vida (Porcentaje) - OPTIMIZADO: usar fuente precargada
       puntos_text = self.font_vida.render(f"{self.HeadBarraDeVida.textoVida}", True, (255, 255, 255))
       self.pantalla.blit(puntos_text, (85, 60))

       # FPS - OPTIMIZADO: usar fuente precargada
       fps = int(self.clock.get_fps())
       fps_text = self.font_fps.render(f"FPS: {fps}", True, (255, 255, 0))
       # logging.debug("FPS de pintado : %i", fps)  # Comentado para mejorar rendimiento
       self.pantalla.blit(fps_text, (10, 110))

       pygame.display.flip() # Aquí es donde ploteamos todo.

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        self.clock.tick(60)
        if self.flagPrint_info:
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
                        if self.flagPrint_info:
                            print("Tecla C presionada")
                        if self.pintaRectángulos == True:
                           self.pintaRectángulos = False
                        else:
                            self.pintaRectángulos = True 
                    if event.key == pygame.K_d:
                        # alternar entre abrir y cerrar
                        if self.door_angle <= 0:
                            self.openingDoor = True
                            self.closingDoor = False
                        elif self.door_angle >= 90:
                            self.closingDoor = True
                            self.openingDoor = False
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
                        if self.flagPrint_info:
                            print('¡¡¡ SOLtado cursor DERECHO !!!')
                        self.player.stop()

                    if event.key == pygame.K_LEFT:
                        self.movimiento = False
                        logging.info('¡¡¡ SOLtado cursor IZQUIERDO !!!')
                        if self.flagPrint_info:
                            print('¡¡¡ SOLtado cursor IZQUIERDO !!!')
                        self.player.stop()

                    if event.key == pygame.K_UP:
                        self.movimiento = False
                        logging.info('¡¡¡ SOLtado cursor ARRIBA !!!')
                        if self.flagPrint_info:
                            print('¡¡¡ SOLtado cursor ARRIBA !!!')
                        self.player.stop()

                    if event.key == pygame.K_DOWN:
                        self.movimiento = False
                        logging.info('¡¡¡ SOLtado cursor ABAJO !!!')
                        if self.flagPrint_info:
                            print('¡¡¡ SOLtado cursor ABAJO !!!')
                        self.player.stop()

            if self.movimiento == True:
                if(self.player.orientacion == 0):
                    self.player.moveUp()
                elif(self.player.orientacion == 1):
                    self.player.moveRight()
                elif(self.player.orientacion == 2):
                    self.player.moveDown()
                elif(self.player.orientacion == 3):
                    self.player.moveLeft()
                else:
                    logging.info('¡¡¡ What !!!')
                    if self.flagPrint_info:
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
        logging.info("Level loaded:", os.path.basename(level_data.path), level_data.width, level_data.height)
        print("Level loaded: ", os.path.basename(level_data.path), level_data.width, level_data.height)
        level_data.debug_layers()
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logging.error("Error cargando nivel JSON: %s", e)
        print("Error cargando nivel JSON: %s", e)
        level_data = None

    notification.notify(title="Inicio", message="Inicio Juego", app_name="OctoPussy", app_icon="/assets/player.png")

    # App principal
    theApp = App()
    theApp.on_execute()

    #Cerramos base de datos
    sqliteConnection.close()
    logging.info("The SQLite connection is closed")

    logging.info("JUEGO ¡¡ Se acabo !!")
