import pygame
import pytest

import Sonido


def test_init():
    s = Sonido.Sonido()
    assert s.reproducirMusica is False
    assert pygame.mixer.get_init() is not None


def test_cargarFicherosAudio():
    s = Sonido.Sonido()
    sonido = s.cargarFicherosAudio("./Resources/Sonidos/", "gunshot.mp3")
    assert isinstance(sonido, pygame.mixer.Sound)


def test_cargarFicherosAudio_inexistente():
    s = Sonido.Sonido()
    with pytest.raises((FileNotFoundError, pygame.error)):
        s.cargarFicherosAudio("./Resources/Sonidos/", "no_existe.mp3")


def test_reproducir_alerta():
    s = Sonido.Sonido()
    s.reproducir_alerta()
    assert s.reproducirMusica is True


def test_detener_alerta():
    s = Sonido.Sonido()
    s.reproducirMusica = True
    s.detener_alerta()
    assert s.reproducirMusica is False
