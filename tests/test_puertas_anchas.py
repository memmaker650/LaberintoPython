# Puertas de 2 o 3 casillas: 2 o 3 casillas de puerta seguidas son una sola puerta, tanto al cargar
# el nivel (levels_parser) como en el juego (MazeLab/Laberinto) y en MazeMapCreator.
import json

import pygame
import pytest

import Laberinto
import MazeLab
from Laberinto import BIAS, CASILLA_PIXEL
from levels_parser import LevelParser, agruparPuertas, tramosPuertas
from test_laberinto import app, ejecutar, mover_jugador, teclas  # noqa: F401 (fixtures)

ANCHO, ALTO = 40, 27


# ---------- Agrupar ----------

def test_puerta_suelta():
    assert agruparPuertas({(3, 4)}) == [[(3, 4)]]


def test_puertas_seguidas_en_fila_y_en_columna():
    assert agruparPuertas({(5, 10), (6, 10)}) == [[(5, 10), (6, 10)]]
    assert agruparPuertas({(20, 5), (20, 3), (20, 4)}) == [[(20, 3), (20, 4), (20, 5)]]


def test_puertas_separadas_no_se_juntan():
    assert agruparPuertas({(1, 1), (3, 1), (1, 3)}) == [[(1, 1)], [(3, 1)], [(1, 3)]]


def test_mas_de_3_se_parten():
    fila = {(x, 2) for x in range(1, 6)}
    assert tramosPuertas(fila) == [[(x, 2) for x in range(1, 6)]]
    assert agruparPuertas(fila) == [[(1, 2), (2, 2), (3, 2)], [(4, 2), (5, 2)]]


# ---------- Nivel ----------

def nivel(carpeta, puertas, nombre="Level_9.json"):
    # Sala con borde de pared. Una pared en la fila 10 con un paso de 2 casillas (columnas 5 y 6) y
    # otra en la columna 20 (filas 11 a 25) con un paso de 3 casillas (filas 12 a 14).
    fondo = [[2 if x in (0, ANCHO - 1) or y in (0, ALTO - 1) else 1 for x in range(ANCHO)] for y in range(ALTO)]
    for x in range(1, ANCHO - 1):
        if x not in (5, 6):
            fondo[10][x] = 2
    for y in range(11, ALTO - 1):
        if y not in (12, 13, 14):
            fondo[y][20] = 2
    objetos = [fila[:] for fila in fondo]
    for x, y in puertas:
        objetos[y][x] = 4
    objetos[ALTO - 2][ALTO - 2] = 3
    datos = {"tileNames": ["Floor", "Wall", "Exit", "Door"], "width": ANCHO, "height": ALTO, "tileWidth": 32,
             "tileHeight": 32, "playerSpawnX": 5, "playerSpawnY": 5,
             "layers": [{"name": "Background", "tiles": fondo}, {"name": "Objects", "tiles": objetos}]}
    (carpeta / nombre).write_text(json.dumps(datos), encoding="utf-8")
    return LevelParser(str(carpeta)).load_by_name(nombre)


PUERTAS = [(5, 10), (6, 10), (20, 12), (20, 13), (20, 14)]


def test_el_parser_crea_una_sola_puerta_por_grupo(tmp_path):
    datos = nivel(tmp_path, PUERTAS)
    assert datos.puertas() == [[(5, 10), (6, 10)], [(20, 12), (20, 13), (20, 14)]]
    assert not [p for p in datos.analizar() if "puerta" in p.lower()]


def test_el_parser_avisa_de_puertas_de_mas_de_3(tmp_path):
    datos = nivel(tmp_path, [(x, 3) for x in range(2, 6)])
    assert any("de más de 3 casillas" in p and "de 4 en (2, 3)" in p for p in datos.analizar())


# ---------- Juego ----------

@pytest.fixture
def juego_puertas(app, tmp_path):
    app.prepararNivel(nivel(tmp_path, PUERTAS))
    app.on_init()
    app.on_render()                     # el primer repintado del mapa crea las puertas
    app.enemigosArray = []
    app.EnemigosGroup.empty()
    app.JefeEnemigo.kill()
    yield app
    MazeLab.Maze()


