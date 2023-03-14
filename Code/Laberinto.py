import mates

import logging
import os
import sys

import pygame
from pygame.locals import *

# -----------
# Constantes
# -----------

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
IMG_DIR = "Resources"
SONIDO_DIR = "Resources/Sonidos"


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


class Player:
    x = 44
    y = 44
    speed = 1

    def moveRight(self):
        self.x = self.x + self.speed

    def moveLeft(self):
        self.x = self.x - self.speed

    def moveUp(self):
        self.y = self.y - self.speed

    def moveDown(self):
        self.y = self.y + self.speed


class Enemigo:
    x = 44
    y = 44
    speed = 1

    def moveRight(self):
        self.x = self.x + self.speed

    def moveLeft(self):
        self.x = self.x - self.speed

    def moveUp(self):
        self.y = self.y - self.speed

    def moveDown(self):
        self.y = self.y + self.speed


class Maze:
    def __init__(self):
        self.M = 25
        self.N = 25
        self.maze = [1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0,
                     1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1,
                     1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1,
                     0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1,
                     1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1,
                     1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0,
                     1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1,
                     1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1,
                     1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1,
                     1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1,
                     1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,
                     1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0,
                     1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, ]

    def draw(self, display_surf, image_surf):
        bx = 0
        by = 0
        for i in range(0, self.M * self.N):
            if self.maze[bx + (by * self.M)] == 1:
                #pygame.sprite.Sprite.__init__(self)
                display_surf.blit(image_surf, (bx * 32, by * 32))
                #self.rect = self.image.get_rect()

            bx = bx + 1
            if bx > self.M - 1:
                bx = 0
                by = by + 1

    # def calcularCasilla(self):

    def esAlcanzable(self, x, y):
        if self.maze[x + (y * self.M)] == 1:
            return False
        else:
            return True

