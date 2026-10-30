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
import math
import Luces

DEBUG_IA = False # Flag para controlar los print

# Patrulla de los enemigos normales dentro de su zona (habitación o pasillo).
PROB_SEGUIR_RECTO = 0.75  # en una habitación, probabilidad de seguir recto si se puede

# Estados de los enemigos.
ESTADO_PATRULLA = 0     # recorre su zona
ESTADO_PERSECUCION = 1  # sigue al jugador (el jefe, por el camino BFS)
ESTADO_ALARMA = 2       # ha visto al jugador y da la alarma
ESTADO_EQUIPO = 3       # trabajo en equipo (pendiente)
NOMBRES_ESTADO = {ESTADO_PATRULLA: "patrulla", ESTADO_PERSECUCION: "persecución",
                  ESTADO_ALARMA: "alarma", ESTADO_EQUIPO: "equipo"}

DURACION_ALARMA_MS = 4000  # sin volver a ver al jugador, la alarma dura esto y vuelve a patrullar


# Cono de visión de un enemigo. Se calcula con rayos que se cortan en las paredes (y puertas),
# así que el enemigo no ve a través de ellas.
class VisionEnemigo:
    def __init__(self, alcance=4 * 32, apertura=60, num_rayos=15):
        self.alcance = alcance      # píxeles
        self.apertura = apertura    # grados
        self.num_rayos = num_rayos
        self.origen = (0, 0)
        self.angulo = 0.0
        self.puntos = []            # extremos de los rayos (el polígono del cono es origen + puntos)

    # Recalcula el cono desde 'origen' mirando hacia 'angulo' (grados, eje Y hacia abajo).
    def actualizar(self, origen, angulo, paredes):
        self.origen = origen
        self.angulo = angulo % 360
        self.puntos = Luces.abanicoRayos(origen, self.angulo, self.apertura, self.num_rayos,
                                         self.alcance, paredes)
        return self.puntos

    def poligono(self):
        return [self.origen] + self.puntos if self.puntos else []

    # ¿Ve el punto? Tiene que estar al alcance, dentro del ángulo del cono y sin paredes en medio.
    def ve(self, punto, paredes):
        ox, oy = self.origen
        px, py = punto
        distancia = math.hypot(px - ox, py - oy)
        if distancia > self.alcance:
            return False
        if distancia > 0:
            direccion = math.degrees(math.atan2(py - oy, px - ox))
            diferencia = (direccion - self.angulo + 180) % 360 - 180
            if abs(diferencia) > self.apertura / 2:
                return False
        for rect in Luces.obstaculosCercanos(self.origen, self.alcance, paredes):
            if rect.clipline(self.origen, punto):
                return False
        return True

class posicion:
    def __init__(self, valorX = 0, valorY = 0):
        self.x = valorX
        self.y = valorY
    
    def cargar(self, valorX, valorY):
        self.x = valorX
        self.y = valorY

