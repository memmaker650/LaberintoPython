# Patrulla de los enemigos normales: habitaciones (zonas amplias) y pasillos (tramos estrechos
# entre paredes). Cada enemigo se queda en la zona donde empieza.
import collections
import random

import pygame
import pytest

import KerberosIA
import Laberinto
import MazeLab
import player
from test_laberinto import app, enemigos_normales  # noqa: F401
from test_niveles import nivel_real

H = MazeLab.NUM_CASILLAS_H
PASO = {0: -H, 1: 1, 2: H, 3: -1}


def rejilla(*filas):
    # Laberinto de prueba dentro de la rejilla del juego: '.' suelo, '#' pared.
    laberinto = [0] * (H * MazeLab.NUM_CASILLAS_VERTI)
    for y, fila in enumerate(filas):
        for x, c in enumerate(fila):
            if c == ".":
                laberinto[y * H + x] = 1
    return laberinto


def zonas_de(laberinto):
    return MazeLab.Maze.calcularZonas(laberinto, H, MazeLab.NUM_CASILLAS_VERTI)


def casillas_por_zona(zonas):
    grupos = collections.defaultdict(set)
    for c, z in zonas.items():
        grupos[z].add(c)
    return grupos


# Dos habitaciones 3x3 unidas por un pasillo (fila 2, x=4..8). En x=6 hay un cruce del que sale
# un callejón hacia abajo, así que el pasillo queda en dos tramos: x=4..5 y x=7..8.
DOS_HABITACIONES = rejilla(
    "#############",
    "#...#####...#",
    "#...........#",
    "#...##.##...#",
    "######.######",
    "######.######",
)


# ================= Zonas =================
def test_zonas_habitaciones_y_pasillos():
    zonas, tipos = zonas_de(DOS_HABITACIONES)
    grupos = casillas_por_zona(zonas)
    por_tipo = collections.Counter(tipos.values())
    assert por_tipo == {"habitacion": 2, "pasillo": 3, "cruce": 1}
    izquierda = zonas[1 * H + 1]
    assert tipos[izquierda] == "habitacion" and grupos[izquierda] == {y * H + x for y in (1, 2, 3) for x in (1, 2, 3)}
    assert tipos[zonas[1 * H + 9]] == "habitacion" and zonas[1 * H + 9] != izquierda
    assert tipos[zonas[2 * H + 6]] == "cruce"            # del pasillo sale el callejón hacia abajo
    assert grupos[zonas[2 * H + 4]] == {2 * H + 4, 2 * H + 5}   # tramo izquierdo
    assert grupos[zonas[2 * H + 7]] == {2 * H + 7, 2 * H + 8}   # tramo derecho
    assert grupos[zonas[5 * H + 6]] == {3 * H + 6, 4 * H + 6, 5 * H + 6}  # callejón
    assert all(tipos[zonas[c]] == "pasillo" for c in (2 * H + 4, 2 * H + 7, 5 * H + 6))


def test_pasillo_de_dos_de_ancho_es_habitacion():
    zonas, tipos = zonas_de(rejilla("######", "#....#", "#....#", "######"))
    assert set(tipos.values()) == {"habitacion"} and len(tipos) == 1


def test_zonas_no_cruzan_el_borde_de_la_fila():
    laberinto = [0] * (H * 3)
    laberinto[H - 1] = laberinto[H] = 1  # última de la fila 0 y primera de la fila 1
    zonas, tipos = MazeLab.Maze.calcularZonas(laberinto, H, 3)
    assert zonas[H - 1] != zonas[H]


