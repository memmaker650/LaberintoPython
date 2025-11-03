from plyer import orientation
import mates
import KerberosIA

import logging
import statistics
import MazeLab
import Sonido
import random
import os
import sys

import time

import pygame
from pygame.locals import *

import pygame as pg
from pygame.math import Vector2

IMG_DIR = "Resources"

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

SCREEN_WIDTH = 864
SCREEN_HEIGHT = 1000

BIAS = 136

# Directorio de imágenes principal
carpeta_imagenes = os.path.join(IMG_DIR, "imagenes")

IMG_DIR = "./Resources"
# Especificación de la paleta de colores
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
ROJO = (255, 0, 0)
VERDE = (0, 255, 0)
AZUL = (0, 0, 255)
HC74225 = (199, 66, 37)
H61CD35 = (97, 205, 53)

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

def detectar_colision(rect1, rect2):
    if not rect1.colliderect(rect2):
        return None
    
    dx_izq = abs(rect1.right - rect2.left)
    dx_der = abs(rect1.left - rect2.right)
    dy_arr = abs(rect1.bottom - rect2.top)
    dy_aba = abs(rect1.top - rect2.bottom)
    
    min_col = min(dx_izq, dx_der, dy_arr, dy_aba)
    
    if min_col == dx_izq:
        return "izquierda"
    elif min_col == dx_der:
        return "derecha"
    elif min_col == dy_arr:
        return "arriba"
    elif min_col == dy_aba:
        return "abajo"

class Disparos(pygame.sprite.Sprite):
    x = int
    y = int
    #  0 Arriba 1 Dcha 2 Abajo 3 Izq
    orientacion = int = 4
    isPlayer = False

    def __init__(self, dx, dy, jugador, orient):
        super().__init__()
        logging.info("INIT clase DISPARO.")
        self.isPlayer = jugador
        self.orientacion = orient

        if self.isPlayer:
            self.image = load_image("disparo.png", "./Code/assets/", alpha=True)
            self.image = pygame.transform.scale(self.image, (10, 20))
            self.municion = 10
        else:
            self.image = load_image("disparoEnemigo.png", "./Code/assets/", alpha=True)
            self.image = pygame.transform.scale(self.image, (8, 18))
            self.municion = 100
        
        if self.orientacion == 1 or self.orientacion == 3:
            self.image = pygame.transform.rotate(self.image, 90)
        
        self.rect = self.image.get_rect()
        self.rect.x = dx
        self.rect.y = dy
        self.y = dy
        self.x = dx
        self.municion = 10

    def definirMunicion(self, valor):
        self.municion = valor

    def actualizarMunicion(self, valor, sentido):  # 0 restar y 1 sumar
        if (sentido == 0):
            self.municion -= valor
        elif (sentido == 1):
            self.municion += valor

    def rotarBala(self, angulo):
        return pygame.transform.rotate(self.imagen, angulo)

    def update(self):
        logging.info('Dentro UPDATE BALA.')
        if self.orientacion == 0: # Arriba
            self.rect.y -= 3
        elif self.orientacion == 1: # Derecha
            self.rect.x += 3
        elif self.orientacion == 2: # Abajo
            self.rect.y += 3
        else:                       # Izquierda
            self.rect.x -= 3

        if self.rect.x < 0:
            self.kill()
        elif self.rect.y < 0:
            self.kill()
        elif self.rect.x > SCREEN_WIDTH:
            self.kill()
        elif self.rect.y < BIAS:
            self.kill()