class App:
    windowWidth = 800
    windowHeight = 600
    player = 0

    # Inicio el reloj y el Sonido.
    clock = pygame.time.Clock()
    pygame.mixer.init()

    # gameIcon = pygame.image.load('carIcon.png')
    # pygame.display.set_icon(gameIcon)

    def __init__(self):
        self._running = True
        self.tocaMenu = True
        self.pause = False
        self.pantalla = 1
        self._jugador = None
        self._enemigo_surf = None
        self._block_surf = None
        self.player = Player()
        self.enemigo = Enemigo()
        self.maze = Maze()

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
        text3 = smallfont.render('quit', True, color)

        while True:

            for ev in pygame.event.get():

                if ev.type == pygame.QUIT:
                    pygame.quit()

                # Chequeamos click del ratón
                if ev.type == pygame.MOUSEBUTTONDOWN:

                    # Chequeamos si click en algún botón
                    # Botón 1 - Nuevo Juego
                    if mates.dentroBoton(mouse, int(width / 2), int((height / 2)) - 50, 230, 40):
                        self.tocaMenu = False
                        self.on_execute()

                    # Botón 2 - Cargar partida


                    # Botón 3 - Opciones
                    if mates.dentroBoton(mouse, int(width / 2), int(height / 2), 230, 40):
                        print ("Opciones del juego, pulsada.")
                        self.tocaMenu = False
                        self.on_execute()

                    # Botón 4 - Salir del juego
                    if mates.dentroBoton(mouse,  int(width / 2), int((height / 2)) + 100, 230, 40):
                        pygame.quit()


            # fills the screen with a color
            self._display_surf.fill((60, 25, 60))

            # stores the (x,y) coordinates into
            # the variable as a tuple
            mouse = pygame.mouse.get_pos()

            # Compruebo si el ratón está dentro de botón.
            # width / 2 <= mouse[0] <= width / 2 + 140 and height / 2 <= mouse[1] <= height / 2 + 40:
            if mates.dentroBoton(mouse, width / 2, (height / 2) - 50, 230, 40) or mates.dentroBoton(mouse, width / 2, height / 2, 230, 40) or mates.dentroBoton(mouse,  width / 2, (height / 2) + 100, 230, 40):
                if mates.dentroBoton(mouse, width / 2, (height / 2) - 50, 230, 40):
                    pygame.draw.rect(self._display_surf, color_light, [width / 2, (height / 2) - 50, 230, 40])

                # Botón 2 - Cargar partida

                # Botón 3 - Opciones
                if mates.dentroBoton(mouse, width / 2, height / 2, 230, 40):
                    pygame.draw.rect(self._display_surf, color_light, [int(width / 2), int(height / 2), 230, 40])

                # Botón 4 - Salir del juego
                if mates.dentroBoton(mouse, width / 2, (height / 2) + 100, 230, 40):
                    pygame.draw.rect(self._display_surf, color_light, [int(width / 2), int((height / 2))+100, 230, 40])

            else:
                pygame.draw.rect(self._display_surf, color_dark, [int(width / 2), int((height / 2)) - 50, 230, 40])
                pygame.draw.rect(self._display_surf, color_dark, [int(width / 2), int((height / 2)), 230, 40])
                pygame.draw.rect(self._display_surf, color_dark, [int(width / 2), int((height / 2)) + 100, 230, 40])

            # superimposing the text onto our button
            self._display_surf.blit(text1, (width / 2 + 50, (height / 2) - 50))
            self._display_surf.blit(text2, (width / 2 + 50, (height / 2)))
            self._display_surf.blit(text3, (width / 2 + 50, (height / 2) + 100))

            # updates the frames of the game
            pygame.display.update()

    def on_init(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((self.windowWidth, self.windowHeight), pygame.HWSURFACE)

        pygame.display.set_caption('Laberinto SquidCastle 2020, Pandemia.')
        logging.info("Inicio del juego.")
        #if self.tocaMenu:
            #self.menu()

        self._running = True
        self._jugador = load_image("player_modif.png", IMG_DIR, alpha=True)
        #pygame.sprite.Sprite.__init__(self._jugador) # Sprite Player
        self._jugador = pygame.transform.scale(self._jugador, (32, 32))
        #self.rect = self.image.get_rect()  # rectángulo Sprite Player
        logging.info("Pintado Jugador")
        self._enemigo_surf = load_image("wilber-eeek.png", IMG_DIR, alpha=True)
        #pygame.sprite.Sprite.__init__(self._jugador)
        self._enemigo_surf = pygame.transform.scale(self._enemigo_surf, (32, 32))
        #self.rect = self.image.get_rect()  # rectángulo Sprite Player
        logging.info('Plot Enemigo')

        self._block_surf = pygame.image.load("../Resources/floor.png").convert()

        #pygame.key.set_repeat(1, 25)  # Activa repeticion de teclas


    def on_event(self, event):
        if event.type == QUIT:
            self._running = False

    def on_loop(self):
        pass

    def on_render(self):
        self.pantalla.fill((0, 0, 0))
        # Aquí defino imagen con clase Jugador
        self.pantalla.blit(self._jugador, (self.player.x, self.player.y))
        # Aquí defino imagen con clase Enemigo
        self.pantalla.blit(self._enemigo_surf, (self.enemigo.x, self.enemigo.y))
        # Defino el laberinto
        self.maze.draw(self.pantalla, self._block_surf)
        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        # clock.tick(60)

        print("Dentro de on_execute.")

        if self.on_init() == False:
            self._running = False

        while (self._running):

            pygame.event.pump()
            keys = pygame.key.get_pressed()

            if (keys[K_RIGHT]):
                self.player.moveRight()

            if (keys[K_LEFT]):
                self.player.moveLeft()

            if (keys[K_UP]):
                self.player.moveUp()

            if (keys[K_DOWN]):
                self.player.moveDown()

            if (keys[K_ESCAPE]):
                self._running = False

            if (keys[K_p]):
                self.pause = True
                logging.info('Tecla de juego pausado PULSADA.')

            self.on_loop()
            self.on_render()
        self.on_cleanup()


if __name__ == "__main__":

    logging.basicConfig(filename="../log/squidcastle.log", level=logging.DEBUG)
    logging.basicConfig(format="%(asctime)s %(message)s")
    logging.warning("Inicio Problema!!!")

    theApp = App()
    theApp.on_execute()

    logging.info("Se acabo!")
