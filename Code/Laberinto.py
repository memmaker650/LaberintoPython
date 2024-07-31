import mates
import player

import logging
import statistics
import random
import os
import sys


import pygame
from pygame.locals import *
import sqlite3

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
    rectSuelo = pygame.sprite.Sprite
    MazeSprite = pygame.sprite.Group

    def addText(self, texto, x, y):
        self.font = pygame.font.SysFont('Arial', 25)
        self.font.render(texto, True, (255, 0, 0))

    def __init__(self):
        self.M = NUM_CASILLAS
        self.N = NUM_CASILLAS
        self.maze = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
                     0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
                     0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,
                     0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0,
                     0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0,
                     0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0,
                     0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0,
                     0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0,
                     0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0,
                     0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0,
                     0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0,
                     0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0,
                     0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0,
                     0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0,
                     0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
                     0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
                     0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
                     0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,
                     0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
                     0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
                     0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    def draw(self, display_surf, image_surf):
        bx = 0
        by = 0
        for i in range(0, self.M * self.N):
            if self.maze[bx + (by * self.M)] == 1:
                #pygame.sprite.Sprite.__init__(self)
                display_surf.blit(image_surf, (bx * CASILLA_PIXEL, by * CASILLA_PIXEL))
                self.rect = image_surf.get_rect()
            else:
                self.rectSuelo.image = pygame.Surface([CASILLA_PIXEL, CASILLA_PIXEL])
                self.rectSuelo.rect = self.rectSuelo.image.get_rect()
                self.addText(str(i), self.rectSuelo.rect.centerx, self.rectSuelo.rect.centery)
                self.MazeSprite.add(self.rectSuelo)
                #pygame.draw.rect(self.pantalla, ROJO, self.rectSuelo)

            bx = bx + 1
            if bx > self.M - 1:
                bx = 0
                by = by + 1

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
        posicion.y = (Casilla / 10) * CASILLA_PIXEL
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
    enemigosSprites = pygame.sprite.Group()
    visionEnemigos = bool

    salir = bool = False

    # Inicio el reloj y el Sonido.
    clock = pygame.time.Clock()
    pygame.mixer.init()

    #Definimos el icono del juego.
    gameIcon = pygame.image.load('../Resources/player.png')
    pygame.display.set_icon(gameIcon)

    def __init__(self):
        self._running = True
        self.tocaMenu = True
        self.movimiento = True
        self.pause = False
        self.pantalla = 1
        self._jugador = None
        self._enemigo = None
        self._block_surf = None
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
            self.enemigosSprites.add(self.enemigo)

        logging.info('Contenido grupo Sprites: %s', len(self.enemigosSprites))
        logging.info("Cagados todos los enemigos")

        self.JefeEnemigo.inicio(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.JefeEnemigo.casilla = Maze.calcularCasilla(self.JefeEnemigo.x, self.JefeEnemigo.y)
        # Cargamos Jefe enemigo

        self.maze = Maze()
        logging.info("Cargado el escenario")

    def verInfoEnemigos(self):
        enemy = player.Enemigo()

        for i in range(1, self.numEnemigos):
            enemy = self.enemigosArray[i]
            enemy.logPosicionEnemigo()

    def menu(self):
        color = (255, 255, 255)

        print("Dentro del Menú!!")

        # light shade of the button
        color_light = (170, 170, 170)

        # dark shade of the button
        color_dark = (100, 100, 100)

        # stores the width of the
        # screen into a variable
        width = self.pantalla.get_width()

        # stores the height of the
        # screen into a variable
        height = self.pantalla.get_height()

        # defining a font
        smallfont = pygame.font.SysFont('Corbel', 35)

        # rendering a text written in Corbel font.
        text1 = smallfont.render('Nuevo Juego', True, color)
        text2 = smallfont.render('Opciones', True, color)
        text4 = smallfont.render('Cargar Partida', True, color)
        text3 = smallfont.render('salir', True, color)

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
                        print ("Opciones del juego, pulsada.")
                        self.tocaMenu = False
                        self.on_execute()

                    # Botón 4 - Salir del juego
                    if mates.dentroBoton(mouse,  int(width / 2), int((height / 2)) + 100, 230, 40):
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
                if mates.dentroBoton(mouse, width / 2, (height / 2) - 50, 230, 40) or mates.dentroBoton(mouse, width / 2, height / 2, 230, 40) or mates.dentroBoton(mouse,  width / 2, (height / 2) + 100, 230, 40):
                    if mates.dentroBoton(mouse, width / 2, (height / 2) - 50, 230, 40):
                        pygame.draw.rect(self.pantalla, color_light, [width / 2, (height / 2) - 50, 230, 40])

                        # Botón 2 - Cargar partida
                        if mates.dentroBoton(mouse, width / 2, height / 2, 230, 40):
                            pygame.draw.rect(self.pantalla, color_light, [int(width / 2), int(height / 2), 230, 40])

                        # Botón 3 - Opciones
                        if mates.dentroBoton(mouse, width / 2, height / 2, 230, 40):
                            pygame.draw.rect(self.pantalla, color_light, [int(width / 2), int(height / 2), 230, 40])

                        # Botón 4 - Salir del juego
                        if mates.dentroBoton(mouse, width / 2, (height / 2) + 100, 230, 40):
                            pygame.draw.rect(self.pantalla, color_light, [int(width / 2), int((height / 2)) + 200, 230, 40])

                        else:
                            pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) - 50, 230, 40])
                            pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)), 230, 40])
                            pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) + 50, 230, 40])
                            pygame.draw.rect(self.pantalla, color_dark, [int(width / 2), int((height / 2)) + 200, 230, 40])

                # superimposing the text onto our button
                self.pantalla.blit(text1, (width / 2 + 50, (height / 2) - 50))
                self.pantalla.blit(text2, (width / 2 + 50, (height / 2)))
                self.pantalla.blit(text3, (width / 2 + 50, (height / 2) + 200))
                self.pantalla.blit(text4, (width / 2 + 50, (height / 2) + 50))

                # updates the frames of the game
                pygame.display.update()

    def on_init(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((self.windowWidth, self.windowHeight), pygame.HWSURFACE)

        pygame.display.set_caption('Laberinto SquidCastle 2024, Aurora.')
        logging.info("Inicio del juego.")

        logging.info("Pintamos el menú del juego.")
        if self.tocaMenu:
            self.menu()

        logging.info("Empezamos un juego nuevo.")
        self._running = True
        self.player.pintarJugador()
        self._jugador = self.player.image
        self.rect = self._jugador.get_rect()  # rectángulo Sprite Player
        logging.info("Pintado Jugador")

        self.enemigo.pintarEnemigo()
        self._enemigo = self.enemigo.image
        print(len(self.enemigosArray))
        i = 0
        for i in range(0, self.numEnemigos):
            enemy = self.enemigosArray[i]
            enemy.pintarEnemigo()
            self.rect = enemy.image.get_rect()  # rectángulo Sprite Player

        logging.info('Plot Enemigo')

        logging.info('Pintar Jefe Enemigo')
        self.JefeEnemigo.pintarJefeEnemigo()
        self.rect = self.JefeEnemigo.image.get_rect()  # rectángulo Sprite Jefe Enemigo
        self.JefeEnemigo.vision(self.JefeEnemigo.image.get_rect().center)

        self._block_surf = pygame.image.load("../Resources/floor.png").convert()

    def on_event(self, event):
        if event.type == QUIT:
            logging.debug("ESCAPE pulsado.")
            self._running = False
            self.salir = True
            pygame.quit()

        if event.type == pygame.QUIT:
            logging.debug("X ventana pulsada !!")
            self._running = False
            self.salir = True
            pygame.quit()

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
        # colision = pygame.sprite.spritecollide(self.maze.MazeSprite, self.enemigosSprites, False, False)
        # if colision:
        #     logging.info('COLISION DETECTADA')
        #     self.enemigo.image = pygame.image.load("principal/explosion.png")
        #     self.enemigo.velocidad_y += 20
        # else:
        #     self.enemigo.kill()
        #pygame.sprite.groupcollide(self.maze.MazeSprite, self.JefeEnemigo, False, False)
        pass

    def on_render(self):
        self.pantalla.fill((0, 0, 0))

        if self.pause == False:
            #Defino el laberinto
            logging.debug("Pintamos laberinto.")
            self.maze.draw(self.pantalla, self._block_surf)
            #self.maze.MazeSprite.draw(self.pantalla, self._block_surf)

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

            # Aquí busco lugar suelo para Enemigo
            logging.debug("Pintamos los enemigos.")
            #self.pantalla.blit(self._enemigo_surf, (self.enemigo.x, self.enemigo.y))
            i = 0
            for i in range(0, self.numEnemigos):
                self.enemigo = self.enemigosArray[i]
                self.pantalla.blit(self._enemigo, (self.enemigo.x, self.enemigo.y))

                if (self.enemigo.flagDisparo == True):
                    self.pantalla.blit(self.enemigo.bala.image, (self.enemigo.bala.x, self.enemigo.bala.y))

            # Jefe Enemigo
            logging.debug('Pintamos el JEFE enemigo.')
            self.pantalla.blit(self.JefeEnemigo.image, (self.JefeEnemigo.x, self.JefeEnemigo.y))

            if (self.visionEnemigos == True):
                self.pantalla.blit(self.JefeEnemigo.visionImage, (self.JefeEnemigo.x, self.JefeEnemigo.y - 40))

            # Pintar disparos del Player
            if(self.player.flagDisparo == True):
                self.pantalla.blit(self.player.bala.image, (self.player.bala.x, self.player.bala.y))

            # Pintar disparos de Jefe Enemigo
            if (self.JefeEnemigo.flagDisparo == True):
                self.pantalla.blit(self.self.JefeEnemigo.bala.image, (self.JefeEnemigo.bala.x, self.JefeEnemigo.bala.y))

        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        # clock.tick(60)

        print("Dentro de on_execute.")

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
                        logging.info('¡¡¡ Pulsado cursor DERECHO !!!')
                        self.player.moveRight()
                    if event.key == pygame.K_LEFT:
                        self.movimiento = True
                        logging.info('¡¡¡ Pulsado cursor IZQUIERDO !!!')
                        self.player.moveLeft()
                    if event.key == pygame.K_UP:
                        self.movimiento = True
                        logging.info('¡¡¡ Pulsado cursor ARRIBA !!!')
                        self.player.moveUp()
                    if event.key == pygame.K_DOWN:
                        self.movimiento = True
                        logging.info('¡¡¡ Pulsado cursor ABAJO !!!')
                        self.player.moveDown()
                    if event.key == pygame.K_SPACE:
                        logging.info('¡¡¡ BARRA ESPACIADORA !!!')
                        self.player.disparo()
                    if event.key == pygame.K_p:
                        if self.Pause == False:
                            self.pause = True
                        else:
                            self.pause = False
                        logging.info('PAUSA PULSADA.')

                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_RIGHT:
                        self.movimiento = True
                        logging.info('¡¡¡ SOLtado cursor DERECHO !!!')
                        self.player.stop()

                    if event.key == pygame.K_LEFT:
                        self.movimiento = True
                        logging.info('¡¡¡ SOLtado cursor IZQUIERDO !!!')
                        self.player.stop()

                    if event.key == pygame.K_UP:
                        self.movimiento = True
                        logging.info('¡¡¡ SOLtado cursor ARRIBA !!!')
                        self.player.stop()

                    if event.key == pygame.K_DOWN:
                        self.movimiento = True
                        logging.info('¡¡¡ SOLtado cursor ABAJO !!!')
                        self.player.stop()
            self.on_loop()
            self.on_render()

        self.on_cleanup()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":

    logging.basicConfig(filename="../log/squidcastle.log", level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    logging.warning("Inicio LaberintoPy!!!")

    sqliteConnection = sqlite3.connect("../DB/tutorial.db")
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

    # App principal
    theApp = App()
    theApp.on_execute()

    #Cerramos base de datos
    sqliteConnection.close()
    logging.info("The SQLite connection is closed")

    logging.info("JUEGO ¡¡ Se acabo !!")
