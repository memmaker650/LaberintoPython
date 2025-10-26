import pygame
import sys

SONIDO_DIR = "Resources/Sonidos"

# =======================
# COMPONENTE: SONIDO
# =======================
class Sonido:
    reproducirMusica = bool = False
    musica = None

    def __init__(self):
        self.reproducirMusica = False
        pygame.mixer.init()  # importante para cargar audio
        
    def cargarFicherosAudio(self, ruta, fichero):
        return pygame.mixer.Sound(ruta+fichero)

    def reproducir_alerta(self):
        if not self.reproduciendo:
            print("🔊 ALERTA activada")
            self.reproducirMusica = True

    def detener_alerta(self):
        if self.reproduciendo:
            print("🔇 ALERTA detenida")
            self.reproducirMusica = False