@pytest.mark.parametrize("nivel", [None, 0, 1, 2])
def test_zonas_en_los_laberintos_reales(nivel):
    m = MazeLab.Maze(None if nivel is None else nivel_real(nivel))
    zonas, tipos = zonas_de(m.maze)
    suelo = {c for c, v in enumerate(m.maze) if v == 1}
    assert set(zonas) == suelo
    for c, z in zonas.items():
        x, y = c % H, c // H
        en_bloque = any(all(m.maze[(y0 + dy) * H + x0 + dx] == 1 for dx in (0, 1) for dy in (0, 1))
                        for x0, y0 in ((x, y), (x - 1, y), (x, y - 1), (x - 1, y - 1)))
        assert (tipos[z] == "habitacion") == en_bloque
    # Cada tramo de pasillo es una línea: ninguna casilla tiene más de 2 vecinas en su tramo.
    for c, z in zonas.items():
        if tipos[z] == "pasillo":
            assert sum(1 for d in PASO.values() if zonas.get(c + d) == z) <= 2


def test_level_1_es_una_sola_habitacion():
    zonas, tipos = zonas_de(MazeLab.Maze(nivel_real(1)).maze)
    assert list(tipos.values()) == ["habitacion"]


# ================= IA de patrulla =================
def ia_en(laberinto, casilla, orientacion):
    zonas, tipos = zonas_de(laberinto)
    ia = KerberosIA.KerberosIA()
    ia.conexiones = MazeLab.Maze.precalcular_conexiones(laberinto, H, MazeLab.NUM_CASILLAS_VERTI)
    ia.asignarZona(zonas, tipos, casilla)
    ia.orientacion = orientacion
    return ia


def andar(ia, pasos):
    # Simula la patrulla casilla a casilla y devuelve las casillas visitadas, en orden.
    visitadas = [ia.casilla]
    for _ in range(pasos):
        d = ia.direccionPatrulla()
        if d is None:
            break
        ia.orientacion = d
        ia.casilla += PASO[d]
        visitadas.append(ia.casilla)
    return visitadas


def test_pasillo_sigue_recto_y_da_la_vuelta_al_final():
    # Tramo derecho (x=7..8): a la derecha está la habitación y a la izquierda el cruce.
    ia = ia_en(DOS_HABITACIONES, 2 * H + 7, 1)
    assert ia.tipoZona() == "pasillo"
    assert andar(ia, 4) == [2 * H + 7, 2 * H + 8, 2 * H + 7, 2 * H + 8, 2 * H + 7]


def test_callejon_va_y_vuelve():
    ia = ia_en(DOS_HABITACIONES, 3 * H + 6, 2)
    assert andar(ia, 4) == [3 * H + 6, 4 * H + 6, 5 * H + 6, 4 * H + 6, 3 * H + 6]


def test_pasillo_recorre_curvas():
    laberinto = rejilla(
        "#######",
        "#.....#",
        "#####.#",
        "#####.#",
        "#######",
    )
    ia = ia_en(laberinto, 1 * H + 1, 2)
    visitadas = andar(ia, 12)
    tramo = {1 * H + x for x in range(1, 6)} | {2 * H + 5, 3 * H + 5}
    assert set(visitadas) == tramo                    # lo recorre entero, de extremo a extremo
    assert visitadas[6] == 3 * H + 5 and visitadas[12] == 1 * H + 1


def test_habitacion_no_sale_de_ella():
    random.seed(3)
    ia = ia_en(DOS_HABITACIONES, 2 * H + 2, 1)
    visitadas = andar(ia, 500)
    assert set(visitadas) <= {y * H + x for y in (1, 2, 3) for x in (1, 2, 3)}
    assert len(set(visitadas)) >= 7                   # se mueve por toda la habitación


def test_zona_de_una_casilla_no_se_mueve():
    ia = ia_en(DOS_HABITACIONES, 2 * H + 6, 1)       # el cruce
    assert ia.direccionPatrulla() is None


def test_sin_zonas_no_patrulla():
    ia = KerberosIA.KerberosIA()
    assert ia.direccionPatrulla() is None and ia.tipoZona() is None


@pytest.mark.parametrize("nivel", [None, 0, 2])
def test_patrulla_simulada_en_todo_el_laberinto(nivel):
    # Desde cada zona con sitio para moverse: el enemigo nunca sale de ella y los pasillos se recorren enteros.
    random.seed(7)
    m = MazeLab.Maze(None if nivel is None else nivel_real(nivel))
    zonas, tipos = zonas_de(m.maze)
    grupos = casillas_por_zona(zonas)
    for z, casillas in grupos.items():
        if tipos[z] == "cruce" or len(casillas) < 2:
            continue
        ia = ia_en(m.maze, min(casillas), 2)
        visitadas = andar(ia, 6 * len(casillas))
        assert set(visitadas) <= casillas
        if tipos[z] == "pasillo":
            assert set(visitadas) == casillas


