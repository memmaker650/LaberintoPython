import math

import pygame

# luces.py
# Iluminación de los niveles oscuros: la zona del laberinto se cubre de oscuridad y el
# jugador sólo ve el haz de su linterna.
#
# El haz se calcula lanzando rayos desde el jugador en abanico. Cada rayo se detiene en el
# primer obstáculo que encuentra (paredes, enemigos y puertas), así que la luz no los
# atraviesa: lo que hay detrás de una pared, de un enemigo o de una puerta queda a oscuras.

# Ángulo del haz (grados, eje Y hacia abajo) según la orientación del jugador:
# 0 Arriba, 1 Derecha, 2 Abajo, 3 Izquierda.
ANGULO_ORIENTACION = {0: 270, 1: 0, 2: 90, 3: 180}

# Degradado del haz: (fracción del alcance de la linterna, alfa de la oscuridad).
# Cerca del jugador la luz es total y se va apagando hacia el final del alcance.
DEGRADADO_HAZ = [(1.0, 130), (0.75, 60), (0.5, 0)]


class Linterna:
    def __init__(self, zona, opacidad=0.9, alcance=230, apertura=60, num_rayos=48,
                 penetracion=10, radio_jugador=16, velocidad_giro=15):
        # zona: rectángulo de pantalla que se oscurece (el laberinto, sin el HUD).
        self.zona = pygame.Rect(zona)
        self.opacidad = opacidad
        self.alfa_oscuridad = round(255 * opacidad)
        self.alcance = alcance              # longitud máxima del haz en píxeles
        self.apertura = apertura            # ancho del haz en grados
        self.num_rayos = num_rayos
        self.penetracion = penetracion      # píxeles que se ilumina el borde del obstáculo alcanzado
        self.radio_jugador = radio_jugador  # pequeño halo para que el jugador se vea a sí mismo
        self.velocidad_giro = velocidad_giro  # grados por frame al cambiar de dirección

        self.angulo = 0.0
        self.haz = []
        self.oscuridad = pygame.Surface(self.zona.size, pygame.SRCALPHA)

    # Gira el haz hacia la dirección de movimiento del jugador por el camino más corto.
    def apuntar(self, orientacion, instantaneo=False):
        if orientacion not in ANGULO_ORIENTACION:
            return
        objetivo = ANGULO_ORIENTACION[orientacion]
        diferencia = (objetivo - self.angulo + 180) % 360 - 180
        if instantaneo or abs(diferencia) <= self.velocidad_giro:
            self.angulo = float(objetivo)
        else:
            self.angulo = (self.angulo + math.copysign(self.velocidad_giro, diferencia)) % 360

    # Punto donde termina un rayo: al alcance máximo o al chocar con el primer obstáculo.
    def lanzarRayo(self, origen, angulo, obstaculos):
        ox, oy = origen
        dx = math.cos(math.radians(angulo))
        dy = math.sin(math.radians(angulo))
        fin = (ox + dx * self.alcance, oy + dy * self.alcance)

        distancia = self.alcance
        for rect in obstaculos:
            tramo = rect.clipline(origen, fin)
            if tramo:
                # El extremo del tramo más cercano al origen es por donde entra el rayo.
                (x1, y1), (x2, y2) = tramo
                distancia = min(distancia, math.hypot(x1 - ox, y1 - oy), math.hypot(x2 - ox, y2 - oy))

        if distancia < self.alcance:
            distancia = min(distancia + self.penetracion, self.alcance)
        return (ox + dx * distancia, oy + dy * distancia)

    # Calcula el abanico de rayos del haz desde 'origen'. Devuelve los puntos finales.
    def calcularHaz(self, origen, obstaculos):
        # Sólo cuentan los obstáculos al alcance de la linterna. Los que contienen al propio
        # jugador (p. ej. un enemigo que le está tocando) se ignoran para no apagar todo el haz.
        alrededor = pygame.Rect(0, 0, 2 * self.alcance, 2 * self.alcance)
        alrededor.center = (round(origen[0]), round(origen[1]))
        cercanos = [r for r in obstaculos if alrededor.colliderect(r) and not r.collidepoint(origen)]

        inicio = self.angulo - self.apertura / 2
        paso = self.apertura / (self.num_rayos - 1)
        self.haz = [self.lanzarRayo(origen, inicio + i * paso, cercanos) for i in range(self.num_rayos)]
        return self.haz

    # Oscurece la zona y abre en la oscuridad el hueco del haz y el halo del jugador.
    def dibujar(self, pantalla, origen, obstaculos):
        puntos = self.calcularHaz(origen, obstaculos)

        self.oscuridad.fill((0, 0, 0, self.alfa_oscuridad))
        ox, oy = origen[0] - self.zona.x, origen[1] - self.zona.y
        locales = [(x - self.zona.x, y - self.zona.y) for x, y in puntos]

        # Del más lejano al más cercano: cada polígono sustituye el alfa del anterior.
        # Cada rayo se recorta a la distancia del tramo (nunca más allá de donde chocó).
        longitudes = [math.hypot(x - ox, y - oy) for x, y in locales]
        for fraccion, alfa in DEGRADADO_HAZ:
            limite = fraccion * self.alcance
            poligono = [(ox, oy)]
            for (x, y), longitud in zip(locales, longitudes):
                escala = min(1.0, limite / longitud) if longitud else 0.0
                poligono.append((ox + (x - ox) * escala, oy + (y - oy) * escala))
            pygame.draw.polygon(self.oscuridad, (0, 0, 0, min(alfa, self.alfa_oscuridad)), poligono)

        pygame.draw.circle(self.oscuridad, (0, 0, 0, 0), (round(ox), round(oy)), self.radio_jugador)
        pantalla.blit(self.oscuridad, self.zona.topleft)
