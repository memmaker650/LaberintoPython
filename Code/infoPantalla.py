import logging
import string
import pygame


class barraDeVida(pygame.sprite.Sprite):
    vida = int
    textoVida = string   # Para poner el % de vida que queda.
    spriteBarraDeVida = None

    def __init__(self):
        self.vida = 100

    def crearBarraDeVida(self):
        # Crear una superficie de 200x50
        self.spriteBarraDeVida = pygame.Surface((200, 50))
        # Rellenar de rojo
        self.spriteBarraDeVida.fill((255, 0, 0))  # RGB: rojo
        # Dibujar borde blanco
        

class panelPuntuacion(pygame.sprite.Sprite):
    puntos = int
    textoPuntos = string
    baseString = "00000000"

    def __init__(self):
        self.puntos = 0
        self.textoPuntos = self.baseString

    def incrementarPuntos(self, subida):
        puntos += subida

    def restarPuntos(self, subida):
        puntos -= subida

    def reiniciarPuntos(self, subida):
        puntos = 0
    
    def conversionTexto(self):
        self.textoPuntos = str(self.puntos).zfill(8)

class infoNivel(pygame.sprite.Sprite):
    NumeroNivel = int
    textoNivel = string

    def __init__(self):
        self.NumeroNivel = 1
        self.textoNivel = "1"

    def definirNumeroNivel(self, NN):
        self.NumeroNivel = NN

    def conversionTexto(self):
        self.textoNivel = str(self.NumeroNivel)

class relojPantalla(pygame.sprite.Sprite):
    maxTiempo = int = 90
    tiempoActual = float
    tiempoInteger = int
    flagTerminado = bool
    textoReloj = string
    
    def __init__(self):
        self.tiempoActual = 90.0
        self.tiempoInteger = 90
        self.flagTerminado = False
        self.textoReloj = "90"

    def cambioSegundo(self):
        if (self.tiempoActual - self.tiempoInteger < 0):  
            self.tiempoInteger -= 1

    def cuentaTiempo(self, valor):
        self.tiempoActual -= valor

    def conversionTexto(self):
        self.textoReloj = str(self.tiempoInteger)

class infoItems(pygame.sprite.Sprite):
    NumeroNivel = int
    textoItems = string

    def definirNumeroNivel(self, NN):
        self.NumeroNivel = NN

# 1 Cuchillo
# 2 Pistola
# 3 Metralleta
# 4 Granada
# 5 Laser
# 6 Bomba humo
class infoArmasMunicion(pygame.sprite.Sprite):
    Armas = [bool]
    municion = [int]
    textoArma = string
    textoMunicion = string
    armaSeleccionada = int = None
    municionArmaSeleccionada = int = None

    def __init__(self):
        self.armaSeleccionada = 4

        n = 6
        self.Armas = [False] * n
        self.Armas[4] = True
        
        n = 6
        self.municion = [0] * n
        self.municion[0] = 1

    def update(self):
        logging.info("Dentro UPDATE info Armas Municion !!!")
        self.Armas = [False] * 6
        self.Armas[self.armaSeleccionada-1] = True

        self.municion[self.armaSeleccionada-1] = self.municionArmaSeleccionada

    def definirMunicion(self, armaNum, municion):
        self.Armas[armaNum] = municion

    def incrementarMunicion(self, armaNum, cargador):
        self.Armas[armaNum] = self.Armas[armaNum]+ cargador

    def gastarMunicion(self, armaNum):
        self.Armas[armaNum] = self.Armas[armaNum] -1

    def conversionTexto(self):
        if self.armaSeleccionada == 1:
            self.textoArma = "Cuchillo"
        elif self.armaSeleccionada == 2:
            self.textoArma = "Pistola"
        elif self.armaSeleccionada == 3:
            self.textoArma = "Metralleta"
        if self.armaSeleccionada == 4:
            self.textoArma = "Granada"
        elif self.armaSeleccionada == 5:
            self.textoArma = "Laser"
        elif self.armaSeleccionada == 6:
            self.textoArma = "Bomba Humo"

        if self.armaSeleccionada == 1:
            self.textoMunicion = str(self.municion[self.armaSeleccionada -1])
        elif self.armaSeleccionada == 2:
            self.textoMunicion = str(self.municion[self.armaSeleccionada -1])
        elif self.armaSeleccionada == 3:
            self.textoMunicion = str(self.municion[self.armaSeleccionada -1])
        if self.armaSeleccionada == 4:
            self.textoMunicion = str(self.municion[self.armaSeleccionada -1])
        elif self.armaSeleccionada == 5:
            self.textoMunicion = str(self.municion[self.armaSeleccionada -1])
        elif self.armaSeleccionada == 6:
            self.textoMunicion = str(self.municion[self.armaSeleccionada -1])