class KerberosIA:
    # Info importante pasada a través del enemigo.
    conexiones = None
    Laberinto = []
    log_debug = False

    def __init__(self, x = 0, y = 0):
        logging.info('Dentro de Inteligencia Artificial, KerberosIA by Jorge Vega')
        self.playerDetectado = False
        self.estado = 0  # 0 Patrol, 1 Following Player, 2 Alarm, 3 Team working
        self.alarma = False
        self.animo = 0  # 0 OK, 1 Angry, 2 Sad, 3 Alarmado
        self.tipo = 0  # 0 soldier, 1 boss or lieutenant
        self.colisionParedes = False

        self.ordenJefe = False
        self.combatir = False

        self.casillasLibres = [False] * 4
        self.casillasLibresVuelta = [False] * 4

        # Info importante pasada a través del enemigo.
        self.KasRecorridas = set()

        self.ultimaCasilla = -1
        self.direccionActual = 1
        self.orientacion = 0
        self.playerDetectado = False
        self.path = []
        self.casillaJugador = 0
        self.posicion = posicion(x, y)
        self.casilla = 0

        # Momento (ms) en que vio al jugador por última vez (para la duración de la alarma).
        self.ultimaVezVisto = None

        # Zonas del laberinto (MazeLab.Maze.calcularZonas) y zona en la que patrulla este enemigo.
        self.zonas = None
        self.tiposZona = None
        self.zona = None

    def definirPosicion(self, x, y ):
        self.posicion.cargar(x, y)

    def detectarPlayer(self):
        logging.info('Método para detectar al jugador.')

    def cambiarEstado(self, state):
        self.estado = state
    
    def cambioEstado(self):
        if (self.estado == 0 and self.playerDetectado == True):
            self.estado = 1
        elif (self.estado == 1 and self.playerDetectado == True):
            self.estado = 2
        elif (self.estado == 2):
            self.gritarAlarma()
            self.estado = 1
        elif (self.ordenJefe == True):
            self.estado = 3
    
    def cambiarSentido(self):
        # 0 Arriba, 1 Derecha, 2 Abajo y 3 Izquierda
        if self.orientacion == 0:
            self.orientacion = 2
        elif self.orientacion == 2:
            self.orientacion = 0
        elif self.orientacion == 1:
            self.orientacion = 3
        elif self.orientacion == 3:
            self.orientacion = 1

    def esInterseccion(self):
        opciones = self.conexiones.get(self.casilla, [])

        return len(opciones) >= 3

    def gritarAlarma(self):
        self.alarma = True
        # Pintar el gruñido de alarma

    # El enemigo ve al jugador: pasa a estado de alarma. Devuelve True si la alarma acaba de saltar
    # (no estaba ya en alarma), para avisar al resto sólo una vez.
    def verJugador(self, ahora_ms):
        self.ultimaVezVisto = ahora_ms
        nueva = self.estado != ESTADO_ALARMA
        self.estado = ESTADO_ALARMA
        self.gritarAlarma()
        return nueva

    # Sin ver al jugador: pasado DURACION_ALARMA_MS desde la última vez, vuelve a patrullar.
    def actualizarAlarma(self, ahora_ms):
        if self.estado == ESTADO_ALARMA and ahora_ms - self.ultimaVezVisto >= DURACION_ALARMA_MS:
            self.estado = ESTADO_PATRULLA
            self.alarma = False

    def nombreEstado(self):
        return NOMBRES_ESTADO.get(self.estado, str(self.estado))

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

    def _casillas_recorridas(self):
        casillas = set()

        if not self.KasRecorridas:
            return casillas

        for elemento in self.KasRecorridas:
            if isinstance(elemento, tuple) and len(elemento) > 0:
                casillas.add(elemento[0])
            else:
                casillas.add(elemento)

        return casillas

    def elegirDireccionEvitar(self, direccionBloqueada=None):
        opciones = list(self.conexiones.get(self.casilla, []))

        if not opciones:
            return self.orientacion

        if direccionBloqueada in opciones and len(opciones) > 1:
            opciones = [d for d in opciones if d != direccionBloqueada]

        # Evitar dar media vuelta salvo que no quede otra.
        opuesta = (self.orientacion + 2) % 4
        opciones_sin_opuesta = [d for d in opciones if d != opuesta]
        if opciones_sin_opuesta:
            opciones = opciones_sin_opuesta

        casillas_recorridas = self._casillas_recorridas()
        candidatas = sorted(
            opciones,
            key=lambda d: (
                self.obtenerCasillaSiguiente(self.casilla, d) in casillas_recorridas,
                d == self.orientacion
            )
        )

        return candidatas[0]

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

    # Patrulla dentro de la zona del enemigo (se llama al pasar por el centro de una casilla).
    #  - Pasillo: lo recorre de un extremo a otro; al llegar al final da media vuelta.
    #  - Habitación: se mueve por ella sin salir, normalmente recto y a veces girando.
    # Nunca elige una casilla de otra zona. Devuelve la dirección (0-3) o None si no puede moverse.
    def asignarZona(self, zonas, tiposZona, casilla):
        self.zonas = zonas
        self.tiposZona = tiposZona
        self.casilla = casilla
        self.zona = zonas.get(casilla)

    def tipoZona(self):
        if self.tiposZona is None or self.zona is None:
            return None
        return self.tiposZona.get(self.zona)

    def direccionPatrulla(self):
        if self.zonas is None or self.zona is None:
            return None
        opciones = [d for d in self.conexiones.get(self.casilla, [])
                    if self.zonas.get(self.obtenerCasillaSiguiente(self.casilla, d)) == self.zona]
        if not opciones:
            return None  # zona de una sola casilla: se queda quieto

        opuesta = (self.orientacion + 2) % 4
        sinVolver = [d for d in opciones if d != opuesta]

        if self.tipoZona() == "pasillo":
            if self.orientacion in sinVolver:
                return self.orientacion          # sigue por el pasillo
            if sinVolver:
                return sinVolver[0]              # curva del pasillo
            return opuesta                       # final del pasillo: media vuelta

        # Habitación (o cualquier otra zona)
        if not sinVolver:
            return opuesta                       # rincón sin salida
        if self.orientacion in sinVolver and random.random() < PROB_SEGUIR_RECTO:
            return self.orientacion
        return random.choice(sinVolver)

    # Método para seguir un camino tras detectar Player
    #----------------------------------------------------------
    def seguirCamino(self):
        logging.debug("Dentro de Seguir Kamino.")
        if len(self.path) == 0:
            return

        # Si hemos llegado a una casilla del camino,
        # eliminar todas las anteriores.
        while len(self.path) > 0 and self.path[0] == self.casilla:
            self.path.pop(0)

        # Destino alcanzado
        if len(self.path) == 0:
            return

        siguienteCasilla = self.path[0]

        self.orientacion = self.calcularDireccion(
            self.casilla,
            siguienteCasilla
        )
    
    # Update IA - Kerberos IA8888888
    #----------------------------------
    def update(self):
        self.casilla = MazeLab.Maze.calcularCasilla(
            self.posicion.x,
            self.posicion.y
        )

        if self.colisionParedes:
            self.path = []
            self.orientacion = self.elegirDireccionEvitar(self.orientacion)
            self.colisionParedes = False
            return self.orientacion

        # Salto la alarma y buscamos y seguimos el camino.
        if self.playerDetectado:
            if self.log_debug:
                print(f"Path BFS: {self.path}")
            if len(self.path) == 0 or (len(self.path) > 0 and self.path[-1] != self.casillaJugador):
                self.path = self.calcular_camino_BFS(
                    self.casilla,
                    self.casillaJugador
                )
            if len(self.path) > 0:
                self.seguirCamino()
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
                    if self.log_debug:
                        print("Callejón")
                    self.orientacion = opciones[0]

                # Pasillo
                elif len(opciones) == 2:
                    if self.log_debug:
                        print("Pasillo")
                    self.orientacion = self.elegirDireccionEvitar()

                # Intersección
                elif len(opciones) >= 3:
                    if self.log_debug:
                        print("Intersección")
                    self.orientacion = self.elegirDireccionEvitar()

        return self.orientacion
