# El nivel puede marcar dónde empieza el jefe enemigo ('Boss' en la capa Objects). Si no lo marca,
# el juego lo coloca al azar como siempre.
import json

import pytest

import MazeLab
from levels_parser import JEFE, LevelParser
from test_laberinto import app  # noqa: F401 (fixture)

ANCHO, ALTO = 30, 20


def nivel(carpeta, jefes=(), nombre="Level_9.json"):
    fondo = [[2 if x in (0, ANCHO - 1) or y in (0, ALTO - 1) else 1 for x in range(ANCHO)] for y in range(ALTO)]
    objetos = [fila[:] for fila in fondo]
    for x, y in jefes:
        objetos[y][x] = 4
    objetos[ALTO - 2][ANCHO - 2] = 3
    datos = {"tileNames": ["Floor", "Wall", "Exit", JEFE], "width": ANCHO, "height": ALTO, "tileWidth": 32,
             "tileHeight": 32, "playerSpawnX": 1, "playerSpawnY": 1,
             "layers": [{"name": "Background", "tiles": fondo}, {"name": "Objects", "tiles": objetos}]}
    (carpeta / nombre).write_text(json.dumps(datos), encoding="utf-8")
    return LevelParser(str(carpeta)).load_by_name(nombre)


def casilla(x, y):
    # Un nivel de 30x20 se dibuja con un marco de una casilla en la rejilla de 40x27.
    return (y + 1) * MazeLab.NUM_CASILLAS_H + x + 1


def test_el_parser_conoce_al_jefe(tmp_path):
    datos = nivel(tmp_path, [(20, 10)])
    assert datos.objetos()[JEFE] == [(20, 10)]
    assert datos.analizar() == []


def test_el_parser_avisa_si_hay_mas_de_un_jefe(tmp_path):
    datos = nivel(tmp_path, [(20, 10), (5, 15)])
    assert any("2 jefes" in p for p in datos.analizar())


def test_el_maze_guarda_la_casilla_del_jefe(tmp_path):
    assert MazeLab.Maze(nivel(tmp_path, [(20, 10)])).posicionJefe == casilla(20, 10)
    assert MazeLab.Maze(nivel(tmp_path)).posicionJefe is None
    assert MazeLab.Maze().posicionJefe is None
    MazeLab.Maze()


@pytest.mark.parametrize("repeticion", range(5))
def test_el_jefe_empieza_donde_dice_el_nivel(app, tmp_path, repeticion):
    app.prepararNivel(nivel(tmp_path, [(20, 10)]))
    jefe = app.JefeEnemigo
    assert jefe.casilla == casilla(20, 10) and jefe.kia.casilla == casilla(20, 10)
    assert MazeLab.Maze.calcularCasilla(*jefe.rect.center) == casilla(20, 10)
    assert all(e.casilla != casilla(20, 10) for e in app.enemigosArray if not e.isJefeEnemigo)
    MazeLab.Maze()


def test_sin_jefe_en_el_nivel_se_coloca_al_azar(app, tmp_path):
    app.prepararNivel(nivel(tmp_path))
    assert app.maze.MazeLaberinto[app.JefeEnemigo.casilla] == 1
    MazeLab.Maze()
