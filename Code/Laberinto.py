import os
import sys

# Los módulos del juego (mates, player, MazeLab...) están junto a este fichero.
DIR_CODIGO = os.path.dirname(os.path.abspath(__file__))
if DIR_CODIGO not in sys.path:
    sys.path.insert(0, DIR_CODIGO)

# Todas las rutas del juego (Resources, log, DB, Levels, Code/assets) son relativas a la
# raíz del proyecto. Nos situamos ahí ANTES de importar los módulos que cargan imágenes,
# para que el juego arranque igual desde la raíz, desde Code/ o desde PyCharm.
DIR_PROYECTO = os.path.dirname(DIR_CODIGO)
os.chdir(DIR_PROYECTO)
DIR_NIVELES = os.path.join(DIR_PROYECTO, "Levels")
RUTA_BD = os.path.join(DIR_PROYECTO, "DB", "tutorial.db")

from typing import Any
import mates
import player
import infoPantalla

import logging
import statistics
import MazeLab
import Sonido
import Luces
import estadisticas
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
from MazeLab import Puerta

# ---------------
# Constantes
# ---------------

SCREEN_WIDTH = 864
SCREEN_HEIGHT = 1000
BIAS = 136
CASILLA_PIXEL = 32
NUM_CASILLAS = 27
IMG_DIR = "Resources"
SONIDO_DIR = "Resources/Sonidos"
FPS = 60 # desired framerate in frames per second.

# Combate
DANO_ENEMIGO = 10            # vida que quita tocar a un enemigo
DANO_JEFE = 20               # vida que quita tocar al jefe
DANO_BALA_ENEMIGA = 10       # vida que quita una bala enemiga
DANO_BALA_JUGADOR = 50       # vida que quita al enemigo una bala del jugador (enemigos: 100, jefe: VIDA_JEFE)
VIDA_JEFE = 200
TIEMPO_INVULNERABLE_MS = 1000  # tras una herida, el jugador no recibe otra durante este tiempo
PUNTOS_ENEMIGO = 50
PUNTOS_JEFE = 200

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
COLOR_BORDE = (90, 60, 40)

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

