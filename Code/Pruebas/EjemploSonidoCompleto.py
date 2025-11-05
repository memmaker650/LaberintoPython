import pygame
import logging

pygame.init()
pygame.mixer.init()
logging.basicConfig(level=logging.INFO)

class Jugador:
    def __init__(self):
        self.sonidoDisparo = pygame.mixer.Sound("disparo.wav")
        self.canalDisparo = pygame.mixer.Channel(0)
        self.municion = 5

    def disparar(self):
        if self.municion <= 0:
            logging.info("Sin munición.")
            return

        logging.info("Player DISPARO: Hay munición.")
        if self.canalDisparo.get_busy():
            self.canalDisparo.stop()

        self.canalDisparo.play(self.sonidoDisparo)
        self.municion -= 1

jugador = Jugador()

for _ in range(3):
    jugador.disparar()
    pygame.time.delay(100)  # Dispara muy rápido