class Player(pygame.sprite.Sprite):
    x = 23
    y = 23
    prev_x = 23
    prev_y = 23
    casilla = 0

    vida = int

    flagDisparo = False
    orientacion = 1  # 1 arriba, 2 derecha, 3 abajo y 4 izquierda.
    speedV = 2
    speedH = 2
    image = None
    rect = None
    arma = int = 2
    municion = int = 10
    bala = Disparos
    balas = pygame.sprite.Group()
    MazeParedes = pygame.sprite.Group

    llavePuerta = bool = False
    llaveFinNivel = bool = False
    champi = bool = False
    pistola = bool = True
    granada = bool = False
    laser = bool = False

    sonidoDisparo = Sonido.Sonido()

    def __init__(self):
        logging.info("Init Player")
        super().__init__()
        self.flagDisparo = False
        self.image = load_image("player_modif.png", IMG_DIR, alpha=True)
        self.image = pygame.transform.scale(self.image, (22, 22))
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.sonidoDisparo.musica = pygame.mixer.Sound("./Resources/Sonidos/gunshot.mp3")

    def inicio(self, vx, vy):
        logging.info("Inicio Player")
        self.x = random.randint(0, vx)
        self.y = random.randint(BIAS, vy)
        self.prev_x = self.x
        self.prev_y = self.y

    def stop(self):
        self.speedH = 0
        self.speedV = 0

    def andar(self):
        if(self.speedH < 6):
            self.speedH = self.speedH + 1
        else:
            self.speedH = 2

        if (self.speedV < 6):
            self.speedV = self.speedV + 1
        else:
            self.speedH = 2

    def guardarPosicionPrevia(self):
        self.prev_x = self.x
        self.prev_y = self.y

    def moveRight(self):
        self.andar()
        self.guardarPosicionPrevia()

        self.x = self.x + self.speedH
        self.logMovimiento("Derecha", self.x, self.y)
        self.orientacion = 1

    def moveLeft(self):
        self.andar()
        self.guardarPosicionPrevia()

        self.x = self.x - self.speedH
        self.logMovimiento('Izquierda', self.x, self.y)
        self.orientacion = 3

    def moveUp(self):
        self.andar()
        self.guardarPosicionPrevia()

        self.y = self.y - self.speedV
        self.logMovimiento('Arriba', self.x, self.y)
        self.orientacion = 0

    def moveDown(self):
        self.andar()
        self.guardarPosicionPrevia()

        self.y = self.y + self.speedV
        self.logMovimiento('Abajo', self.x, self.y)
        self.orientacion = 2

    def asignarVida(self, valor):
        self.vida = valor

    def cambiarVida(self, valor):
        self.vida += valor

    def getPosicion(self):
        return self.casilla

    def logMovimiento(self, direccion, finalx, finaly):
        logging.info('Movimiento %s hasta x: %s, y %s', direccion, finalx, finaly)

    def pintarJugador(self):
        logging.info("Pintamos Jugador")

    def update(self):
        logging.debug('Dentro Update JUGADOR.')
        # Actualizar el rectángulo de colisión con la posición actual
        self.rect.x = self.x
        self.rect.y = self.y
        logging.info("Player INFO: Velocidad V %s y VeloH %s", self.speedV, self.speedH)

    def rotar(self, angulo):
        return pygame.transform.rotate(self.imagen, angulo)

    def escalaGrises(self):
        return pygame.transform.grayscale(self.imagen)

    def disparo(self):
        if self.municion > 0:
            logging.info("Player DISPARO: Hay munición.")
            self.bala = Disparos(self.x, self.y, True, self.orientacion)
            self.balas.add(self.bala)
            self.flagDisparo = True
            self.municion -= 1
            self.canalDisparo = self.sonidoDisparo.musica.play()


