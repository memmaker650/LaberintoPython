from pygame.locals import *
import pygame
import time
import random
import logging

# Dimensiones de la pantalla.
display_width = 800
display_height = 600

# definición colores
black = (0,0,0)
white = (255,255,255)
red = (200, 0, 0)
green = (0, 200, 0)

bright_red = (255, 0, 0)
bright_green = (0, 255, 0)

block_color = (53, 115, 255)

#defino el reloj del juego.
clock = pygame.time.Clock()

#gameDisplay = pygame.display.set_mode((display_width,display_height))

def text_objects(text, font):
    textSurface = font.render(text, True, black)
    return textSurface, textSurface.get_rect()

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

    def text_objects(text, font):
        textSurface = font.render(text, True, black)
        return textSurface, textSurface.get_rect()

class Maze:
    def __init__(self):
        self.M = 26
        self.N = 26
        self.maze = [1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
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
1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,]

    def draw(self, display_surf, image_surf):
        bx = 0
        by = 0
        for i in range(0, self.M * self.N):
            #No entiendo la condición del IF.
            if self.maze[bx + (by * self.M)] == 1:
                display_surf.blit(image_surf, (bx * 32, by * 32))

            bx = bx + 1
            if bx > self.M - 1:
                bx = 0
                by = by + 1

# def button(msg,x,y,w,h,ic,ac,action=None):
#     mouse = pygame.mouse.get_pos()
#     click = pygame.mouse.get_pressed()
#
#     logging.info('Generado un botón.')
#
#     if x+w > mouse[0] > x and y+h > mouse[1] > y:
#         pygame.draw.rect(gameDisplay, ac,(x,y,w,h))
#         if click[0] == 1 and action != None:
#             action()
#     else:
#         pygame.draw.rect(gameDisplay, ic,(x,y,w,h))
#     smallText = pygame.font.SysFont("comicsansms",20)
#     textSurf, textRect = text_objects(msg, smallText)
#     textRect.center = ( (x+(w/2)), (y+(h/2)) )
#     gameDisplay.blit(textSurf, textRect)

class App:
    windowWidth = 800
    windowHeight = 600
    player = 0
    pause = False
    ejecutando = True

    logging.basicConfig(filename='../log/squidcastle.log', level=logging.DEBUG)
    logging.basicConfig(format='%(asctime)s %(message)s')
    #logging.debug('This message should go to the log file')
    logging.info('Inicio Juego.')
    #logging.warning('And this, too')

    #gameIcon = pygame.image.load('carIcon.png')
    #pygame.display.set_icon(gameIcon)

    def __init__(self):
        self._display_surf = None
        self._image_surf = None
        self._block_surf = None
        self.player = Player()
        self.maze = Maze()

    # def game_intro(self):
    #     intro = True
    #
    #     while intro:
    #         for event in pygame.event.get():
    #             # print(event)
    #             if event.type == pygame.QUIT:
    #                 pygame.quit()
    #                 quit()
    #
    #         gameDisplay.fill(white)
    #         largeText = pygame.font.SysFont("comicsansms", 115)
    #         TextSurf, TextRect = text_objects("A bit Racey", largeText)
    #         TextRect.center = ((display_width / 2), (display_height / 2))
    #         gameDisplay.blit(TextSurf, TextRect)
    #
    #         button("GO!", 150, 450, 100, 50, green, bright_green, self.on_loop)
    #         button("Quit", 550, 450, 100, 50, red, bright_red, self.quitgame())
    #
    #         pygame.display.update()
    #         clock.tick(15)

    # def unpause(self):
    #     self.pause = False
    #
    # def paused(self):
    #     largeText = pygame.font.SysFont("comicsansms", 115)
    #     TextSurf, TextRect = text_objects("Paused", largeText)
    #     TextRect.center = ((display_width // 2), (display_height // 2))
    #     gameDisplay.blit(TextSurf, TextRect)
    #     logging.info('Juego Pausado.')
    #
    #     while self.pause:
    #         for event in pygame.event.get():
    #             # print(event)
    #             if event.type == pygame.QUIT:
    #                 pygame.quit()
    #                 quit()
    #
    #         # gameDisplay.fill(white)
    #
    #         button("Continue", 150, 450, 100, 50, green, bright_green, self.unpause)
    #         button("Quit", 550, 450, 100, 50, red, bright_red, self.quitgame())
    #
    #         pygame.display.update()
    #         clock.tick(15)

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode((self.windowWidth, self.windowHeight), pygame.HWSURFACE)

        pygame.display.set_caption('Laberinto SquidCastle 2020, Pandemia.')
        self.ejecutando = True
        self._image_surf = pygame.image.load("../Resources/player.png").convert()
        self._block_surf = pygame.image.load("../Resources/floor.png").convert()

    def on_event(self, event):
        if event.type == QUIT:
            self.ejecutando = False

    def on_loop(self):
        pass

    def on_render(self):
        logging.info('Pintando.')
        self._display_surf.fill((0, 0, 0))
        logging.info('Pintar al personaje Jugador.')
        self._display_surf.blit(self._image_surf, (self.player.x, self.player.y))
        logging.info('Pintamos el laberinto..')
        self.maze.draw(self._display_surf, self._block_surf)
        pygame.display.flip()

    def quitgame(self):
        pygame.quit()
        logging.info('Cerrando.')
        quit()

    def on_execute(self):
        if self.on_init() == False:
            self.ejecutando = False

        while (self.pause):
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

            # if (keys[K_p]):
            #     self.pause = True

            if (keys[K_ESCAPE]):
                self.quitgame()

            self.on_loop()
            self.on_render()

        #self.quitgame()


if __name__ == "__main__":
    theApp = App()
    theApp.on_execute()
