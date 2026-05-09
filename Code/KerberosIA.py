import mates

import logging
import statistics
import MazeLab
import random
import os
import sys

import pygame
from pygame.locals import *

DEBUG_IA = False # Flag para controlar los print

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
    direccion = int

    casilla = int = 0
    posicion = MazeLab.posicion
    casillasLibres = None
    casillasLibresVuelta = None

    # Info importante pasada a través del enemigo.
    KasRecorridas = None
    conexiones = None
    Laberinto = []

    def __init__(self):
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

    def definirPosicion(self, x, y ):
        self.posicion = MazeLab.posicion(x, y)

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

    def gritarAlarma(self):
        self.alarma = True
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

        range = MazeLab.NUM_CASILLAS_H * MazeLab.NUM_CASILLAS_VERTI
        if self.casilla != 0 or self.casilla == range:
            # Izquierda
            if self.Laberinto[self.casilla-1] == 1:
                self.casillasLibresVuelta[3] = True
                if self.casilla-1 not in self.KasRecorridas:
                    self.casillasLibres[3] = True
            # Derecha
            if self.Laberinto[self.casilla+1] == 1:
                self.casillasLibresVuelta[1] = True
                if self.casilla-1 not in self.KasRecorridas:
                    self.casillasLibres[1] = True
            # Arriba
            if self.Laberinto[self.casilla-MazeLab.NUM_CASILLAS_VERTI] == 1:
                self.casillasLibresVuelta[0] = True
                if self.casilla-1 not in self.KasRecorridas:
                    self.casillasLibres[0] = True
            # Abajo
            if self.Laberinto[self.casilla+MazeLab.NUM_CASILLAS_VERTI] == 1:
                self.casillasLibresVuelta[2] = True
                logging.info("Error, no se puede cargar la casilla: ")
                if self.casilla-1 not in self.KasRecorridas:
                    self.casillasLibres[2] = True
        else:
            logging.info('Fuera de Rango en KIA Cálculo casilla')
            if DEBUG_IA:
                print('Fuera de Rango en KIA Cálculo casilla')
    
    def elegirDireccion(self):
        opciones = self.conexiones[self.casilla]

        # evitar volver atrás
        opuesta = (self.orientacion + 2) % 4

        posibles = [d for d in opciones if d != opuesta]

        if posibles:
            return random.choice(posibles)

        return opuesta

    def update(self):
        if self.colisionParedes:
            self.elegirDireccion()
            result = self.casillasLibres.count(True)
            valor = 0 # Reinit el valor a devolver.

            if result > 0:
                if DEBUG_IA:
                    print("Dentro KerberoIA Jefe Enemigo.")
                if result == 1:
                    for i in self.casillasLibres:
                        if i:
                            valor += 1
                            valor = self.casillasLibres[result-1]
                            break
                else:
                    res = random.randint(0, result-1)
                    x = 0
                    for i in self.casillasLibres:
                        if i: 
                            x += 1
                            valor += 1
                            
                            if x == res:
                                return valor
                if DEBUG_IA:
                    print("valor en IA : ", valor)
                
                """ try:
                    while not self.casillasLibres[valor]:
                        if valor < 4:
                            valor += 1
                except ValueError:
                    print("Oops!  That was no valid number.  Try again...", valor) """
                
                if DEBUG_IA:
                    print("DirecciÓN a TOMAR: ", valor)
            else:
                self.casillasLibres = self.casillasLibresVuelta
                result = self.casillasLibres.count(True)
                #valor = random.randint(0, result-1)
                if DEBUG_IA:
                    print('ENCERRADO!!!, cómo es posible')
                logging.info('ENCERRADO!!!, cómo es posible')
                valor = 0
            self.colisionParedes = False
        else: 
            # self.cambiar_direccion()
            valor = self.orientacion

        # Devolvemos la dirección a donde se va a mover el Enemigo.        
        return valor