# ================= Enemigos en el juego =================
@pytest.fixture
def juego(app):
    app.on_init()
    app.on_render()
    return app


def centro(e):
    return e.x + e.rect.width // 2, e.y + e.rect.height // 2


def test_enemigos_empiezan_en_el_centro_de_su_zona(juego):
    for e in enemigos_normales(juego):
        assert MazeLab.Maze.estaCentroCasilla(*centro(e))
        assert e.kia.zona == juego.zonas[e.casilla]
        assert juego.tiposZona[e.kia.zona] != "cruce"
        assert sum(1 for z in juego.zonas.values() if z == e.kia.zona) >= 2


def test_enemigos_patrullan_sin_salir_de_su_zona(juego):
    # Sin jugador cerca, durante 25 segundos de juego cada enemigo se mueve y se queda en su zona.
    for e in enemigos_normales(juego):
        e.visitadas = set()
    juego.player.x, juego.player.y = juego.player.prev_x, juego.player.prev_y = 900, 900
    for _ in range(1500):
        juego.on_loop()
        for e in enemigos_normales(juego):
            casilla = MazeLab.Maze.calcularCasilla(*centro(e))
            assert juego.zonas.get(casilla) == e.kia.zona, "un enemigo ha salido de su zona"
            e.visitadas.add(casilla)
    for e in enemigos_normales(juego):
        assert len(e.visitadas) >= 2, "un enemigo no se ha movido"


def test_enemigo_de_pasillo_lo_recorre_entero(app):
    # Coloca un enemigo en el tramo de pasillo más largo del laberinto y comprueba que llega a los dos extremos.
    app.prepararNivel(nivel_real(0))
    app.on_init()
    grupos = casillas_por_zona(app.zonas)
    pasillo = max((z for z in grupos if app.tiposZona[z] == "pasillo"), key=lambda z: len(grupos[z]))
    e = enemigos_normales(app)[0]
    inicio = min(grupos[pasillo])
    pos = MazeLab.Maze.centroCasilla(inicio)
    e.x, e.y = pos.x - 11, pos.y - 11
    e.kia.asignarZona(app.zonas, app.tiposZona, inicio)
    for otro in enemigos_normales(app)[1:] + [app.JefeEnemigo]:
        otro.kill()
    app.player.x = app.player.y = app.player.prev_x = app.player.prev_y = 900
    visitadas = set()
    for _ in range(32 * 2 * len(grupos[pasillo]) + 64):
        app.on_loop()
        visitadas.add(MazeLab.Maze.calcularCasilla(*centro(e)))
    assert visitadas == grupos[pasillo]


def test_media_vuelta_al_chocar_con_puerta(juego):
    e = enemigos_normales(juego)[0]
    e.orientacion = 1
    e.cambiar_direccion()
    assert e.orientacion == 3 and e.speedH == 1 and e.speedV == 1
    x = e.x
    e.kia.zonas = None  # sin IA: sigue en su dirección (izquierda)
    e.patrullar()
    assert e.x == x - 1


def test_partida_restaurada_conserva_la_zona(monkeypatch, juego):
    estado = juego.estadoPartida()
    for nombre in ("enemigosArray", "EnemigosGroup", "PlayerGroup"):
        monkeypatch.setattr(Laberinto.App, nombre, [] if nombre == "enemigosArray" else pygame.sprite.Group())
    otra = Laberinto.App()
    otra.restaurarPartida(estado)
    for original, copia in zip(enemigos_normales(juego), enemigos_normales(otra)):
        assert copia.kia.zona == otra.zonas[copia.casilla]
        assert otra.tiposZona[copia.kia.zona] == juego.tiposZona[original.kia.zona]
