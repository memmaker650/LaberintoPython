# Niveles más grandes que la pantalla: la rejilla crece con el nivel (hasta 64x64) y la cámara
# también se desplaza en vertical.
import json

import pygame
import pytest

import Laberinto
import MazeLab
from Laberinto import BIAS, CASILLA_PIXEL
from levels_parser import LevelParser
from test_laberinto import app, juego, mover_jugador  # noqa: F401 (fixtures)

ANCHO, ALTO = 48, 40


def nivel_grande(carpeta, ancho=ANCHO, alto=ALTO, nombre="Level_9.json"):
    # Suelo con borde de pared, unas paredes interiores para que haya zonas, la salida abajo a la derecha.
    fondo = [[2 if x in (0, ancho - 1) or y in (0, alto - 1) else 1 for x in range(ancho)] for y in range(alto)]
    for y in range(1, alto - 1):
        if y % 6 == 0:
            for x in range(1, ancho - 3):
                fondo[y][x] = 2
    objetos = [[0] * ancho for _ in range(alto)]
    objetos[alto - 2][ancho - 2] = 3    # Exit
    datos = {"tileNames": ["Floor", "Wall", "Exit"], "width": ancho, "height": alto, "tileWidth": 32,
             "tileHeight": 32, "playerSpawnX": 1, "playerSpawnY": 1,
             "layers": [{"name": "Background", "tiles": fondo}, {"name": "Objects", "tiles": objetos}]}
    (carpeta / nombre).write_text(json.dumps(datos), encoding="utf-8")
    return LevelParser(str(carpeta)).load_by_name(nombre)


@pytest.fixture
def grande(app, tmp_path):
    app.prepararNivel(nivel_grande(tmp_path))
    app.on_init()
    app.on_render()
    yield app
    MazeLab.Maze()          # deja la rejilla por defecto (40x27) para el resto de tests


def centro(casilla):
    p = MazeLab.Maze.centroCasilla(casilla)
    return p.x, p.y


# ---------- Rejilla y superficies ----------

def test_la_rejilla_crece_con_el_nivel(grande):
    assert (MazeLab.NUM_CASILLAS_H, MazeLab.NUM_CASILLAS_VERTI) == (ANCHO, ALTO)
    assert (grande.maze.M, grande.maze.N) == (ANCHO, ALTO)
    assert len(grande.maze.MazeLaberinto) == ANCHO * ALTO
    assert MazeLab.ANCHO_MUNDO == ANCHO * CASILLA_PIXEL and MazeLab.ALTO_MUNDO == BIAS + ALTO * CASILLA_PIXEL
    assert grande.mundo.get_size() == grande.map_surface.get_size() == (MazeLab.ANCHO_MUNDO, MazeLab.ALTO_MUNDO)
    # La salida está en la última fila de suelo: casilla = fila * ancho + columna.
    assert grande.maze.mazeDataExtra[(ALTO - 2) * ANCHO + ANCHO - 2] == 4


def test_el_laberinto_por_defecto_vuelve_a_40x27(grande):
    MazeLab.Maze()
    assert (MazeLab.NUM_CASILLAS_H, MazeLab.NUM_CASILLAS_VERTI) == (40, 27)
    assert MazeLab.ALTO_MUNDO == 1000 and MazeLab.ANCHO_MUNDO == 1280


@pytest.mark.parametrize("n", [0, 1, 2, 4, 5])
def test_los_niveles_actuales_siguen_en_40x27(n):
    MazeLab.Maze(LevelParser(Laberinto.DIR_NIVELES).load_by_name(f"Level_{n}.json"))
    assert (MazeLab.NUM_CASILLAS_H, MazeLab.NUM_CASILLAS_VERTI) == (40, 27)


def test_maximo_64x64(tmp_path):
    MazeLab.Maze(nivel_grande(tmp_path, 64, 64))
    assert (MazeLab.NUM_CASILLAS_H, MazeLab.NUM_CASILLAS_VERTI) == (64, 64)
    with pytest.raises(ValueError, match="máximo es 64x64"):
        MazeLab.Maze(nivel_grande(tmp_path, 40, 65, "Level_8.json"))
    MazeLab.Maze()


def test_las_superficies_solo_se_rehacen_si_cambia_el_tamano(app, tmp_path):
    mundo = app.mundo
    app.prepararNivel()
    assert app.mundo is mundo
    app.prepararNivel(nivel_grande(tmp_path))
    assert app.mundo is not mundo
    MazeLab.Maze()


