import mates

import logging
import statistics
import MazeLab
import random
import os
import sys

import pygame
from pygame.locals import *
from collections import deque

DEBUG_IA = False # Flag para controlar los print

class posicion:
    def __init__(self, valorX = 0, valorY = 0):
        self.x = valorX
        self.y = valorY
    
    def cargar(self, valorX, valorY):
        self.x = valorX
        self.y = valorY

class KerberosIA:
    playerDetectado = bool = False
    estado = int   # 0 Patrol, 1 Following Player, 2 Alarm, 3 Team working
    alarma = bool = False
    animo = int    # 0 OK, 1 Angry, 2 Sad, 3 Alarmado
    tipo = int      # 0 soldier, 1 boss or lieutenant

    ordenJefe = bool = False
    combatir = bool = False

    colisionParedes = bool = False
    orientacion = int = 0
    direccion = int

    # Info importante pasada a través del enemigo.
    KasRecorridas = None
    conexiones = None
    Laberinto = []

    def __init__(self, x = 0, y = 0):
        logging.info('Dentro de Inteligencia Artificial, KerberosIA by Jorge Vega')
        self.isPlayerDetected = False
        self.estado = 0  # 0 Patrol, 1 Following Player, 2 Alarm, 3 Team working
        self.animo = 0  # 0 OK, 1 Angry, 2 Sad
        self.tipo = 0  # 0 soldier, 1 boss or lieutenant
        self.colisionParedes = False

        self.casillasLibres = [False] * 4
        self.casillasLibresVuelta = [False] * 4

        # Info importante pasada a través del enemigo.
        self.KasRecorridas = set()

        self.ultimaCasilla = -1
        self.direccionActual = 1
        self.playerDetectado = False
        self.path = []
        self.casillaJugador = 0
        self.posicion = posicion(x, y)
        self.casilla = 0

    def definirPosicion(self, x, y ):
        self.posicion.cargar(x, y)

    def detectarPlayer(self):
        logging.info('Método para detectar al jugador.')

    def cambiarEstado(self, state):
        self.estado = state
    
    def cambioEstado(self):
        if (self.estado == 0 and self.isPlayerDetected == True):
            self.estado = 1
        elif (self.estado == 1 and self.isPlayerDetected == True):
            self.estado = 2
        elif (self.estado == 2):
            self.gritarAlarma()
            self.estado = 1
        elif (self.ordenJefe == True):
            self.estado = 3
    
    def cambiarSentido(self):
        # Cambio simple de dirección: invertir velocidad vertical
        self.speedV = -self.speedV 

        # 0 Arriba, 1 Derecha, 2 Abajo y 3 Izquierda
        if self.orientation == 0:
            self.orientation = 2
        elif self.orientation == 2:
            self.orientation = 0
        elif self.orientation == 1:
            self.orientation = 3
        elif self.orientation == 3:
            self.orientation = 1

    def esInterseccion(self):
        opciones = self.conexiones.get(self.casilla, [])

        return len(opciones) >= 3

    def gritarAlarma(self):
        self.alarma = True
        # Pintar el gruñido de alarma

    def reiniciarArraySiguientesCasillas(self):
        self.casillasLibres.clear()
        self.casillasLibres = [False] * 4
    
    def reiniciarArraySiguientesCasillasVuelta(self):
        self.casillasLibresVuelta.clear()
        self.casillasLibresVuelta = [False] * 4

    def calcularDireccion(self, origen, destino):
        diferencia = destino - origen

        if diferencia == -MazeLab.NUM_CASILLAS_H:
            return 0

        elif diferencia == 1:
            return 1

        elif diferencia == MazeLab.NUM_CASILLAS_H:
            return 2

        elif diferencia == -1:
            return 3

        return self.orientacion

    def obtenerCasillaSiguiente(self, casilla, direccion):
        # 0 Arriba
        if direccion == 0:
            return casilla - MazeLab.NUM_CASILLAS_H

        # 1 Derecha
        elif direccion == 1:
            return casilla + 1

        # 2 Abajo
        elif direccion == 2:
            return casilla + MazeLab.NUM_CASILLAS_H

        # 3 Izquierda
        elif direccion == 3:
            return casilla - 1

        return casilla
    
    def mover(self, casilla, direccion):
        if direccion == 0:
            return casilla - MazeLab.NUM_CASILLAS_H

        elif direccion == 1:
            return casilla + 1

        elif direccion == 2:
            return casilla + MazeLab.NUM_CASILLAS_H

        elif direccion == 3:
            return casilla - 1

    def calcular_camino_BFS(self, casillaInicio, casillaObjetivo):
        cola = deque()
        cola.append((casillaInicio, [casillaInicio]))

        visitados = set()

        while cola:
            casillaActual, camino = cola.popleft()

            # Objetivo encontrado
            if casillaActual == casillaObjetivo:
                return camino

            if casillaActual in visitados:
                continue

            visitados.add(casillaActual)

            # Obtener conexiones
            direcciones = self.conexiones.get(casillaActual, [])

            for direccion in direcciones:

                siguiente = self.obtenerCasillaSiguiente(
                    casillaActual,
                    direccion
                )

                if siguiente not in visitados:

                    cola.append(
                        (siguiente, camino + [siguiente])
                    )

        # Sin camino
        return []    
    
    def elegirDireccion(self):
        opciones = self.conexiones.get(self.casilla, [])

        if not opciones:
            return self.orientacion

        # evitar dar media vuelta
        opuesta = (self.orientacion + 2) % 4

        posibles = [d for d in opciones if d != opuesta]

        if posibles:
            return random.choice(posibles)

        return opuesta
    
    # Update IA - Kerberos IA
    #----------------------------------
    def update(self):
        self.casilla = MazeLab.Maze.calcularCasilla(
            self.posicion.x,
            self.posicion.y
        )

        if self.playerDetectado:
            self.path = self.calcular_camino_BFS(
                self.casilla,
                self.casillaJugador
            )
        else:
            # SOLO actuar al entrar en nueva casilla
            if self.casilla != self.ultimaCasilla:
                self.ultimaCasilla = self.casilla

                opciones = self.conexiones.get(
                    self.casilla,
                    []
                )
                # Callejón
                if len(opciones) == 1:
                    print("Callejón")
                    self.orientacion = opciones[0]

                # Pasillo
                elif len(opciones) == 2:
                    print("Pasillo")
                    opuesta = (self.orientacion + 2) % 4

                    posibles = [
                        d for d in opciones
                        if d != opuesta
                    ]
                    if posibles:
                        self.orientacion = posibles[0]

                # Intersección
                elif len(opciones) >= 3:
                    print("Intersección")
                    self.orientacion = self.elegirDireccion()

        return self.orientacion