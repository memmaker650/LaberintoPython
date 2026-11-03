import math

import pygame
import pytest

import MazeLab
from MazeLab import Maze, BIAS, CASILLA_PIXEL, NUM_CASILLAS_H, NUM_CASILLAS_VERTI
from conftest import casillas_suelo, _plyer


# ---------- posicion ----------
def test_posicion():
    assert (MazeLab.posicion().x, MazeLab.posicion().y) == (0, 0)
    p = MazeLab.posicion(3, 4)
    assert (p.x, p.y) == (3, 4)


# ---------- Construcción del Maze ----------
def test_maze_dimensiones(maze):
    assert len(maze.MazeLaberinto) == NUM_CASILLAS_H * NUM_CASILLAS_VERTI
    assert len(maze.mazeDataExtra) == len(maze.MazeLaberinto)
    assert maze.MazeLaberinto is maze.maze


def test_maze_crea_una_pared_por_cada_cero(maze):
    assert len(maze.MazeParedes) == maze.maze.count(0)


def test_maze_paredes_en_su_posicion(maze):
    rects = {(s.rect.x, s.rect.y) for s in maze.MazeParedes}
    assert (0, BIAS) in rects                         # casilla 0 es pared
    assert (CASILLA_PIXEL, BIAS + CASILLA_PIXEL) not in rects  # casilla 41 es suelo


def test_maze_lanza_notificacion():
    _plyer.notificaciones.clear()
    Maze()
    assert _plyer.notificaciones and _plyer.notificaciones[0]["title"] == "Maze created"


# ---------- Conversión casilla <-> píxel ----------
@pytest.mark.parametrize("x, y, casilla", [
    (0, BIAS, 0),
    (31, BIAS + 31, 0),
    (32, BIAS, 1),
    (0, BIAS + 32, NUM_CASILLAS_H),
    (5 * 32 + 10, BIAS + 3 * 32 + 10, 5 + 3 * NUM_CASILLAS_H),
])
def test_calcularCasilla(x, y, casilla):
    assert Maze.calcularCasilla(x, y) == casilla