# ------------------------------
# Clases y Funciones utilizadas
# ------------------------------
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
        self.x = valorX
        self.y = valorY
            
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

    efecto_rojo = False
    impactoPlayer = False
    impactoEnemigo = False
    impactoJefeEnemigo = False
    enemigoImpactado = None

    # Estadísticas del nivel en curso y resultado ("muerto" o "completado") cuando acaba.
    estadisticas = None
    resultadoPartida = None
    ultimaHerida_ms = -10 ** 9

    # Nivel oscuro: linterna del jugador (None si el nivel está iluminado).
    oscuridad = 0.0
    linterna = None
    posEnemyImpc = posicion(0, 0)

    pintaRectángulos = bool = True
    pintaVision = bool = True

    # Flags de Depuración de información.
    flagPrint_info = False
    flagPrint_ColisionInfo = False
    flagDebugEnemigos = True
    flagPintarBocadilloTexto = False
    bocadillo_timer = 0
    textoBocadillo = None
    grupo_explosiones = pygame.sprite.Group()
    flagExplosion = False
    explosion_timer = 0

    grupo_humo = pygame.sprite.Group()
    flagHumo = False
    humo_timer = 0

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

    # Gestión del Sonido.
    Sound = None
    canalmusicaFondo = None

    # Estado del mensaje de alerta
    alerta_activa = False
    alerta_texto = "X"
    alerta_inicio_ms = 0
    alerta_duracion_ms = 3000  # 3 segundos

    font_alerta = None # elige tu fuente

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

        # Gestión del Mapa
        self.map_surface = pygame.Surface(
            (self.windowWidth, self.windowHeight)).convert()
        self.flagDebugEnemigos = True
        self.rebuild_map = True
        self.floor_surf = None
        self.wall_surf = None

        self.Sound = Sonido.Sonido()

        self.visionEnemigos = True
        self.tiempo_inicio = pygame.time.get_ticks()

        self.salir = False

        self.ia_update_interval = 500  # milisegundos (500ms = 0.5 segundos, o 1000ms = 1 segundo)
        self.ultimo_update_ia = pygame.time.get_ticks()
        self.ia_necesita_update = True 

        # Init Personajes
        self.player = player.Player()  # damos los valores por defecto.

        # Cargando el escenario por defecto y colocando enemigos y jefe.
        self.prepararNivel()

        pygame.init()

        self.font_alerta = pygame.font.SysFont('Impact', 32) 
        
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

    # Prepara el laberinto (el de por defecto o un nivel JSON de la carpeta Levels)
    # y coloca a los enemigos y al jefe sobre casillas de suelo.
    def prepararNivel(self, nivel=None):
        self.maze = MazeLab.Maze(nivel)
        logging.info("Cargado el escenario")
        self.conexiones = MazeLab.Maze.precalcular_conexiones(
            self.maze.MazeLaberinto,
            MazeLab.NUM_CASILLAS_H,
            MazeLab.NUM_CASILLAS_VERTI
        )
        logging.info("GEnero las conexiones del escenario")

        # Estado de la partida que depende del laberinto.
        self.enemigosArray = []
        self.EnemigosGroup = pygame.sprite.Group()
        self.casillaObjetosTocados = set()
        self.flagInit = True
        self.rebuild_map = True
        self.tiempo_inicio = pygame.time.get_ticks()
        self.estadisticas = estadisticas.Estadisticas(inicio_ms=self.tiempo_inicio)
        self.resultadoPartida = None
        self.ultimaHerida_ms = -10 ** 9

        # Niveles oscuros: sólo se ve lo que ilumina la linterna (código en Luces.py).
        self.oscuridad = nivel.oscuridad if nivel is not None else 0.0
        if self.oscuridad > 0:
            zonaLaberinto = (0, BIAS, SCREEN_WIDTH, SCREEN_HEIGHT - BIAS)
            self.linterna = Luces.Linterna(zonaLaberinto, opacidad=self.oscuridad)
            self.linterna.apuntar(self.player.orientacion, instantaneo=True)
        else:
            self.linterna = None

        candidatas = self.casillasInicioEnemigos()

        # Llenar el vector de enemigos
        for i in range(0, self.numEnemigos):
            self.enemigo = player.Enemigo()
            self.enemigo.casilla = candidatas.pop(0)
            pos = MazeLab.Maze.calcularPixelPorCasilla(self.enemigo.casilla)
            self.enemigo.x = pos.x
            self.enemigo.y = pos.y
            self.enemigo.prev_x = self.enemigo.x
            self.enemigo.prev_y = self.enemigo.y
            self.enemigosArray.append(self.enemigo)
            self.EnemigosGroup.add(self.enemigo)

        # Ubicar al jefe enemigo en el centro de su casilla.
        self.JefeEnemigo = player.Enemigo()
        self.JefeEnemigo.isJefeEnemigo = True
        self.JefeEnemigo.vida = VIDA_JEFE
        self.JefeEnemigo.casilla = candidatas.pop(0)
        pos = MazeLab.Maze.centroCasilla(self.JefeEnemigo.casilla)
        self.JefeEnemigo.x = pos.x - (self.JefeEnemigo.rect.width // 2)
        self.JefeEnemigo.y = pos.y - (self.JefeEnemigo.rect.height // 2)
        self.JefeEnemigo.rect.x = self.JefeEnemigo.x
        self.JefeEnemigo.rect.y = self.JefeEnemigo.y
        self.JefeEnemigo.prev_x = self.JefeEnemigo.x
        self.JefeEnemigo.prev_y = self.JefeEnemigo.y
        self.JefeEnemigo.kia.definirPosicion(pos.x, pos.y)
        self.JefeEnemigo.kia.casilla = self.JefeEnemigo.casilla

    # Casillas de suelo visibles donde pueden empezar los enemigos, sin repetir y lejos del jugador.
    # Primero las que marca el nivel (perros del JSON) y luego el resto, ambas en orden aleatorio.
    def casillasInicioEnemigos(self):
        ancho = MazeLab.NUM_CASILLAS_H
        inicio = self.maze.casillaInicioJugador()

        def valida(c):
            if self.maze.MazeLaberinto[c] != 1 or not MazeLab.Maze.elementoVisibleCasilla(c):
                return False
            if inicio is None:
                return True
            distancia = abs(c % ancho - inicio % ancho) + abs(c // ancho - inicio // ancho)
            return distancia >= 4

        delNivel = [c for c in dict.fromkeys(self.maze.posicionesEnemigos) if valida(c)]
        resto = [c for c in range(len(self.maze.MazeLaberinto)) if valida(c) and c not in delNivel]
        random.shuffle(delNivel)
        random.shuffle(resto)
        candidatas = delNivel + resto
        if len(candidatas) < self.numEnemigos + 1:
            raise ValueError("El laberinto no tiene suficientes casillas de suelo para los enemigos")
        return candidatas

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
        # posicionesRecorridas guarda tuplas (casilla, tiempo).
        for elemento in reversed(nemesis.posicionesRecorridas):
            casilla = elemento[0] if isinstance(elemento, tuple) else elemento
            posi: posicion = self.maze.centroCasilla(casilla)
            if not flagInit:
                pygame.draw.line(self.pantalla, (255, 255, 0), (puntoPrevio.x, puntoPrevio.y), (posi.x, posi.y), 3)
            else:
                flagInit = False
            puntoPrevio = posi

    def menu(self):
        color = (255, 255, 255)

        if self.flagPrint_info:
            print("Dentro del Menú!!")
        
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

        mouse = pygame.mouse.get_pos()

        while True:
            for ev in pygame.event.get():

                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    self.salir = True
                    pygame.quit()
                    sys.exit()

                # Chequeamos click del ratón
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    mouse = ev.pos

                    # Chequeamos si click en algún botón
                    # Botón 1 - Nuevo Juego
                    if mates.dentroBoton(mouse, int(width / 2), int((height / 2)) - 60, 230, 40):
                        self.tocaMenu = False
                        self.on_execute()

                    # Botón 2 - Opciones (misma zona en la que se pinta el botón)
                    if mates.dentroBoton(mouse, int(width / 2), int(height / 2) - 10, 230, 40):
                        logging.info("Opciones del juego, pulsada.")
                        self.tocaMenu = False
                        self.menuOpciones()

                    # Botón 3 - Cargar partida
                    #TO DO Programación botón cargar partida.

                    # Botón 4 - Salir del juego
                    if mates.dentroBoton(mouse,  int(width / 2), int((height / 2)) + 190, 230, 40):
                        self.tocaMenu = False
                        self.salir = True
                        pygame.quit()
                        sys.exit()

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
                # Botón 2
                elif mates.dentroBoton(mouse, width / 2, (height / 2)-10, 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int(height / 2) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +190, 230, 40])
                # Botón 3
                elif mates.dentroBoton(mouse, width / 2, (height / 2)+40 , 230, 40):
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

        mouse = pygame.mouse.get_pos()

        while True:
            for ev in pygame.event.get():

                if ev.type == pygame.QUIT:
                    self.salir = True
                    pygame.quit()
                    sys.exit()

                # Chequeamos click del ratón
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    mouse = ev.pos

                    # Chequeamos si click en algún botón
                    # Botón 1 - Seleccion Nivel
                    if mates.dentroBoton(mouse, int(width / 2), int((height / 2)) - 60, 230, 40):
                        logging.info("Pulsado Botón Selección de Nivel.")
                        self.tocaMenu = False
                        self.seleccionNivel()

                    # Botón 2 - Estadísticas Juego (TO DO: de momento abre Selección de Nivel)
                    if mates.dentroBoton(mouse, int(width / 2), int((height / 2)) - 10, 230, 40):
                        logging.info("Pulsado Botón : Estadísticas de Juego del Jugador.")
                        self.tocaMenu = False
                        self.seleccionNivel()

                    # Botón 3 - Inventario Juego
                    if mates.dentroBoton(mouse, int(width / 2), int(height / 2) + 40, 230, 40):
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
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_darkblue, [int(width / 2), int((height / 2)) +190, 230, 40])
                # Botón 2
                elif mates.dentroBoton(mouse, width / 2, (height / 2)-10, 230, 40):
                    pygame.draw.rect(self.pantalla, color_darkorange, [int(width / 2), int(height / 2) -10, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) -60, 230, 40])
                    pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) +40, 230, 40])
                    pygame.draw.rect(self.pantalla, color_darkblue, [int(width / 2), int((height / 2)) +190, 230, 40])
                # Botón 3
                elif mates.dentroBoton(mouse, width / 2, (height / 2)+40 , 230, 40):
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
                # Textos centrados en su botón (230x40) para que los largos quepan dentro.
                for texto, dy in ((text1, -60), (text2, -10), (text3, 40), (text4, 190)):
                    boton = pygame.Rect(int(width / 2), int(height / 2) + dy, 230, 40)
                    self.pantalla.blit(texto, texto.get_rect(center=boton.center))

                # updates the frames of the game
                pygame.display.update()
                
    # Botones del menú Seleccionar Nivel: (y relativa a la mitad de la pantalla, número de nivel).
    # None es el botón Volver. El nivel N se carga del fichero Levels/Level_N.json.
    BOTONES_NIVEL = [(-60, 1), (-10, 2), (40, 3), (90, 4), (140, 5), (200, None)]

    def seleccionNivel (self):
        color = (255, 255, 255)

        if self.flagPrint_info:
            print("Dentro de Selecciona Nivel!!")     

        width = self.pantalla.get_width()
        height = self.pantalla.get_height()

        # defining a font
        smallfont = pygame.font.SysFont('Corbel', 35)
        Titlefont = pygame.font.SysFont('Impact', 150)

        textTitle = Titlefont.render('Octopussy', True, color_otherorange)
        textos = {numero: smallfont.render(f'Nivel {numero}' if numero else 'Volver', True, color)
                  for _, numero in self.BOTONES_NIVEL}

        mouse = pygame.mouse.get_pos()

        while True:
            for ev in pygame.event.get():

                if ev.type == pygame.QUIT:
                    self.salir = True
                    pygame.quit()
                    sys.exit()

                # Chequeamos click del ratón (zona = rectángulo pintado del botón)
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    mouse = ev.pos
                    for dy, numero in self.BOTONES_NIVEL:
                        if not mates.dentroBoton(mouse, int(width / 2), int(height / 2) + dy, 230, 40):
                            continue
                        if numero is None:
                            logging.info("Pulsado Botón Voler al Menú Principal")
                            self.tocaMenu = False
                            self.menu()
                        else:
                            logging.info("Pulsado Botón Nivel %s", numero)
                            self.confirmarCargaNivel(numero)

            if self.salir == False:
                self.pantalla.fill((60, 25, 60))
                mouse = pygame.mouse.get_pos()

                for dy, numero in self.BOTONES_NIVEL:
                    encima = mates.dentroBoton(mouse, int(width / 2), int(height / 2) + dy, 230, 40)
                    if numero is None:
                        colorBoton = color_overblue if encima else color_darkblue
                    else:
                        colorBoton = color_darkorange if encima else color_dark
                    pygame.draw.rect(self.pantalla, colorBoton, [int(width / 2), int(height / 2) + dy, 230, 40])
                    self.pantalla.blit(textos[numero], ((width / 2) + 50, (height / 2) + dy + 10))

                self.pantalla.blit(textTitle, ((width / 2) - 400, (height / 2) - 400))

                # updates the frames of the game
                pygame.display.update()

    # Pide confirmación y, si el usuario acepta, carga Levels/Level_<numero>.json y empieza la partida.
    # Devuelve False si se cancela o el nivel no se puede cargar.
    def confirmarCargaNivel(self, numero):
        fichero = f"Level_{numero}.json"
        try:
            nivel = LevelParser(DIR_NIVELES).load_by_name(fichero)
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as error:
            logging.error("No se puede cargar %s: %s", fichero, error)
            self.dialogoConfirmacion(f"No se puede cargar el Nivel {numero}", [str(error)],
                                     textoSi="Aceptar", textoNo=None)
            return False

        detalle = [f"Fichero {fichero}: {nivel.width}x{nivel.height} casillas"]
        problemas = nivel.analizar()
        if nivel.oscuridad:
            detalle.append("Nivel oscuro: sólo verás lo que ilumine tu linterna.")
        if problemas:
            detalle.append(f"Aviso: el nivel tiene {len(problemas)} problema(s). {problemas[0]}")

        if not self.dialogoConfirmacion(f"¿Cargar el Nivel {numero}?", detalle):
            logging.info("Carga del Nivel %s cancelada", numero)
            return False

        try:
            self.prepararNivel(nivel)
        except ValueError as error:
            logging.error("Nivel %s no válido: %s", numero, error)
            self.dialogoConfirmacion(f"No se puede cargar el Nivel {numero}", [str(error)],
                                     textoSi="Aceptar", textoNo=None)
            return False

        logging.info("Cargado el Nivel %s desde %s", numero, fichero)
        self.HeadNivel.definirNumeroNivel(numero)
        self.tocaMenu = False
        self.on_execute()
        return True

    # Ventana de diálogo modal sobre la pantalla actual.
    # Devuelve True con el botón de aceptar o INTRO, y False con el de cancelar o ESC.
    # Con textoNo=None sólo muestra el botón de aceptar (mensaje informativo).
    def dialogoConfirmacion(self, titulo, detalle=(), textoSi="Sí", textoNo="Cancelar"):
        anchoPantalla, altoPantalla = self.pantalla.get_size()
        fondo = self.pantalla.copy()
        oscuro = pygame.Surface((anchoPantalla, altoPantalla), pygame.SRCALPHA)
        oscuro.fill((0, 0, 0, 160))

        fuenteTitulo = pygame.font.SysFont('Impact', 34)
        fuenteTexto = pygame.font.SysFont('Corbel', 24)
        fuenteBoton = pygame.font.SysFont('Corbel', 30)

        anchoCaja = 600
        lineas = []
        for texto in detalle:
            lineas.extend(self.partirTexto(texto, fuenteTexto, anchoCaja - 40))

        caja = pygame.Rect(0, 0, anchoCaja, 170 + len(lineas) * 28)
        caja.center = (anchoPantalla // 2, altoPantalla // 2)

        self.botonDialogoSi = pygame.Rect(0, 0, 160, 46)
        self.botonDialogoNo = pygame.Rect(0, 0, 160, 46) if textoNo else None
        if self.botonDialogoNo:
            self.botonDialogoSi.midbottom = (caja.centerx - 95, caja.bottom - 20)
            self.botonDialogoNo.midbottom = (caja.centerx + 95, caja.bottom - 20)
        else:
            self.botonDialogoSi.midbottom = (caja.centerx, caja.bottom - 20)

        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.salir = True
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        return True
                    if ev.key == pygame.K_ESCAPE:
                        return False
                if ev.type == pygame.MOUSEBUTTONDOWN and getattr(ev, "button", 1) == 1:
                    if self.botonDialogoSi.collidepoint(ev.pos):
                        return True
                    if self.botonDialogoNo and self.botonDialogoNo.collidepoint(ev.pos):
                        return False

            raton = pygame.mouse.get_pos()
            self.pantalla.blit(fondo, (0, 0))
            self.pantalla.blit(oscuro, (0, 0))
            pygame.draw.rect(self.pantalla, (60, 25, 60), caja, border_radius=12)
            pygame.draw.rect(self.pantalla, color_otherorange, caja, 3, border_radius=12)

            textoTitulo = fuenteTitulo.render(titulo, True, BLANCO)
            self.pantalla.blit(textoTitulo, textoTitulo.get_rect(midtop=(caja.centerx, caja.top + 20)))
            for i, linea in enumerate(lineas):
                textoLinea = fuenteTexto.render(linea, True, BLANCO)
                self.pantalla.blit(textoLinea, (caja.left + 20, caja.top + 75 + i * 28))

            botones = [(self.botonDialogoSi, textoSi, color_darkorange, color_dark)]
            if self.botonDialogoNo:
                botones.append((self.botonDialogoNo, textoNo, color_overblue, color_darkblue))
            for rect, texto, colorEncima, colorNormal in botones:
                pygame.draw.rect(self.pantalla, colorEncima if rect.collidepoint(raton) else colorNormal,
                                 rect, border_radius=8)
                textoBoton = fuenteBoton.render(texto, True, BLANCO)
                self.pantalla.blit(textoBoton, textoBoton.get_rect(center=rect.center))

            pygame.display.update()

    # Divide un texto en líneas que quepan en 'ancho' píxeles con la fuente indicada.
    @staticmethod
    def partirTexto(texto, fuente, ancho):
        lineas = []
        actual = ""
        for palabra in texto.split():
            prueba = f"{actual} {palabra}".strip()
            if fuente.size(prueba)[0] <= ancho or not actual:
                actual = prueba
            else:
                lineas.append(actual)
                actual = palabra
        if actual:
            lineas.append(actual)
        return lineas

    def inventarioJuego(self):
        # TO DO Pantalla de inventario. De momento se vuelve al menú desde el que se llamó.
        logging.info("Inventario del juego: pendiente de programar.")

    # Resta vida al jugador y la apunta en las estadísticas. Tras una herida hay un tiempo de
    # invulnerabilidad para que un mismo choque no quite vida en todos los frames.
    # Devuelve True si el jugador ha recibido la herida.
    def herirJugador(self, dano):
        ahora = pygame.time.get_ticks()
        if ahora - self.ultimaHerida_ms < TIEMPO_INVULNERABLE_MS:
            return False
        self.ultimaHerida_ms = ahora
        self.HeadBarraDeVida.vida = max(0, self.HeadBarraDeVida.vida - dano)
        self.estadisticas.registrarHerida(dano)
        logging.info("Jugador herido (-%s). Vida: %s", dano, self.HeadBarraDeVida.vida)
        if self.HeadBarraDeVida.vida <= 0:
            self.resultadoPartida = "muerto"
        return True

    # Fin del nivel: cierra las estadísticas, las guarda en la BD sólo si se ha completado el
    # nivel, muestra la pantalla final y vuelve al menú con una partida nueva.
    def terminarPartida(self, completado):
        self.estadisticas.finalizar(pygame.time.get_ticks(), nivel=self.HeadNivel.NumeroNivel,
                                    puntos=self.HeadPuntuacion.puntos)
        if completado:
            try:
                self.estadisticas.guardar(RUTA_BD)
                pie = "Estadísticas guardadas en la base de datos."
            except sqlite3.Error as error:
                logging.error("No se han podido guardar las estadísticas: %s", error)
                pie = "No se han podido guardar las estadísticas."
            self.pantallaFinal("¡NIVEL COMPLETADO!", VERDE, self.estadisticas.lineas(), pie)
        else:
            self.pantallaFinal("GAME OVER", ROJO, self.estadisticas.lineas(),
                               "Las estadísticas sólo se guardan si terminas el nivel.")
        self.reiniciarPartida()
        self.tocaMenu = False
        self.menu()

    # Pantalla de fin de nivel: título y, debajo, las estadísticas. Se cierra con INTRO, ESC o un clic.
    def pantallaFinal(self, titulo, colorTitulo, lineas, pie=""):
        ancho = self.pantalla.get_width()
        fuenteTitulo = pygame.font.SysFont('Impact', 110)
        fuenteSubtitulo = pygame.font.SysFont('Corbel', 30)
        fuenteDatos = pygame.font.SysFont('Corbel', 34)
        fuentePie = pygame.font.SysFont('Corbel', 26)
        subtitulo = f"Nivel {self.estadisticas.nivel} - {self.estadisticas.jugador} - Puntos: {self.estadisticas.puntos}"

        pygame.event.clear()  # que una tecla pulsada durante el juego no cierre la pantalla
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.salir = True
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                    return
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    return

            self.pantalla.fill((25, 10, 25))
            texto = fuenteTitulo.render(titulo, True, colorTitulo)
            self.pantalla.blit(texto, texto.get_rect(center=(ancho // 2, 190)))
            texto = fuenteSubtitulo.render(subtitulo, True, GRIS)
            self.pantalla.blit(texto, texto.get_rect(center=(ancho // 2, 290)))
            for i, linea in enumerate(lineas):
                texto = fuenteDatos.render(linea, True, BLANCO)
                self.pantalla.blit(texto, texto.get_rect(center=(ancho // 2, 380 + i * 52)))
            if pie:
                texto = fuentePie.render(pie, True, AMARILLO)
                self.pantalla.blit(texto, texto.get_rect(center=(ancho // 2, 780)))
            texto = fuentePie.render("Pulsa INTRO o haz clic para continuar", True, GRIS)
            self.pantalla.blit(texto, texto.get_rect(center=(ancho // 2, 840)))
            pygame.display.update()

    # Deja la App lista para una partida nueva con el laberinto por defecto.
    def reiniciarPartida(self):
        player.Player.balas.empty()
        player.Enemigo.balas.empty()
        self.player = player.Player()
        self.PlayerGroup = pygame.sprite.Group()
        self.HeadBarraDeVida = infoPantalla.barraDeVida()
        self.HeadPuntuacion = infoPantalla.panelPuntuacion()
        self.HeadHuesos = infoPantalla.infoHuesos()
        self.HeadNivel = infoPantalla.infoNivel()
        self.efecto_rojo = False
        self.impactoPlayer = self.impactoEnemigo = self.impactoJefeEnemigo = False
        self.flagPintarBocadilloTexto = False
        self.alerta_activa = False
        self.movimiento = False
        self.prepararNivel()

    def on_init(self):
        pygame.display.set_caption('Laberinto SquidCastle 2026, Aurora.')
        logging.info("Inicio del juego.")

        logging.info("Pintamos el menú del juego.")
        if self.tocaMenu:
            self.menu()
        
        self.Sound.musica = pygame.mixer.Sound("./Resources/Sonidos/sobrecarga-cibernetica.mp3")

        logging.info("Empezamos un juego nuevo.")
        self._running = True
        # El reloj y el tiempo de las estadísticas empiezan al empezar a jugar, no en los menús.
        self.tiempo_inicio = pygame.time.get_ticks()
        self.estadisticas.inicio_ms = self.tiempo_inicio
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
            if enemy.vida <= 0:
                continue  # enemigo muerto en esta partida
            self.EnemigosGroup.add(enemy)
            self.rect = enemy.imageEnemigo.get_rect()  # rectángulo Sprite Player
            # Asignar grupo de paredes al enemigo para que pueda consultarlo
            enemy.MazeInfo = self.maze.MazeLaberinto
            enemy.conexiones = self.conexiones  # Paso las conexiones que van a liberar mucho trabajo de computación
            enemy.pasarConexionesIA()

        logging.info('Plot Enemigo')

        logging.info('Pintar Jefe Enemigo')
        if self.JefeEnemigo.vida > 0:
            self.EnemigosGroup.add(self.JefeEnemigo)
        self.rect = self.JefeEnemigo.imageJefeEnemigo.get_rect()  # rectángulo Sprite Jefe Enemigo

        # Asignar grupo de paredes al Jefe Enemigo
        self.JefeEnemigo.MazeInfo = self.maze.MazeLaberinto
        self.JefeEnemigo.kia.Laberinto = self.JefeEnemigo.MazeInfo
        self.JefeEnemigo.conexiones = self.conexiones
        self.JefeEnemigo.pasarConexionesIA()

        self.floor_surf = pygame.image.load("./Resources/floor.png").convert()
        self.wall_surf = pygame.image.load("./Resources/Wall.png").convert()

        # Imágenes del efecto rojo (se calculan una sola vez).
        self.imagePlayer_roja = self.player.dibujaDañoPlayer()
        self.imageEnemigo_roja = self.enemigo.dibujaDaño(False)
        self.imageJefe_roja = self.JefeEnemigo.dibujaDaño(True)
        # self.wall_surf = pygame.image.load("./Resources/WallBricks.png").convert()

    def on_loop(self):
        self.player.update()

        # Jefe Enemigo: la IA (kia.update) y el movimiento se ejecutan en updateJefe() al
        # pasar por el centro de cada casilla. Aquí sólo se sincroniza la información.
        # Actualizar casilla y recorrido siempre (son operaciones rápidas)
        self.JefeEnemigo.casilla = self.maze.calcularCasilla(
            self.JefeEnemigo.x + (self.JefeEnemigo.rect.width // 2),
            self.JefeEnemigo.y + (self.JefeEnemigo.rect.height // 2)
        )
        self.JefeEnemigo.kia.casillaJugador = self.maze.calcularCasilla(
            self.player.x + (self.player.rect.width // 2),
            self.player.y + (self.player.rect.height // 2)
        )
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
                x.x -= CASILLA_PIXEL
                x.rect.x = x.x
                if x.prev_x is not None:
                    x.prev_x -= CASILLA_PIXEL

            # Puertas (bisagra y rect deben moverse juntos)
            for puerta in self.maze.MazePuertas:
                puerta.x -= CASILLA_PIXEL
                puerta.pivot = (puerta.x, puerta.y)

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
                logging.debug("Desplazar Llave Puertas")
            for x in self.maze.MazeOro:
                x.rect.x -= CASILLA_PIXEL
            for x in self.maze.MazePilaHuesos:
                x.rect.x -= CASILLA_PIXEL

        for puerta in self.maze.MazePuertas:
            puerta.update()
        
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

        # Colisión entre EnEMiGos para evitar pasos entre ellos.
        #----------------------------------------------------------
        # JefeEnemigo pertenece a EnemigosGroup: filtramos autocolisión.
        colision_btEnemies = [
            s for s in pygame.sprite.spritecollide(self.JefeEnemigo, self.EnemigosGroup, False)
            if s is not self.JefeEnemigo
        ] if self.JefeEnemigo.alive() else []
        if colision_btEnemies:
            logging.debug('KOLLsiON NTRE Enemigos DETECTADA - num ELem (%s)', len(colision_btEnemies))
            if self.flagPrint_info:
                print(f'COLISION NTRE Enemigos DETECTADA - num ELem ({len(colision_btEnemies)})')
 
            self.JefeEnemigo.x = self.JefeEnemigo.prev_x
            self.JefeEnemigo.y = self.JefeEnemigo.prev_y
            self.JefeEnemigo.rect.x = self.JefeEnemigo.x
            self.JefeEnemigo.rect.y = self.JefeEnemigo.y
 
            for cl in colision_btEnemies:
                logging.info(f'ENEMIGO colisionó con JeFE NeMesis')

        # Colisión del jugador con ENEMIGOS
        #----------------------------------------------------------
        colision_playerNemesis = pygame.sprite.spritecollide(self.player, self.EnemigosGroup, False)
        if colision_playerNemesis:
            logging.debug("KOL Ntre player y Enemigo.")
            # Pintar Enemigo y el player
            self.tiempo_rojo = pygame.time.get_ticks()
            self.efecto_rojo = True
            self.impactoPlayer = True

            # El contacto hiere al jugador (el jefe hace más daño).
            self.herirJugador(DANO_JEFE if self.JefeEnemigo in colision_playerNemesis else DANO_ENEMIGO)

            # Enemigo es Jefe Enemigo (sólo si sigue vivo: está en EnemigosGroup).
            if self.JefeEnemigo in colision_playerNemesis:
                logging.debug("¡C O L I SS E U M !")
                self.impactoJefeEnemigo = True

                self.bocadillo_timer = 180
                self.flagPintarBocadilloTexto = True
                self.textoBocadillo = "Hay un INTRUSO !! Venid"

                Kfinal = self.maze.calcularCasilla(
                    self.player.x + (self.player.rect.width // 2),
                    self.player.y + (self.player.rect.height // 2)
                )
                for nemesis in self.EnemigosGroup:
                    Kinicio = self.maze.calcularCasilla(
                        nemesis.x + (nemesis.rect.width // 2),
                        nemesis.y + (nemesis.rect.height // 2)
                    )
                    nemesis.kia.playerDetectado = True
                    nemesis.kia.casillaJugador = Kfinal
                    nemesis.kia.path = nemesis.kia.calcular_camino_BFS(Kinicio, Kfinal)

            else:
                if colision_playerNemesis:
                    logging.debug('COLISION PLAYER con ENEMIGO - num ELem (%s)', len(colision_playerNemesis))
                    if self.flagPrint_info:
                        print(f'COLISION PLAYER con ENEMIGO - num ELem ({len(colision_playerNemesis)})')

                    self.player.x = self.player.prev_x
                    self.player.y = self.player.prev_y

                    self.impactoEnemigo = True
                    self.enemigoImpactado = colision_playerNemesis[0]

                    self.bocadillo_timer = 180
                    self.flagPintarBocadilloTexto = True
                    self.textoBocadillo = "INTRUSO encontrado !! Jefe aquí !!!"

                    logging.info("PLAYER ha activado alerta del Jefe Enemigo")

                    Kinicio = self.maze.calcularCasilla(
                        self.JefeEnemigo.x + (self.JefeEnemigo.rect.width // 2),
                        self.JefeEnemigo.y + (self.JefeEnemigo.rect.height // 2)
                    )
                    Kfinal = self.maze.calcularCasilla(
                        self.player.x + (self.player.rect.width // 2),
                        self.player.y + (self.player.rect.height // 2)
                    )

                    self.JefeEnemigo.kia.playerDetectado = True
                    self.JefeEnemigo.kia.path = self.JefeEnemigo.kia.calcular_camino_BFS(
                        Kinicio,
                        Kfinal
                    )
                    self.ia_necesita_update = True

                    for enemigo_tocado in colision_playerNemesis:
                        logging.info(
                            "PLAYER colisionó con ENEMIGO en (%s, %s)",
                            enemigo_tocado.x,
                            enemigo_tocado.y
                        )

        # Colisión del jugador con Puerta
        #----------------------------------------
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
        #----------------------------------------
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
                
                if nemesis.isJefeEnemigo:
                    if self.flagPrint_info:
                        print(
                            f"Colision Jefe Enemigo con PARED --> "
                            f"{self.maze.calcularCasilla(nemesis.x + (nemesis.rect.width // 2), nemesis.y + (nemesis.rect.height // 2))} !!!"
                        )
                    nemesis.detectarColision()
                    # self.bocadillo_timer = 180 
                    # self.flagPintarBocadilloTexto = True
                    # self.textoBocadillo = "ChoKado Pared!"

                    for pared in paredes:
                        if nemesis.rect.colliderect(pared.rect):
                            if nemesis.rect.x < 0:
                                if self.flagPrint_ColisionInfo:
                                    print("Colisión por IZQUIERDA")
                            elif nemesis.rect.x > 0:
                                if self.flagPrint_ColisionInfo:
                                    print("Colisión por DERECHA")

                            if nemesis.rect.y > 0:
                                if self.flagPrint_ColisionInfo:
                                    print("Colisión por ABAJO") 
                            elif nemesis.rect.y < 0:
                                if self.flagPrint_ColisionInfo:
                                    print("Colisión por ARRIBA")

                    # Recolocar al jefe en el centro de la casilla segura anterior.
                    casilla_segura = MazeLab.Maze.calcularCasilla(
                        nemesis.prev_x + (nemesis.rect.width // 2),
                        nemesis.prev_y + (nemesis.rect.height // 2)
                    )
                    centro = MazeLab.Maze.centroCasilla(casilla_segura)
                    nemesis.x = centro.x - (nemesis.rect.width // 2)
                    nemesis.y = centro.y - (nemesis.rect.height // 2)
                    nemesis.rect.x = nemesis.x
                    nemesis.rect.y = nemesis.y
                    nemesis.casilla = casilla_segura
                    nemesis.kia.casilla = casilla_segura
                    nemesis.kia.definirPosicion(
                        nemesis.x + (nemesis.rect.width // 2),
                        nemesis.y + (nemesis.rect.height // 2)
                    )
                    nemesis.kia.colisionParedes = True
                    self.ia_necesita_update = True

                # Revertir y cambiar dirección solo del enemigo que colisiona
                if hasattr(nemesis, 'revertir_movimiento') and not nemesis.isJefeEnemigo:
                    #print("    Dentro Reventir MOV")
                    nemesis.revertir_movimiento()
                    

                if hasattr(nemesis, 'cambiar_direccion'):
                    #print("Dentro Cambiar DIR")
                    nemesis.cambiar_direccion()

        # Colisión de ENemigos con Puerta
        colision_enemigosPuerta = pygame.sprite.groupcollide(self.EnemigosGroup, self.maze.MazePuertas, False, False)
        if colision_enemigosPuerta:
            logging.debug('COLISION Enemigo con Puerta DETECTADA - num ELem (%s)', len(colision_enemigosPuerta))
            # Opcional: procesar cada enemigo que colisionó
            for enemigo, puertas in colision_enemigosPuerta.items():
                logging.debug('Enemigo en (%s, %s) colisionó con %s puertas', enemigo.x, enemigo.y, len(puertas))

                # Revertir y cambiar dirección solo del enemigo que colisiona
                if hasattr(enemigo, 'revertir_movimiento'):
                    enemigo.revertir_movimiento()

                # if hasattr(enemigo, 'cambiar_direccion'):
                    # enemigo.cambiar_direccion()

        
        # Colisión de Extras Escenario con Player
        colision_PlayerConExtra = pygame.sprite.spritecollide(self.player, self.maze.MazeExtra, False)
        if colision_PlayerConExtra:
            logging.info('Huesos  IMPACTADA')
            if self.flagPrint_info:
                print('Huesos  IMPACTADA')
            self.rebuildMap()

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
            self.rebuildMap()

            # Marcar una alerta
            self.alerta_activa = True
            self.alerta_texto = "¡Has cogido la llave!"
            self.alerta_inicio_ms = pygame.time.get_ticks()

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
            self.rebuildMap() 

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
            self.rebuildMap()

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
            self.rebuildMap()

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
            self.estadisticas.registrarHuesos(1)

            # Marcar los huesos como cogidos ANTES de repintar, para que no se vuelvan a crear.
            for cpcE in colision_PlayerConHueso:
                logging.info(f'Hueso Sólo tocado')
                self.casillaObjetosTocados.add(self.maze.calcularCasilla(cpcE.rect.x, cpcE.rect.y))
                cpcE.kill()
            self.rebuildMap()

        # Colisión de Player con Oro.
        colision_PlayerConOro = pygame.sprite.spritecollide(self.player, self.maze.MazeOro, True)
        if colision_PlayerConOro:
            logging.info('Oro IMPACTADO')
            if self.flagPrint_info:
                print('Oro cogida')
            self.HeadPuntuacion.puntos += 100
            casillasOro = set()
            for cpcE in colision_PlayerConOro:
                logging.info(f'Oro tocado')
                casillasOro.add(self.maze.calcularCasilla(cpcE.rect.x, cpcE.rect.y))
                cpcE.kill()
            self.casillaObjetosTocados |= casillasOro
            # Una moneda por casilla (el mapa puede tener sprites repetidos en la misma).
            self.estadisticas.registrarOro(len(casillasOro))
            self.rebuildMap()

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
            self.estadisticas.registrarHuesos(10)
            self.rebuildMap()

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
            self.rebuildMap()

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
            # Llegar a la salida termina el nivel (salvo que el jugador acabe de morir).
            if self.resultadoPartida is None:
                self.resultadoPartida = "completado"

        # Colisión de Balas Enemigos con Paredes
        for EnemyAmmo in self.EnemigosGroup:
            colision_EnemyBalasParedes = pygame.sprite.groupcollide(EnemyAmmo.balas, self.maze.MazeParedes, False, False)
            if colision_EnemyBalasParedes:
                logging.info('COLISION Blas Player DETECTADA %s', len(colision_EnemyBalasParedes))
                # Opcional: procesar cada enemigo que colisionó
                for muni, paredes in colision_EnemyBalasParedes.items():
                    logging.info(f'BalaEnemigo en ({muni.x}, {muni.y}) colisionó con {len(paredes)} paredes')
                    muni.kill()
        
        # Balas enemigas que alcanzan al jugador.
        if pygame.sprite.spritecollide(self.player, player.Enemigo.balas, True):
            self.herirJugador(DANO_BALA_ENEMIGA)

        # Balas del jugador que alcanzan a un enemigo (antes de chocar con la pared de detrás).
        impactos = pygame.sprite.groupcollide(self.player.balas, self.EnemigosGroup, True, False)
        for bala, enemigosTocados in impactos.items():
            enemigo = enemigosTocados[0]
            muerto = enemigo.recibirDisparo(DANO_BALA_JUGADOR)
            self.estadisticas.registrarImpacto(muerto)
            if muerto:
                logging.info("Enemigo muerto en (%s, %s)", enemigo.x, enemigo.y)
                self.HeadPuntuacion.puntos += PUNTOS_JEFE if enemigo.isJefeEnemigo else PUNTOS_ENEMIGO

        # Colisión de Balas Player con Paredes
        colision_PlayerBalasConParedes = pygame.sprite.groupcollide(self.player.balas, self.maze.MazeParedes, False, False)
        if colision_PlayerBalasConParedes:
            logging.info('COLISION Enemigo DETECTADA %s', len(colision_PlayerBalasConParedes))
            # Opcional: procesar cada enemigo que colisionó
            for muni, paredes in colision_PlayerBalasConParedes.items():
                logging.info(f'Bala Player en ({muni.x}, {muni.y}) colisionó con {len(paredes)} paredes')
                muni.kill()
    
    # Repinto el Laberinto
    def rebuildMap(self):
       self.map_surface.fill((0,0,0))
    
       self.maze.draw(
           self.map_surface,
           self.floor_surf,
           self.wall_surf,
           self.casillaObjetosTocados
       )
    
    # on RENDER
    #--------------------
    def on_render(self):
        if self.pause == False:
           # SOLO si cambió el mapa
            if self.rebuild_map:
                self.rebuildMap()
                self.rebuild_map = False
            
            # Dibujar mapa ya preparado
            self.pantalla.blit(self.map_surface, (0,0))
            
            for puerta in self.maze.MazePuertas:
                puerta.draw(self.pantalla)

            if self.flagDebugEnemigos:
                self.maze.pintarDetallesCasillaEnemigo(self.pantalla)

            if self.flagExplosion and self.explosion_timer > 0:
                self.explosion_timer -= 1
                self.grupo_explosiones.update()
                self.grupo_explosiones.draw(self.pantalla)

                if self.explosion_timer <= 0:
                    self.flagExplosion = False

            if self.flagHumo and self.humo_timer > 0:
                self.humo_timer -= 1
                self.grupo_humo.update()
                self.grupo_humo.draw(self.pantalla)

                if self.humo_timer <= 0:
                    self.flagHumo = False

            if self.iteracion == 35:
               self.iteracion = 0

            # Parte bocadillo de Texto.
            if self.flagPintarBocadilloTexto and self.bocadillo_timer != 0:
                self.bocadillo_timer -= 1
                if self.impactoEnemigo:
                    self.JefeEnemigo.bocadilloTexto(self.pantalla, self.textoBocadillo, self.enemigoImpactado.rect.centerx, self.enemigoImpactado.rect.top, 255)
                elif self.impactoJefeEnemigo:
                    self.JefeEnemigo.bocadilloTexto(self.pantalla, self.textoBocadillo, self.JefeEnemigo.rect.centerx, self.JefeEnemigo.rect.top, 255)

            # Aquí busco lugar suelo para Jugador
            # Llamada a la IA
            if self.flagInit == True:
                self.flagInit = False
                if self.flagPrint_info:
                    print("Casilla Inicial Jugador: ", self.maze.posicionInitJugador)
                self.player.casilla = self.maze.posicionInitJugador    
                pos = MazeLab.Maze.calcularPixelPorCasilla(self.player.casilla)
                self.player.x = pos.x
                self.player.y = pos.y
                self.player.guardarPosicionPrevia()  # si no, una colisión lo devolvería a (23, 23)
                self.pantalla.blit(self._jugador, (self.player.x, self.player.y))
            else:
                self.pantalla.blit(self._jugador, (self.player.x, self.player.y))
            
            if self.pintaRectángulos == True:
                pygame.draw.rect(self.pantalla, (0, 255, 0), self.player.rect, 2)
 
            if self.flagPrint_info:
                print(f"Casillas con puerta (visible): ", len(self.maze.MazePuertas))

            # Aquí busco lugar suelo para Enemigo y Jefe Enemigo.
            # logging.debug("Pintamos los enemigos.")  # Comentado para mejorar rendimiento
            for i, enemy in enumerate(self.enemigosArray):
                if not enemy.alive():
                    continue  # muerto
                if(enemy.isJefeEnemigo):
                    if self.flagPrint_info:
                        print('---Posición DRAW LORD: ',self.JefeEnemigo.x, self.JefeEnemigo.y)
                    self.pantalla.blit(self._JefeEnemigo, (self.JefeEnemigo.x, self.JefeEnemigo.y))
                else:
                    if self.flagPrint_info:
                        print('---Posición DRAW ENEMIGO: ',i, enemy.x, enemy.y)
                    self.pantalla.blit(self._enemigo, (enemy.x, enemy.y))
                    if self.pintaRectángulos == True:
                        pygame.draw.rect(self.pantalla, (255, 0, 0), enemy.rect, 2)

            # Jefe Enemigo + VISIÓN (si sigue vivo)
            # logging.debug('Pintamos el JEFE enemigo.') 
            jefeVivo = self.JefeEnemigo.alive()
            if jefeVivo:
                self.pantalla.blit(self.JefeEnemigo.imageJefeEnemigo, (self.JefeEnemigo.x, self.JefeEnemigo.y))
            if jefeVivo and self.pintaRectángulos == True:
                pygame.draw.rect(self.pantalla, (0, 0, 255), self.JefeEnemigo.rect, 2)
            # VISION
            if jefeVivo and self.visionEnemigos == True:
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
 
                    self.JefeEnemigo.bocadilloTexto(self.pantalla, "¡ ALARMA !", self.JefeEnemigo.rect.centerx, self.JefeEnemigo.rect.top, alphaBTexto)
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

            # Nivel oscuro: la linterna sigue la dirección del jugador y no atraviesa
            # paredes, enemigos ni puertas.
            if self.linterna is not None:
                self.linterna.apuntar(self.player.orientacion)
                obstaculos = [s.rect for s in self.maze.MazeParedes]
                obstaculos += [s.rect for s in self.EnemigosGroup]
                obstaculos += [p.rect for p in self.maze.MazePuertas]
                self.linterna.dibujar(self.pantalla, self.player.rect.center, obstaculos)

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

        self.now = pygame.time.get_ticks()

        if self.alerta_activa:
            # Si han pasado más de 3 segundos, la desactivamos
            if self.now - self.alerta_inicio_ms > self.alerta_duracion_ms:
                self.alerta_activa = False
            else:
                # --- Dibujar la alerta por encima de todo ---
                # Crear texto
                texto_surface = self.font_alerta.render(self.alerta_texto, True, (255, 255, 255))

                # Fondo semi-transparente
                ancho, alto = self.pantalla.get_size()
                overlay = pygame.Surface((ancho, 60), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))  # negro con alpha 180

                # Posicionar en la parte superior (por ejemplo)
                y = 20
                x_texto = (ancho - texto_surface.get_width()) // 2

                self.pantalla.blit(overlay, (0, y - 10))
                self.pantalla.blit(texto_surface, (x_texto, y))

        # Aplicar efecto rojo y vibración cuando jugador y Enemigo/s
        if self.efecto_rojo:
            ahora = pygame.time.get_ticks()

            if ahora - self.tiempo_rojo < 2000:
                if (ahora // 100) % 2:
                    if self.impactoPlayer:
                        self.pantalla.blit(self.imagePlayer_roja, (self.player.x, self.player.y))
                    if self.impactoEnemigo:
                        self.pantalla.blit(self.imageEnemigo_roja, (self.enemigoImpactado.x, self.enemigoImpactado.y))
                    if self.impactoJefeEnemigo:
                        self.pantalla.blit(self.imageJefe_roja, (self.JefeEnemigo.x, self.JefeEnemigo.y))
                else:
                    if self.impactoPlayer:
                        self.pantalla.blit(self.player.image, (self.player.x, self.player.y))
                    if self.impactoEnemigo:
                        self.pantalla.blit(self.enemigoImpactado.imageEnemigo, (self.enemigoImpactado.x, self.enemigoImpactado.y))
                    if self.impactoJefeEnemigo:
                        self.pantalla.blit(self.enemigo.imageJefeEnemigo, (self.JefeEnemigo.x, self.JefeEnemigo.y))
            else:
                self.efecto_rojo = False

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
                        if self.player.disparo():
                            self.estadisticas.registrarDisparo()
                    if event.key == pygame.K_RETURN:
                        logging.info('¡¡¡ INTRO !!!')
                        self.JefeEnemigo.alarma = True
                        self.JefeEnemigo.restarRelojBocadilloTexto()
                        for x in self.EnemigosGroup:
                            x.disparo()
                    if event.key == pygame.K_c:
                        if self.flagPrint_info:
                            print("Tecla C presionada")
                        if self.pintaRectángulos == True:
                           self.pintaRectángulos = False
                        else:
                            self.pintaRectángulos = True 
                    if event.key == pygame.K_x:
                        logging.info('Tecla X presionada')
                        # Defino una explosion
                        explosion = MazeLab.Explosion(400, 300)
                        self.grupo_explosiones.add(explosion)
                        self.flagExplosion = True
                        self.explosion_timer = 150
                    if event.key == pygame.K_d:
                        logging.info('Tecla D presionada')
                        for puerta in self.maze.MazePuertas:
                            puerta.abierta = not puerta.abierta
                    if event.key == pygame.K_k:
                        logging.info('Tecla K presionada')
                        if MazeLab.Maze.pintaKasillaNumSuelo:
                            MazeLab.Maze.pintaKasillaNumSuelo = False
                            self.rebuildMap()
                        else:
                            MazeLab.Maze.pintaKasillaNumSuelo = True
                            self.rebuildMap()
                    if event.key == pygame.K_v:
                        logging.info('Tecla V presionada')
                        if self.pintaVision == True:
                           self.pintaVision = False
                        else:
                            self.pintaVision = True 
                    if event.key == pygame.K_z:
                        logging.info('Tecla Z apretada')
                        smoke = MazeLab.Smoke(200, 600, 210)
                        self.grupo_humo.add(smoke)
                        self.flagHumo= True
                        self.humo_timer = 150
                        self.rebuildMap()
                    if event.key == pygame.K_s:
                        logging.info('Tecla S apretada')
                        if self.Sound.reproducirMusica == False:
                           self.canalmusicaFondo = self.Sound.musica.play()  # 🔊 Reproduce el sonido una vez
                           # musicaFondo.play(loops=-1)  # Si quieres que se repita indefinidamente
                           self.Sound.musica.set_volume(0.7)
                           self.Sound.reproducirMusica = True
                        else:
                            self.Sound.reproducirMusica = False
                            self.canalmusicaFondo.stop()
                    if event.key == pygame.K_p:
                        self.pause = not self.pause
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

            # Muerte del jugador o salida alcanzada: pantalla final con las estadísticas.
            if self.resultadoPartida is not None:
                self.terminarPartida(self.resultadoPartida == "completado")
            self.clock.tick(FPS)  # <--- Aquí, después de renderizar

        self.on_cleanup()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    logging.basicConfig(filename="./log/squidcastle.log", level=logging.WARNING,
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
        logging.info("JSON File data = %s", data)
    
    except FileNotFoundError:
        logging.error("Error: The file 'Level2.json' was not found.")

    except json.JSONDecodeError:
        logging.error("Error: Failed to decode JSON from the file.")

    try:
        parser = LevelParser("./Levels")
        level_data = parser.load_by_name("Level_2.json")
        logging.info("Level loaded: %s %s %s", os.path.basename(level_data.path), level_data.width, level_data.height)
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