class Enemigo(pygame.sprite.Sprite):
    x = 12
    y = 12
    prev_x = None
    prev_y = None
    casilla = 0

    vida = int
    flagDisparo = bool = False
    isJefeEnemigo = bool = False

    alarma = bool = False
    # bocadilloTexto vars
    bubble_start_time = pygame.time.get_ticks()
    bubble_duration = 10000  # 10 segundos
    fade_duration = 2000     # últimos 2 segundos para desvanecerse

    posicionesRecorridas = []
    tiempoOlvido = 5

    orientacion = int  # 0 Arriba 1 Derecha 2 Abajo 3 Izquierda

    visionImage = None
    velocidadVisionRotacion = float = 1.5
    visionPos = Vector2
    speedV = 1
    speedH = 1
    angle = int
    imageEnemigo = None
    imageJefeEnemigo = None
    rect = None
    bala = Disparos
    balas = pygame.sprite.Group()
    MazeInfo = []
    balasArray = []
    kia = None

    sonidoDisparoEnemigo = Sonido.Sonido()

    def __init__(self):
        logging.info("Init Enemigo")
        super().__init__()
        self.orientacion = 'N'

        # Inicio IA enemigos
        self.kia = KerberosIA.KerberosIA()
        self.kia.KasRecorridas = self.posicionesRecorridas

        self.vida = 100
        self.municion = 100

        self.visionPos = Vector2 (0, 0)
        self.angle = 2
        self.flagDisparo = False
        self.imageEnemigo = load_image("Chainsaw.png", IMG_DIR, alpha=True)
        self.imageEnemigo = pygame.transform.scale(self.imageEnemigo, (22, 22))
        self.rect = self.imageEnemigo.get_rect()
        self.imageJefeEnemigo = load_image("wilber-eeek.png", IMG_DIR, alpha=True)
        self.imageJefeEnemigo = pygame.transform.scale(self.imageJefeEnemigo, (22, 22))
        self.rect = self.imageJefeEnemigo.get_rect()
        # self.visionImage = load_image("linterna.png", "Code/assets", alpha=True)
        # self.visionImage = pygame.transform.scale(self.visionImage, (60, 60))
        self.visionImage = pygame.Surface((40, 60), pygame.SRCALPHA)
        # Coordenadas del triángulo (vértice arriba, base abajo)
        # Vértice cerca del planeta, base en el exterior
        p1 = (20, 5)   # vértice
        p2 = (5, 55)   # esquina izquierda base
        p3 = (35, 55)  # esquina derecha base
        # Dibujamos triángulo amarillo con alpha 50%
        color = (199,180,70, 128)  # RGBA → alpha=128 (50%)
        pygame.draw.polygon(self.visionImage, color, [p1, p2, p3])        
        self.visionImage.set_alpha(128)

        self.isJefeEnemigo = False
        self.visionPos = Vector2([Enemigo.x, Enemigo.y])
        self.offset = Vector2(200, 0)
        self.angle = 0
        self.sonidoDisparoEnemigo.musica = pygame.mixer.Sound("./Resources/Sonidos/gunfire.mp3")

    def inicio(self, vx, vy):
        logging.info("Inicio Enemigos")
        self.x = random.randint(0, vx)
        self.y = random.randint(BIAS, vy)
        self.prev_x = self.x
        self.prev_y = self.y

    def definirJefeEnemigo(self):
        self.isJefeEnemigo = True

    def inicioCelda(self, cell):
        self.casilla = cell

    def logPosicionEnemigo(self):
        logging.info('Posición Enemigo: x: %s e y: %s con casilla --> %s', self.x, self.y, self.casilla)

    def moveRight(self):
        self.x = self.x + self.speedH
        self.orientacion = 1
        self.logMovimiento('Derecha', self.x, self.y)

    def moveLeft(self):
        self.x = self.x - self.speedH
        self.orientacion = 3
        self.logMovimiento('Izquierda', self.x, self.y)

    def moveUp(self):
        self.y = self.y - self.speedV
        self.orientacion = 0
        self.logMovimiento('Arriba', self.x, self.y)

    def moveDown(self):
        self.y = self.y + self.speedV
        self.orientacion = 2
        self.logMovimiento('Abajo', self.x, self.y)

    def getPosicion(self):
        return self.casilla

    def vision(self, pos):
        logging.info("Pintamos cono de visión")
        
    def visionRotar(self):
        logging.info("visión Rotar")
        self.angle = (self.angle + self.velocidadVisionRotacion) % 360
        # Add the rotated offset vector to the pos vector to get the rect.center.
        # self.visionImage = pygame.transform.rotate(self.visionImage, self.angle)

    # MÉTODO UPDATE 
    def update(self):
        logging.debug('Dentro Update ENEMIGOS.')
        # Guardar posición previa
        self.prev_x = self.x
        self.prev_y = self.y

        # Actualizar el rectángulo de colisión con la posición actual
        self.rect.x = self.x
        self.rect.y = self.y
        
        #self.visionRotar()
        self.moveDown()
        
        # Actualizar rect tras mover
        self.rect.x = self.x
        self.rect.y = self.y

        self.borrarRecorridosAntiguos()

    def updateJefe(self):
        logging.debug('Dentro Update ENEMIGOS.')
        # Guardar posición previa
        self.prev_x = self.x
        self.prev_y = self.y

        # Actualizar el rectángulo de colisión con la posición actual
        self.rect.x = self.x
        self.rect.y = self.y

        self.kia.casilla = MazeLab.Maze.calcularCasilla(self.x, self.y)

        self.kia.definirPosicion(self.x, self.y)
        
        self.visionRotar()
        dir = self.kia.update()
        if dir == 0:
            self.moveUp()
        elif dir == 1:
            self.moveRight()
        elif dir == 2:
            self.moveDown()
        else:
            self.moveLeft()
        
        # Actualizar rect tras mover
        self.rect.x = self.x
        self.rect.y = self.y

        self.borrarRecorridosAntiguos()

    def revertir_movimiento(self):
        # Revertir a la posición previa tras colisión
        if hasattr(self, 'prev_x') and hasattr(self, 'prev_y'):
            self.x = self.prev_x
            self.y = self.prev_y

    def cambiar_direccion(self):
        # Cambio simple de dirección: invertir velocidad vertical
        self.speedV = -self.speedV 

        if self.orientacion == 0:
            self.orientacion = 2
        elif self.orientacion == 2:
            self.orientacion = 0
        elif self.orientacion == 1:
            self.orientacion = 3
        elif self.orientacion == 3:
            self.orientacion = 1

        self.kia.orientacion = self.orientacion
        # Pequeño desplazamiento para evitar quedarse pegado
        #self.rect.y = self.y

    def logMovimiento(self, direccion, finalx, finaly):
        logging.info('Movimiento %s hasta x: %s, y %s', direccion, finalx, finaly)

    def detectarColision(self):
        self.kia.colisionParedes = True
        self.kia.orientacion = self.orientacion
        self.kia.update()
        
    def rotar(self, angulo):
        return pygame.transform.rotate(self.imagen, angulo)

    def escalaGrises(self):
        return pygame.transform.grayscale(self.imagen)

    # Aquí guardamos la posición donde está el enemigo donde no está el jugador.
    def cargarCasillaRecorrido(self, casilla):
        existe = any(v == 3 for v, t in self.posicionesRecorridas)
        # Sólo cargamos posiciones que no hayamos recorrido.
        if not existe:
            self.posicionesRecorridas.append((casilla, time.time()))

    def borrarRecorridosAntiguos(self):
        ahora = time.time()
        self.posicionesRecorridas = [(v, t) for (v, t) in self.posicionesRecorridas if ahora - t < self.tiempoOlvido]
        
    @staticmethod
    def bocadilloTexto(surface, text, pos, alpha, color=(255, 255, 255), text_color=(0, 0, 0)):
        """Dibuja un bocadillo de texto con transparencia controlada por alpha."""
        font = pygame.font.SysFont("arial", 20)
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect()

        padding = 10
        bubble_width = text_rect.width + padding * 2
        bubble_height = text_rect.height + padding * 2

        bubble_rect = pygame.Rect(0, 0, bubble_width, bubble_height)
        bubble_rect.midbottom = (pos[0], pos[1] - 10)

        # Superficie con canal alfa
        bubble_surf = pygame.Surface((bubble_width, bubble_height + 10), pygame.SRCALPHA)

        # Color con opacidad (alpha)
        bubble_color = (*color[:3], alpha)

        # Cuerpo del bocadillo
        pygame.draw.rect(bubble_surf, bubble_color, (0, 0, bubble_width, bubble_height), border_radius=10)

        # Punta
        pygame.draw.polygon(bubble_surf, bubble_color, [
        (bubble_width // 2 - 8, bubble_height),
        (bubble_width // 2 + 8, bubble_height),
        (bubble_width // 2, bubble_height + 10)
        ])

        # Texto (se aplica opacidad igual al bocadillo)
        text_with_alpha = text_surf.copy()
        text_with_alpha.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)

        bubble_surf.blit(text_with_alpha, (padding, padding))
        surface.blit(bubble_surf, bubble_rect.topleft)

    def restarRelojBocadilloTexto(self):
        self.bubble_start_time = pygame.time.get_ticks()

    def disparo(self):
        if self.municion > 0:
            self.bala = Disparos(self.rect.centerx, self.rect.top, False, self.orientacion)
            self.balas.add(self.bala)
            self.flagDisparo = True
            self.municion -= 1
            self.canalDisparo = self.sonidoDisparoEnemigo.musica.play()