import mates

import logging
import statistics
import random
import os
import sys

import pygame
from pygame.locals import *


class KerberosIA:
    isPlayerDetected = bool
    estado = int   # 0 Patrol, 1 Following Player, 2 Alarm, 3 Team working
    alarma = bool
    animo = int    # 0 OK, 1 Angry, 2 Sad
    tipo = int      # 0 soldier, 1 boss or lieutenant
    ordenJefe = bool

    def __init__(self):
        logging.info('Dentro de Inteligencia Artificial, KerberosIA by Jorge Vega')
        self.isPlayerDetected = False
        self.estado = 0  # 0 Patrol, 1 Following Player, 2 Alarm, 3 Team working
        self.animo = 0  # 0 OK, 1 Angry, 2 Sad
        self.tipo = 0  # 0 soldier, 1 boss or lieutenant

    def detectarPlayer(self):
        logging('Método para detectar al jugador.')

    def cambioEstado(self):
        if (self.estado == 0 & self.isPlayerDetected == True):
            self.estado = 1
        elif (self.estado == 1 & self.isPlayerDetected == True):
            self.estado = 2
        elif (self.estado == 2):
            self.gritarAlarma()
            self.estado = 1
        elif (self.ordenJefe == True):
            self.estado = 3

    def gritarAlarma(self):
        alarma = True;
        # Pintar el gruñido de alarma