@pytest.mark.parametrize("casilla", [0, 1, 41, 977, NUM_CASILLAS_H * NUM_CASILLAS_VERTI - 1])
def test_calcularPixelPorCasilla_ida_y_vuelta(casilla):
    pos = Maze.calcularPixelPorCasilla(casilla)
    assert pos.x == (casilla % NUM_CASILLAS_H) * CASILLA_PIXEL
    assert pos.y == (casilla // NUM_CASILLAS_H) * CASILLA_PIXEL + BIAS
    assert Maze.calcularCasilla(pos.x, pos.y) == casilla


@pytest.mark.parametrize("casilla", [0, 41, 977])
def test_centroCasilla(casilla):
    pos = Maze.centroCasilla(casilla)
    esquina = Maze.calcularPixelPorCasilla(casilla)
    assert (pos.x, pos.y) == (esquina.x + 16, esquina.y + 16)
    assert Maze.calcularCasilla(pos.x, pos.y) == casilla
    # Guarda la posición de la cruz y del recuadro para pintar.
    assert Maze.PosicionCruz is pos
    assert (Maze.PosicionPintarCasilla.x, Maze.PosicionPintarCasilla.y) == (esquina.x, esquina.y)


def test_estaCentroCasilla():
    x, y = Maze.centroCasilla(41).x, Maze.centroCasilla(41).y
    assert Maze.estaCentroCasilla(x, y) is True
    assert Maze.estaCentroCasilla(x + 1, y) is False
    assert Maze.estaCentroCasilla(x, y - 1) is False


@pytest.mark.parametrize("casilla, visible", [(0, True), (26, True), (27, False), (39, False), (66, True)])
def test_elementoVisibleCasilla(casilla, visible):
    assert Maze.elementoVisibleCasilla(casilla) is visible


def test_elementoVisiblePosicion():
    assert Maze.elementoVisiblePosicion(10, BIAS + 10) is True
    assert Maze.elementoVisiblePosicion(30 * 32, BIAS + 10) is False


# ---------- esAlcanzable ----------
def test_esAlcanzable_suelo_y_pared(maze):
    assert maze.esAlcanzable(32 + 5, BIAS + 32 + 5) is True   # casilla 41: suelo
    assert maze.esAlcanzable(5, BIAS + 5) is False             # casilla 0: pared


@pytest.mark.parametrize("x, y", [(-1, 300), (MazeLab.ANCHO_MUNDO, 300), (100, -5), (100, 1001)])
def test_esAlcanzable_fuera_de_pantalla(maze, x, y):
    assert maze.esAlcanzable(x, y) is False


def test_esAlcanzable_zona_cabecera(maze):
    # (40, 10) está en la cabecera (HUD), nunca debería ser alcanzable.
    assert maze.esAlcanzable(40, 10) is False


def test_esAlcanzable_zona_derecha_del_mundo(maze):
    # Coordenadas del mundo: la zona derecha (x > 864) también existe.
    assert maze.esAlcanzable(33 * 32 + 5, BIAS + 20 * 32 + 5) is True


def test_esAlcanzableCasilla(maze):
    assert maze.esAlcanzableCasilla(41) is True
    assert maze.esAlcanzableCasilla(0) is False


# ---------- precalcular_conexiones ----------
def test_precalcular_conexiones_grid_pequeno():
    # 3x3:  1 1 0
    #       1 0 0
    #       1 1 1
    grid = [1, 1, 0,
            1, 0, 0,
            1, 1, 1]
    con = Maze.precalcular_conexiones(grid, 3, 3)
    assert con == {
        0: [1, 2],
        1: [3],
        3: [0, 2],
        6: [0, 1],
        7: [1, 3],
        8: [3],
    }


def test_precalcular_conexiones_no_cruza_bordes():
    # Fila 0 termina en suelo y fila 1 empieza en suelo: no deben conectarse.
    grid = [0, 1,
            1, 0]
    con = Maze.precalcular_conexiones(grid, 2, 2)
    assert con == {1: [], 2: []}


def test_precalcular_conexiones_laberinto_real_simetricas(maze, conexiones):
    assert set(conexiones) == set(casillas_suelo(maze))
    opuesta = {0: 2, 1: 3, 2: 0, 3: 1}
    paso = {0: -NUM_CASILLAS_H, 1: 1, 2: NUM_CASILLAS_H, 3: -1}
    for casilla, dirs in conexiones.items():
        for d in dirs:
            vecina = casilla + paso[d]
            assert maze.maze[vecina] == 1
            assert opuesta[d] in conexiones[vecina]


# ---------- Cámara ----------
# camaraX = x del mundo que se ve en el borde izquierdo de la pantalla (864 px = 27 casillas).
ANCHO = MazeLab.ANCHO_MUNDO
DERECHA = 864 - MazeLab.MARGEN_CAMARA - CASILLA_PIXEL   # a partir de aquí la cámara se mueve


def test_camara_quieta_lejos_de_los_bordes(maze):
    assert maze.camaraX == 0
    assert maze.moverCamara(400) == 0
    assert maze.moverCamara(DERECHA) == 0


def test_camara_sigue_al_jugador_a_la_derecha(maze):
    assert maze.moverCamara(DERECHA + 10) == 10
    assert maze.moverCamara(DERECHA + 100) == 100


def test_camara_no_se_sale_del_laberinto(maze):
    assert maze.moverCamara(ANCHO - 20) == ANCHO - 864           # 1280 - 864 = 416
    assert maze.moverCamara(-50) == 0


def test_camara_vuelve_a_la_izquierda(maze):
    maze.moverCamara(DERECHA + 300)
    assert maze.camaraX == 300
    assert maze.moverCamara(300 + MazeLab.MARGEN_CAMARA + 10) == 300   # todavía en pantalla
    assert maze.moverCamara(300 + MazeLab.MARGEN_CAMARA - 40) == 260
    assert maze.moverCamara(0) == 0


def test_camara_fija(maze):
    maze.camaraFija = True
    assert maze.moverCamara(ANCHO - 20) == 0


def test_nuevaCasillaTrasCamaraMovida(maze):
    for casilla in (0, 41, 500):
        assert maze.nuevaCasillaTrasCamaraMovida(casilla) == casilla


def test_nuevaPosicionXYTrasCamaraMovida(maze):
    pos = maze.nuevaPosicionXYTrasCamaraMovida(100, 200)
    assert (pos.x, pos.y) == (68, 200)


# ---------- Dibujo ----------
def _visibles(maze, valor):
    # Con la cámara, draw() pinta y crea los objetos de TODO el laberinto (también la zona derecha).
    return [i for i, v in enumerate(maze.mazeDataExtra) if v == valor]


def test_draw_pinta_suelo_y_paredes(maze, superficie):
    suelo = pygame.Surface((32, 32)); suelo.fill((10, 200, 10))
    pared = pygame.Surface((32, 32)); pared.fill((200, 10, 10))
    Maze.pintaKasillaNumSuelo = False
    try:
        maze.draw(superficie, suelo, pared)
    finally:
        Maze.pintaKasillaNumSuelo = True
    assert superficie.get_at((5, BIAS + 5))[:3] == (200, 10, 10)        # casilla 0
    assert superficie.get_at((32 + 5, BIAS + 32 + 5))[:3] == (10, 200, 10)  # casilla 41


def test_draw_crea_objetos_y_puertas(maze, superficie):
    suelo = pygame.Surface((32, 32))
    maze.draw(superficie, suelo, suelo)
    assert maze.posicionInitJugador == _visibles(maze, 44)[0] == 977
    assert len(maze.MazePuertas) == len(_visibles(maze, 33))
    assert {c for c, _ in maze.posicionPuerta} == set(_visibles(maze, 33))
    for c, orient in maze.posicionPuerta:
        horizontal = not maze.esAlcanzableCasilla(c - 1) and not maze.esAlcanzableCasilla(c + 1)
        assert orient == (4 if horizontal else 1)
    assert len(maze.MazeHueso) == len(_visibles(maze, 2))
    assert len(maze.MazePilaHuesos) == len(_visibles(maze, 3))
    assert len(maze.MazeBandera) == len(_visibles(maze, 4))
    assert len(maze.MazeLlave) == len(_visibles(maze, 6))
    assert len(maze.MazeLlavePuerta) == len(_visibles(maze, 7))
    assert len(maze.MazeChampi) == len(_visibles(maze, 8))
    assert len(maze.MazeRedStar) == len(_visibles(maze, 9))
    assert len(maze.MazeTunnel) == len(_visibles(maze, 10))
    assert len(maze.MazeOro) == len(_visibles(maze, 11))
    assert len(maze.MazeGranada) == len(_visibles(maze, 13))
    assert len(maze.MazeBotiquin) == len(_visibles(maze, 15))


def test_draw_respeta_objetos_cogidos(maze, superficie):
    suelo = pygame.Surface((32, 32))
    huesos = _visibles(maze, 2)
    oros = _visibles(maze, 11)
    maze.draw(superficie, suelo, suelo, {huesos[0], oros[0]})
    assert len(maze.MazeHueso) == len(huesos) - 1
    assert len(maze.MazeOro) == len(oros) - 1


def test_draw_respeta_flags(maze, superficie):
    suelo = pygame.Surface((32, 32))
    maze.flagBotiquin = False
    maze.flagLlave = False
    maze.draw(superficie, suelo, suelo)
    assert len(maze.MazeBotiquin) == 0
    assert len(maze.MazeLlave) == 0


def test_draw_pinta_la_zona_derecha_en_coordenadas_del_mundo(maze):
    # La zona derecha (columnas 27-39) se pinta a partir de x = 864 en la superficie del mundo.
    mundo = pygame.Surface((MazeLab.ANCHO_MUNDO, 1000))
    suelo = pygame.Surface((32, 32)); suelo.fill((10, 200, 10))
    pared = pygame.Surface((32, 32)); pared.fill((200, 10, 10))
    Maze.pintaKasillaNumSuelo = False
    try:
        maze.draw(mundo, suelo, pared)
    finally:
        Maze.pintaKasillaNumSuelo = True
    c = 20 * NUM_CASILLAS_H + 33                       # fila 20, columna 33: suelo
    assert maze.maze[c] == 1
    assert mundo.get_at((33 * 32 + 5, BIAS + 20 * 32 + 5))[:3] == (10, 200, 10)
    assert mundo.get_at((39 * 32 + 5, BIAS + 5))[:3] == (200, 10, 10)
    assert 395 in {c for c, _ in maze.posicionPuerta}  # la puerta de la columna 35 también existe


def test_addText(maze):
    maze.addText("hola", 0, 0)
    assert isinstance(maze.font, pygame.font.Font)


def test_pintarDetallesCasillaEnemigo(maze, superficie):
    Maze.centroCasilla(41)
    maze.pintarDetallesCasillaEnemigo(superficie)
    cx, cy = Maze.PosicionCruz.x, Maze.PosicionCruz.y
    assert superficie.get_at((cx, cy))[:3] == (0, 255, 0)
    # Recuadro naranja de la casilla.
    esquina = Maze.PosicionPintarCasilla
    assert superficie.get_at((esquina.x, esquina.y))[:3] == (244, 127, 38)


# ---------- Explosion ----------
def test_explosion_carga_frames():
    e = MazeLab.Explosion(400, 300)
    assert len(e.frames) == 21
    assert e.image is e.frames[0]
    assert e.rect.center == (400, 300)
    assert e.frames[0].get_size() == (128, 128)


def test_explosion_update_avanza_y_termina():
    grupo = pygame.sprite.Group()
    e = MazeLab.Explosion(100, 100)
    grupo.add(e)
    e.update()  # aún no ha pasado el tiempo
    assert e.frame_actual == 0
    for i in range(1, 21):
        e.tiempo_ultimo_frame = -10_000
        e.update()
        assert e.frame_actual == i
        assert e.image is e.frames[i]
    e.tiempo_ultimo_frame = -10_000
    e.update()
    assert not grupo.has(e)


# ---------- Smoke ----------
def test_smoke_carga_frames_una_vez():
    MazeLab.Smoke.FRAMES = None
    s1 = MazeLab.Smoke(200, 200, alfa=100)
    frames = MazeLab.Smoke.FRAMES
    assert len(frames) == 31
    s2 = MazeLab.Smoke(300, 300)
    assert s2.frames is frames is s1.frames
    assert s1.rect.center == (200, 200)


def test_smoke_update_crece_y_se_desvanece():
    grupo = pygame.sprite.Group()
    s = MazeLab.Smoke(200, 200)
    grupo.add(s)
    s.tiempo_ultimo_frame = -10_000
    s.update()
    assert s.frame_actual == 1
    assert s.image.get_size() == (141, 141)
    assert s.image.get_alpha() == 207
    assert s.rect.center == (200, 200)
    for _ in range(30):
        s.tiempo_ultimo_frame = -10_000
        s.update()
    assert not grupo.has(s)


# ---------- Puerta ----------
def test_puerta_init():
    p = MazeLab.Puerta(100, 200, 1, casilla=55)
    assert (p.orientacion, p.casilla) == (1, 55)
    assert p.image_original.get_size() == (15, 32)
    assert p.angle == 0 and p.abierta is False
    assert p.pivot == (100, 200)
    # Vertical (1) cerrada: la hoja baja desde la bisagra, 'radio' píxeles en el eje Y.
    assert p.rect.center == (100, 216)
    assert p.image.get_size() == (15, 32)


def test_puerta_horizontal_init():
    p = MazeLab.Puerta(100, 200, 4)
    # Horizontal (4) cerrada: la hoja sale hacia la derecha de la bisagra.
    assert p.rect.center == (116, 200)
    assert p.image.get_size() == (32, 15)


@pytest.mark.parametrize("orientacion, abierta", [(1, (116, 200)), (4, (100, 216))])
def test_puerta_abrir_y_cerrar(orientacion, abierta):
    p = MazeLab.Puerta(100, 200, orientacion)
    cerrada = p.rect.center
    p.abierta = True
    for _ in range(60):
        p.update()
    assert p.angle == 90
    assert p.rect.center == abierta
    p.abierta = False
    p.update()
    assert p.angle == 88
    for _ in range(60):
        p.update()
    assert p.angle == 0
    assert p.rect.center == cerrada


def test_puerta_rotar_tamano():
    p = MazeLab.Puerta(100, 200, 4)
    p.angle = 90
    p.rotar()
    assert p.image.get_size() == (15, 32)
    p.angle = 0
    p.rotar()
    assert p.image.get_size() == (32, 15)


def test_puertas_centradas_en_su_casilla(maze, superficie):
    # Cerradas, la bisagra está en mitad del lado de la pared y la hoja cruza la casilla por el centro.
    maze.draw(superficie, pygame.Surface((32, 32)), pygame.Surface((32, 32)))
    assert maze.MazePuertas
    for puerta in maze.MazePuertas:
        columna, fila = puerta.casilla % NUM_CASILLAS_H, puerta.casilla // NUM_CASILLAS_H
        casilla = pygame.Rect(columna * CASILLA_PIXEL, fila * CASILLA_PIXEL + BIAS, CASILLA_PIXEL, CASILLA_PIXEL)
        assert puerta.rect.center == casilla.center
        if puerta.orientacion == 1:
            assert puerta.pivot == casilla.midtop
        else:
            assert puerta.pivot == casilla.midleft


def test_puerta_draw(superficie):
    p = MazeLab.Puerta(100, 200, 1)
    p.draw(superficie)
    assert superficie.get_at((100, 200))[:3] == (128, 128, 128)  # bisagra
    assert superficie.get_at(p.rect.center)[:3] != (0, 0, 0)


def test_numeros_de_casilla_encima_de_los_objetos(maze, superficie):
    # Los números se pintan al final: ni los objetos de la casilla ni el suelo de la siguiente los tapan.
    suelo = pygame.Surface((32, 32))
    suelo.fill((90, 90, 90))
    Maze.pintaKasillaNumSuelo = True
    maze.draw(superficie, suelo, suelo)
    hueso = _visibles(maze, 2)[0]
    centro = Maze.centroCasilla(hueso)
    zona = pygame.Rect(centro.x, centro.y, 24, 14)  # donde empieza el número
    rojos = [p for p in ((x, y) for x in range(zona.left, zona.right) for y in range(zona.top, zona.bottom))
             if superficie.get_at(p)[:3] == (255, 0, 0)]
    assert rojos


def test_sin_numeros_de_casilla(maze, superficie):
    suelo = pygame.Surface((32, 32))
    suelo.fill((90, 90, 90))
    Maze.pintaKasillaNumSuelo = False
    try:
        maze.draw(superficie, suelo, suelo)
    finally:
        Maze.pintaKasillaNumSuelo = True
    # Casilla 42: suelo sin objetos. Sin números no hay nada rojo en ella.
    esquina = Maze.calcularPixelPorCasilla(42)
    assert maze.mazeDataExtra[42] == 1
    assert not any(superficie.get_at((esquina.x + dx, esquina.y + dy))[:3] == (255, 0, 0)
                   for dx in range(32) for dy in range(32))