def puerta_en(app, columna, fila):
    casilla = fila * MazeLab.NUM_CASILLAS_H + columna
    return next(p for p in app.maze.MazePuertas if casilla in p.casillas)


def test_el_juego_crea_una_puerta_por_grupo(juego_puertas):
    m = juego_puertas.maze
    assert len(m.MazePuertas) == 2
    ancha, alta = puerta_en(juego_puertas, 5, 10), puerta_en(juego_puertas, 20, 13)
    assert ancha is puerta_en(juego_puertas, 6, 10) and alta is puerta_en(juego_puertas, 20, 12)
    assert ancha.casillas == [10 * ANCHO + 5, 10 * ANCHO + 6] and ancha.casilla == 10 * ANCHO + 5
    assert alta.casillas == [r * ANCHO + 20 for r in (12, 13, 14)]
    # Cerrada, la hoja cruza todas sus casillas por la mitad.
    assert ancha.orientacion == 4 and ancha.rect.width == 2 * CASILLA_PIXEL
    assert ancha.rect.left == 5 * CASILLA_PIXEL and ancha.rect.centery == BIAS + 10 * CASILLA_PIXEL + 16
    assert alta.orientacion == 1 and alta.rect.height == 3 * CASILLA_PIXEL
    assert alta.rect.top == BIAS + 12 * CASILLA_PIXEL and alta.rect.centerx == 20 * CASILLA_PIXEL + 16
    assert sorted(c for c, _ in m.posicionPuerta) == sorted([ancha.casilla, alta.casilla])


def bajar(app, columna, pasos=60):
    mover_jugador(app, columna * CASILLA_PIXEL + 5, BIAS + 7 * CASILLA_PIXEL + 5)
    for _ in range(pasos):
        app.player.moveDown()
        app.on_loop()
    return (app.player.y - BIAS) // CASILLA_PIXEL


@pytest.mark.parametrize("columna", [5, 6])
def test_cerrada_bloquea_todo_el_pasillo(juego_puertas, columna):
    assert bajar(juego_puertas, columna) < 10


@pytest.mark.parametrize("columna", [5, 6])
def test_abierta_deja_pasar_por_todo_el_pasillo(juego_puertas, columna):
    puerta = puerta_en(juego_puertas, 5, 10)
    puerta.abierta, puerta.angle = True, 90
    puerta.rotar()
    assert bajar(juego_puertas, columna) > 10


def test_la_ia_bloquea_todas_sus_casillas(juego_puertas):
    assert juego_puertas.casillasPuertasCerradas() == {10 * ANCHO + 5, 10 * ANCHO + 6,
                                                     12 * ANCHO + 20, 13 * ANCHO + 20, 14 * ANCHO + 20}
    puerta_en(juego_puertas, 20, 12).abierta = True
    assert juego_puertas.casillasPuertasCerradas() == {10 * ANCHO + 5, 10 * ANCHO + 6}


@pytest.mark.parametrize("columna, fila", [(5, 9), (6, 9), (21, 14), (19, 12)])
def test_tecla_d_abre_la_puerta_desde_cualquiera_de_sus_casillas(monkeypatch, juego_puertas, columna, fila):
    monkeypatch.setattr(juego_puertas, "on_init", lambda: True)
    mover_jugador(juego_puertas, columna * CASILLA_PIXEL + 5, BIAS + fila * CASILLA_PIXEL + 5)
    teclas((pygame.KEYDOWN, pygame.K_d))
    ejecutar(juego_puertas)
    abiertas = [p for p in juego_puertas.maze.MazePuertas if p.abierta]
    assert abiertas == [puerta_en(juego_puertas, columna if columna in (5, 6) else 20, 10 if fila == 9 else 13)]


def test_el_estado_de_la_puerta_se_conserva_al_repintar(juego_puertas):
    puerta = puerta_en(juego_puertas, 6, 10)
    puerta.abierta, puerta.angle = True, 90
    juego_puertas.maze.draw(juego_puertas.map_surface, juego_puertas.floor_surf, juego_puertas.wall_surf)
    nueva = puerta_en(juego_puertas, 6, 10)
    assert nueva is not puerta and nueva.abierta and nueva.angle == 90
