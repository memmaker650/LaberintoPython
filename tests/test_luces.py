# Linterna de los niveles oscuros (Code/Luces.py) y su uso en el juego.
import math

import pygame
import pytest

import Luces
import MazeLab
from levels_parser import LevelParser
from test_laberinto import app  # noqa: F401 (fixture)
from test_niveles import LEVELS_DIR, nivel_real

BIAS = MazeLab.BIAS
ZONA = (0, BIAS, 864, 1000 - BIAS)


@pytest.fixture
def linterna():
    return Luces.Linterna(ZONA, opacidad=0.9, alcance=200, apertura=60, num_rayos=31, penetracion=10)


def alfa(linterna, x, y):
    # Alfa de la oscuridad en un punto de pantalla (0 = iluminado del todo).
    return linterna.oscuridad.get_at((round(x) - linterna.zona.x, round(y) - linterna.zona.y)).a


def distancia(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ---------- Dirección del haz ----------
@pytest.mark.parametrize("orientacion, angulo", [(0, 270), (1, 0), (2, 90), (3, 180)])
def test_apuntar_instantaneo(linterna, orientacion, angulo):
    linterna.apuntar(orientacion, instantaneo=True)
    assert linterna.angulo == angulo


def test_apuntar_gira_poco_a_poco_por_el_camino_corto(linterna):
    linterna.apuntar(1, instantaneo=True)        # derecha (0º)
    linterna.apuntar(0)                          # hacia arriba (270º): gira -15º
    assert linterna.angulo == 345
    for _ in range(10):
        linterna.apuntar(0)
    assert linterna.angulo == 270


def test_apuntar_orientacion_desconocida_no_cambia(linterna):
    linterna.apuntar(2, instantaneo=True)
    linterna.apuntar("N")
    assert linterna.angulo == 90


def test_opacidad(linterna):
    assert linterna.alfa_oscuridad == 230
    assert Luces.Linterna(ZONA, opacidad=0.5).alfa_oscuridad == 128


# ---------- Rayos ----------
def test_rayo_sin_obstaculos_llega_al_alcance(linterna):
    fin = linterna.lanzarRayo((400, 500), 0, [])
    assert fin == pytest.approx((600, 500))


def test_rayo_se_para_en_el_obstaculo(linterna):
    pared = pygame.Rect(480, 480, 32, 40)
    fin = linterna.lanzarRayo((400, 500), 0, [pared])
    assert fin == pytest.approx((490, 500))      # entra en x=480 + 10 px de penetración


def test_rayo_usa_el_obstaculo_mas_cercano(linterna):
    cerca, lejos = pygame.Rect(450, 490, 10, 20), pygame.Rect(520, 490, 10, 20)
    assert linterna.lanzarRayo((400, 500), 0, [lejos, cerca]) == pytest.approx((460, 500))


def test_rayo_ignora_obstaculos_detras(linterna):
    detras = pygame.Rect(300, 490, 32, 20)
    assert linterna.lanzarRayo((400, 500), 0, [detras]) == pytest.approx((600, 500))


def test_rayo_penetracion_no_supera_el_alcance(linterna):
    al_final = pygame.Rect(595, 490, 20, 20)
    assert linterna.lanzarRayo((400, 500), 0, [al_final]) == pytest.approx((600, 500))


# ---------- Haz completo ----------
def test_calcularHaz_abanico(linterna):
    linterna.apuntar(2, instantaneo=True)        # hacia abajo
    origen = (400, 400)
    puntos = linterna.calcularHaz(origen, [])
    assert len(puntos) == 31
    angulos = [math.degrees(math.atan2(y - origen[1], x - origen[0])) for x, y in puntos]
    assert min(angulos) == pytest.approx(60) and max(angulos) == pytest.approx(120)
    assert angulos[15] == pytest.approx(90)
    assert all(distancia(p, origen) == pytest.approx(200) for p in puntos)


def test_calcularHaz_ignora_obstaculo_que_contiene_al_jugador(linterna):
    encima = pygame.Rect(390, 390, 22, 22)
    puntos = linterna.calcularHaz((400, 400), [encima])
    assert all(distancia(p, (400, 400)) == pytest.approx(200) for p in puntos)


def test_calcularHaz_descarta_obstaculos_fuera_de_alcance(linterna, monkeypatch):
    lejos = pygame.Rect(800, 900, 32, 32)
    vistos = []
    original = linterna.lanzarRayo
    monkeypatch.setattr(linterna, "lanzarRayo", lambda o, a, obs: vistos.append(list(obs)) or original(o, a, obs))
    linterna.calcularHaz((100, 300), [lejos])
    assert all(obs == [] for obs in vistos)


# ---------- Oscuridad ----------
def test_dibujar_oscurece_salvo_el_haz(linterna):
    pantalla = pygame.Surface((864, 1000))
    linterna.apuntar(1, instantaneo=True)        # derecha
    linterna.dibujar(pantalla, (400, 500), [])
    assert alfa(linterna, 400, 500) == 0          # halo del jugador
    assert alfa(linterna, 480, 500) == 0          # cerca, dentro del haz
    assert alfa(linterna, 530, 500) == 60         # a 3/4 del alcance: algo de penumbra
    assert 0 < alfa(linterna, 580, 500) < 230     # al final del haz: penumbra
    assert alfa(linterna, 300, 500) == 230        # detrás del jugador
    assert alfa(linterna, 480, 650) == 230        # fuera del abanico
    assert alfa(linterna, 700, 500) == 230        # más allá del alcance


@pytest.mark.parametrize("nombre", ["pared", "enemigo", "puerta"])
def test_dibujar_no_atraviesa_obstaculos(linterna, nombre):
    # Cualquier obstáculo (rect de pared, enemigo o puerta) deja a oscuras lo que hay detrás.
    tamanos = {"pared": (32, 32), "enemigo": (22, 22), "puerta": (15, 32)}
    obstaculo = pygame.Rect((0, 0), tamanos[nombre])
    obstaculo.center = (480, 500)
    linterna.apuntar(1, instantaneo=True)
    linterna.dibujar(pygame.Surface((864, 1000)), (400, 500), [obstaculo])
    assert alfa(linterna, 450, 500) == 0                       # antes del obstáculo: luz
    assert alfa(linterna, obstaculo.left + 3, 500) == 0        # su borde se ve
    assert alfa(linterna, obstaculo.right + 20, 500) == 230    # detrás: oscuro


def test_dibujar_solo_oscurece_la_zona_del_laberinto(linterna):
    pantalla = pygame.Surface((864, 1000))
    pantalla.fill((200, 200, 200))
    linterna.dibujar(pantalla, (400, 500), [])
    assert pantalla.get_at((400, 50))[:3] == (200, 200, 200)          # HUD intacto
    assert pantalla.get_at((100, 900))[:3] == (20, 20, 20)            # 90% de oscuridad


# ---------- Datos del nivel ----------
def test_level_2_es_oscuro_y_los_demas_no():
    niveles = {n: nivel_real(n) for n in range(6)}
    assert niveles[2].oscuridad == 0.9
    assert all(niveles[n].oscuridad == 0 for n in (0, 1, 3, 4, 5))


def test_oscuridad_fuera_de_rango(tmp_path):
    import json
    from test_niveles import FONDO_OK, NOMBRES, OBJETOS_OK
    datos = {"tileNames": NOMBRES, "width": 5, "height": 4, "tileWidth": 32, "tileHeight": 32,
             "playerSpawnX": 1, "playerSpawnY": 1, "oscuridad": 1.5,
             "layers": [{"name": "Background", "tiles": FONDO_OK}, {"name": "Objects", "tiles": OBJETOS_OK}]}
    (tmp_path / "Level_1.json").write_text(json.dumps(datos), encoding="utf-8")
    with pytest.raises(ValueError, match="oscuridad"):
        LevelParser(str(tmp_path)).load_by_name("Level_1.json")


# ---------- En el juego ----------
def test_nivel_iluminado_sin_linterna(app):
    app.prepararNivel(nivel_real(0))
    assert app.linterna is None and app.oscuridad == 0
    app.prepararNivel()
    assert app.linterna is None


def jugar_nivel_2(app, frames=3):
    app.prepararNivel(nivel_real(2))
    app.on_init()
    for _ in range(frames):
        app.on_loop()
        app.on_render()


def test_level_2_crea_la_linterna(app):
    jugar_nivel_2(app)
    assert app.linterna is not None
    assert app.linterna.alfa_oscuridad == 230
    assert app.linterna.zona == pygame.Rect(0, BIAS, 864, 1000 - BIAS)


def test_level_2_oscurece_la_pantalla(app):
    jugar_nivel_2(app)
    # Lejos del jugador (esquina inferior izquierda) la oscuridad es máxima.
    assert alfa(app.linterna, 100, 900) == 230
    assert max(app.pantalla.get_at((100, 900))[:3]) <= 30
    # El jugador se ve.
    assert alfa(app.linterna, *app.player.rect.center) == 0


def test_level_2_linterna_sigue_al_jugador(app):
    jugar_nivel_2(app)
    app.player.orientacion = 2
    for _ in range(10):
        app.on_render()
    assert app.linterna.angulo == 90
    origen = app.player.rect.center
    # Con un número par de rayos el central se desvía medio paso (≈0,6º): tolerancia de 2 px.
    centro_haz = app.linterna.haz[len(app.linterna.haz) // 2]
    assert centro_haz[0] == pytest.approx(origen[0], abs=2) and centro_haz[1] > origen[1]


def test_level_2_obstaculos_del_juego(app, monkeypatch):
    # La linterna recibe paredes, enemigos (incluido el jefe) y puertas como obstáculos.
    jugar_nivel_2(app, frames=1)
    recibidos = []
    monkeypatch.setattr(app.linterna, "dibujar", lambda p, o, obs: recibidos.extend(obs))
    app.on_render()
    rects = {tuple(r) for r in recibidos}
    assert {tuple(s.rect) for s in app.maze.MazeParedes} <= rects
    assert {tuple(s.rect) for s in app.EnemigosGroup} <= rects
    assert tuple(app.JefeEnemigo.rect) in rects
    assert {tuple(p.rect) for p in app.maze.MazePuertas} <= rects


def test_level_2_enemigo_tapa_la_luz(app):
    jugar_nivel_2(app, frames=2)  # el rect del jugador se actualiza en el on_loop siguiente a colocarlo
    # Jugador mirando a la izquierda por el pasillo de la fila 1 y un enemigo a 3 casillas.
    app.player.orientacion = 3
    app.linterna.apuntar(3, instantaneo=True)
    enemigo = app.enemigosArray[0]
    esquina = MazeLab.Maze.calcularPixelPorCasilla(app.maze.casillaInicioJugador() - 3)
    enemigo.x, enemigo.y = esquina.x + 5, esquina.y + 5
    enemigo.update = lambda: None
    enemigo.rect.topleft = (enemigo.x, enemigo.y)
    app.on_render()
    cy = app.player.rect.centery
    assert alfa(app.linterna, enemigo.rect.right + 8, cy) == 0     # entre jugador y enemigo
    assert alfa(app.linterna, enemigo.rect.left - 25, cy) == 230   # detrás del enemigo


def test_level_2_pausa_no_pinta_la_linterna(app, monkeypatch):
    jugar_nivel_2(app, frames=1)
    llamadas = []
    monkeypatch.setattr(app.linterna, "dibujar", lambda *a: llamadas.append(1))
    app.pause = True
    app.on_render()
    assert llamadas == []
