import mates

import logging
import statistics
import MazeLab
import random
import os
import sys

import pygame
from pygame.locals import *


class KerberosIA:
    isPlayerDetected = bool = False
    estado = int   # 0 Patrol, 1 Following Player, 2 Alarm, 3 Team working
    alarma = bool = False
    animo = int    # 0 OK, 1 Angry, 2 Sad, 3 Alarmado
    tipo = int      # 0 soldier, 1 boss or lieutenant

    ordenJefe = bool = False
    combatir = bool = False

    colisionParedes = bool = False
    orientacion = int = 0

    casilla = int = 0
    posicion = MazeLab.posicion
    casillasLibres = [False] * 4
    casillasLibresVuelta = [False] * 4

    # Info importante pasada a través del enemigo.
    KasRecorridas = set()
    Laberinto = []

    def __init__(self):
        logging.info('Dentro de Inteligencia Artificial, KerberosIA by Jorge Vega')
        self.isPlayerDetected = False
        self.estado = 0  # 0 Patrol, 1 Following Player, 2 Alarm, 3 Team working
        self.animo = 0  # 0 OK, 1 Angry, 2 Sad
        self.tipo = 0  # 0 soldier, 1 boss or lieutenant
        self.colisionParedes = False

    def definirPosicion(self, x, y ):
        self.posicion = MazeLab.posicion(x, y)

    def detectarPlayer(self):
        logging.info('Método para detectar al jugador.')

    def cambiarEstado(self, state):
        self.estado = state

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
    
    def cambiar_direccion(self):
        # Cambio simple de dirección: invertir velocidad vertical
        self.speedV = -self.speedV 

        if self.orientation == 0:
            self.orientation = 2
        elif self.orientation == 2:
            self.orientation = 0
        elif self.orientation == 1:
            self.orientation = 3
        elif self.orientation == 3:
            self.orientation = 1

    def gritarAlarma(self):
        alarma = True;
        # Pintar el gruñido de alarma

    def reiniciarArraySiguientesCasillas(self):
        self.casillasLibres.clear()
        self.casillasLibres = [False] * 4
    
    def reiniciarArraySiguientesCasillasVuelta(self):
        self.casillasLibresVuelta.clear()
        self.casillasLibresVuelta = [False] * 4

    def revisarCasillasAdyacentes(self):
        # Calculo de casillas para elegir siguiente posición de movimiento del personaje.
        logging.info('Revisar casillas para movimiento.')
        self.reiniciarArraySiguientesCasillas()
        self.reiniciarArraySiguientesCasillasVuelta()

        # Izquierda
        if self.Laberinto[self.casilla-1] == 1:
            self.casillasLibresVuelta [3] = True
            if self.casilla-1 not in self.KasRecorridas:
                self.casillasLibres[3] = True
        # Derecha
        if self.Laberinto[self.casilla+1] == 1:
            self.casillasLibresVuelta [1] = True
            if self.casilla-1 not in self.KasRecorridas:
                self.casillasLibres[1] = True
        # Arriba
        if self.Laberinto[self.casilla-MazeLab.NUM_CASILLAS] == 1:
            self.casillasLibresVuelta [0] = True
            if self.casilla-1 not in self.KasRecorridas:
                self.casillasLibres[0] = True
        # Abajo
        if self.Laberinto[self.casilla+MazeLab.NUM_CASILLAS] == 1:
            self.casillasLibresVuelta [2] = True
            if self.casilla-1 not in self.KasRecorridas:
                self.casillasLibres[2] = True

    def update(self):
        self.revisarCasillasAdyacentes()
        result = self.casillasLibres.count(True)

        if not self.colisionParedes:
            if result > 0:
                valor = random.randint(0, result-1)
                # print("valor1: ", valor)
                # print("tamaño vector: ", len(self.casillasLibres))
                while not self.casillasLibres[valor]:
                    valor += 1
            else:
                self.casillasLibres = self.casillasLibresVuelta
                result = self.casillasLibres.count(True)
                valor = random.randint(0, result-1)
                # print("valor 2: ", valor)
                # print("tamaño vector: ", len(self.casillasLibres))
                while not self.casillasLibres[valor]:
                    valor += 1
        else: 
            self.cambiar_direccion()
            valor = self.orientacion

        # Devolvemos la dirección a donde se va a mover el Enemigo.        
        return valor