# ---------- Cámara vertical ----------

def test_camara_vertical_sigue_al_jugador(grande):
    m = grande.maze
    abajo = 1000 - MazeLab.MARGEN_CAMARA - CASILLA_PIXEL          # y en pantalla a partir de la que baja
    assert m.moverCamara(100, 500) == 0 and m.camaraY == 0
    m.moverCamara(100, abajo + 40)
    assert m.camaraY == 40
    m.moverCamara(100, abajo + 40 + 10)                          # sigue bajando con el jugador
    assert m.camaraY == 50
    m.moverCamara(100, 50 + BIAS + MazeLab.MARGEN_CAMARA + 5)    # todavía en pantalla: no se mueve
    assert m.camaraY == 50
    m.moverCamara(100, 50 + BIAS + MazeLab.MARGEN_CAMARA - 20)   # sube
    assert m.camaraY == 30
    m.moverCamara(100, 10 ** 6)                                 # no pasa del final del mundo
    assert m.camaraY == MazeLab.ALTO_MUNDO - 1000
    m.moverCamara(100, 0)
    assert m.camaraY == 0


def test_camara_vertical_quieta_en_niveles_de_27_filas(juego):
    for y in (BIAS, 500, 990):
        juego.maze.moverCamara(100, y)
        assert juego.maze.camaraY == 0


def test_moverCamara_sin_y_no_mueve_en_vertical(grande):
    grande.maze.camaraY = 120
    grande.maze.moverCamara(100)
    assert grande.maze.camaraY == 120


def test_jugador_baja_hasta_el_final(grande):
    for e in list(grande.EnemigosGroup):
        e.kill()
    # Columna 45: la única sin paredes interiores, de arriba abajo.
    x, y = centro(ANCHO + ANCHO - 3)
    mover_jugador(grande, x - 11, y - 11)
    for _ in range(1500):
        grande.player.moveDown()
        grande.on_loop()
    fila = MazeLab.Maze.calcularCasilla(*grande.player.rect.center) // ANCHO
    assert fila == ALTO - 2                                      # la última fila de suelo
    assert grande.maze.camaraY == MazeLab.ALTO_MUNDO - 1000
    grande.on_render()


def test_render_pinta_lo_que_ve_la_camara_en_vertical(grande):
    grande.maze.camaraX, grande.maze.camaraY = 200, 300
    grande.on_render()
    for x, y in ((10, 300), (500, 600), (850, 990)):
        assert grande.pantalla.get_at((x, y)) == grande.mundo.get_at((x + 200, y + 300))


def test_balas_no_desaparecen_por_debajo_de_la_pantalla(grande):
    import player
    bala = player.Disparos(100, 1200, True, 2)
    player.Player.balas.add(bala)
    bala.update()
    assert bala.alive()
    bala.rect.y = MazeLab.ALTO_MUNDO + 1
    bala.update()
    assert not bala.alive()


def test_conos_en_una_capa_del_tamano_de_la_pantalla(grande):
    grande.maze.camaraX, grande.maze.camaraY = 200, 300
    grande.on_render()
    assert grande.superficieConos.get_size() == (864, 1000)


def test_la_linterna_sigue_a_la_camara(grande):
    import Luces
    grande.linterna = Luces.Linterna((0, BIAS, 864, 1000 - BIAS), opacidad=0.9)
    grande.oscuridad = 0.9
    grande.maze.camaraX, grande.maze.camaraY = 200, 300
    grande.on_render()
    assert grande.linterna.zona.topleft == (200, 300 + BIAS)


def test_guardar_y_continuar_un_nivel_grande(app, tmp_path, monkeypatch):
    monkeypatch.setattr(Laberinto, "DIR_NIVELES", str(tmp_path))
    app.prepararNivel(nivel_grande(tmp_path))
    app.on_init()
    x, y = centro((ALTO - 3) * ANCHO + 10)
    mover_jugador(app, x - 11, y - 11)
    app.on_loop()
    estado = app.estadoPartida()
    assert estado["fichero"] == "Level_9.json" and estado["camaraY"] == app.maze.camaraY > 0
    app.prepararNivel()                                          # otro nivel (40x27) entre medias
    app.restaurarPartida(estado)
    assert (MazeLab.NUM_CASILLAS_H, MazeLab.NUM_CASILLAS_VERTI) == (ANCHO, ALTO)
    assert app.maze.camaraY == estado["camaraY"] and app.mundo.get_height() == MazeLab.ALTO_MUNDO
    MazeLab.Maze()
