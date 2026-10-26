# Configuración común de los tests del Laberinto.
# - Pygame sin ventana ni audio reales (drivers "dummy").
# - Directorio de trabajo = raíz del repositorio (los recursos se cargan con rutas relativas).
# - plyer sustituido por un módulo falso para no lanzar notificaciones de escritorio.
import os
import sys
import types
import random

import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CODE_DIR = os.path.join(RAIZ, "Code")

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

os.chdir(RAIZ)
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

# plyer falso: notification.notify no hace nada y guarda las llamadas.
_plyer = types.ModuleType("plyer")
_plyer.notificaciones = []
_plyer.notification = types.SimpleNamespace(notify=lambda **k: _plyer.notificaciones.append(k))
_plyer.orientation = None
sys.modules["plyer"] = _plyer

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((864, 1000))

import MazeLab  # noqa: E402
import player  # noqa: E402
import KerberosIA  # noqa: E402


def _vaciar_grupos_maze():
    # Los grupos de sprites de Maze son atributos de clase: se acumulan entre instancias.
    for nombre, valor in vars(MazeLab.Maze).items():
        if isinstance(valor, pygame.sprite.Group):
            valor.empty()


@pytest.fixture(autouse=True)
def entorno_limpio():
    random.seed(1234)
    if not pygame.display.get_init() or pygame.display.get_surface() is None:
        pygame.init()
        pygame.display.set_mode((864, 1000))
    _vaciar_grupos_maze()
    player.Player.balas.empty()
    player.Enemigo.balas.empty()
    yield
    _vaciar_grupos_maze()


_obtener_eventos = pygame.event.get


@pytest.fixture(autouse=True)
def eventos_sin_bloqueo(monkeypatch):
    # Los menús y el diálogo esperan eventos en un bucle infinito. Si un test se queda
    # esperando eventos que nunca llegan, falla en vez de bloquear toda la suite.
    vacios = [0]

    def obtener(*args, **kwargs):
        eventos = _obtener_eventos(*args, **kwargs)
        vacios[0] = 0 if eventos else vacios[0] + 1
        if vacios[0] > 600:
            raise RuntimeError("El test espera eventos de pygame que nunca llegan (bucle bloqueado)")
        return eventos
    monkeypatch.setattr(pygame.event, "get", obtener)


@pytest.fixture
def maze():
    return MazeLab.Maze()


@pytest.fixture
def conexiones(maze):
    return MazeLab.Maze.precalcular_conexiones(
        maze.MazeLaberinto, MazeLab.NUM_CASILLAS_H, MazeLab.NUM_CASILLAS_VERTI
    )


@pytest.fixture
def superficie():
    return pygame.Surface((864, 1000))


def centro(casilla):
    # Centro en píxeles de una casilla (atajo para los tests).
    pos = MazeLab.Maze.centroCasilla(casilla)
    return pos.x, pos.y


def casillas_suelo(maze):
    return [i for i, v in enumerate(maze.MazeLaberinto) if v == 1]
