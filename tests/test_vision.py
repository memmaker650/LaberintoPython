# Visión de los enemigos: cono que se corta en paredes y puertas, y alarma al ver al jugador.
import math
import types

import pygame
import pytest

import KerberosIA
import Laberinto
import Luces
import MazeLab
import player
from test_laberinto import Salida, app, enemigos_normales  # noqa: F401
from test_niveles import nivel_real

H = MazeLab.NUM_CASILLAS_H
PASO = {0: -H, 1: 1, 2: H, 3: -1}
ALCANCE = 4 * 32


def distancia(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ================= Rayos compartidos (Luces.py) =================
def test_lanzarRayo_funcion():
    pared = pygame.Rect(480, 480, 32, 40)
    assert Luces.lanzarRayo((400, 500), 0, 200, [pared]) == pytest.approx((480, 500))
    assert Luces.lanzarRayo((400, 500), 0, 200, [pared], penetracion=10) == pytest.approx((490, 500))
    assert Luces.lanzarRayo((400, 500), 180, 200, [pared]) == pytest.approx((200, 500))


def test_abanicoRayos():
    puntos = Luces.abanicoRayos((400, 400), 90, 60, 7, 100, [])
    assert len(puntos) == 7
    angulos = [math.degrees(math.atan2(y - 400, x - 400)) for x, y in puntos]
    assert angulos[0] == pytest.approx(60) and angulos[-1] == pytest.approx(120)


def test_obstaculosCercanos():
    cerca, lejos, encima = pygame.Rect(420, 400, 10, 10), pygame.Rect(800, 800, 10, 10), pygame.Rect(395, 395, 10, 10)
    assert Luces.obstaculosCercanos((400, 400), 50, [cerca, lejos, encima]) == [cerca]


# ================= VisionEnemigo =================
@pytest.fixture
def vision():
    v = KerberosIA.VisionEnemigo(alcance=ALCANCE, apertura=60, num_rayos=15)
    v.actualizar((400, 400), 0, [])  # mirando a la derecha
    return v


def test_cono_sin_paredes(vision):
    assert len(vision.puntos) == 15
    assert all(distancia(p, (400, 400)) == pytest.approx(ALCANCE) for p in vision.puntos)
    assert vision.poligono()[0] == (400, 400) and len(vision.poligono()) == 16


def test_cono_se_corta_en_las_paredes():
    pared = pygame.Rect(450, 300, 32, 200)
    v = KerberosIA.VisionEnemigo(alcance=ALCANCE)
    v.actualizar((400, 400), 0, [pared])
    # clipline devuelve enteros: el corte puede pasar unas centésimas de la pared.
    assert all(p[0] <= 451 for p in v.puntos)
    assert v.puntos[len(v.puntos) // 2] == pytest.approx((450, 400))


@pytest.mark.parametrize("punto, visto", [
    ((480, 400), True),            # delante
    ((400 + ALCANCE, 400), True),  # justo al alcance
    ((400 + ALCANCE + 2, 400), False),  # demasiado lejos
    ((480, 440), True),            # dentro del ángulo (≈27º)
    ((440, 480), False),           # fuera del ángulo (≈63º)
    ((330, 400), False),           # detrás
    ((400, 400), True),            # encima del enemigo
])
def test_ve(vision, punto, visto):
    assert vision.ve(punto, []) is visto


def test_no_ve_a_traves_de_paredes(vision):
    pared = pygame.Rect(440, 380, 10, 40)
    assert vision.ve((480, 400), [pared]) is False
    assert vision.ve((430, 400), [pared]) is True     # antes de la pared sí


def test_ve_con_angulo_que_da_la_vuelta():
    v = KerberosIA.VisionEnemigo(alcance=ALCANCE, apertura=60)
    v.actualizar((400, 400), 350, [])
    assert v.angulo == 350
    assert v.ve((480, 400 + 10), []) is True      # a +7º, con el cono centrado en -10º
    v.actualizar((400, 400), -90, [])             # se normaliza a 270º (arriba)
    assert v.angulo == 270 and v.ve((400, 320), []) is True


# ================= Estados de la IA =================
def test_estados_definidos():
    assert (KerberosIA.ESTADO_PATRULLA, KerberosIA.ESTADO_PERSECUCION, KerberosIA.ESTADO_ALARMA,
            KerberosIA.ESTADO_EQUIPO) == (0, 1, 2, 3)
    ia = KerberosIA.KerberosIA()
    assert ia.estado == KerberosIA.ESTADO_PATRULLA and ia.nombreEstado() == "patrulla"


def test_ver_jugador_da_la_alarma_una_vez():
    ia = KerberosIA.KerberosIA()
    assert ia.verJugador(1000) is True
    assert ia.estado == KerberosIA.ESTADO_ALARMA and ia.alarma is True
    assert ia.nombreEstado() == "alarma"
    assert ia.verJugador(1500) is False       # sigue viéndolo: no vuelve a avisar
    assert ia.ultimaVezVisto == 1500


def test_alarma_se_apaga_tras_no_verlo():
    ia = KerberosIA.KerberosIA()
    ia.verJugador(1000)
    ia.actualizarAlarma(1000 + KerberosIA.DURACION_ALARMA_MS - 1)
    assert ia.estado == KerberosIA.ESTADO_ALARMA
    ia.actualizarAlarma(1000 + KerberosIA.DURACION_ALARMA_MS)
    assert ia.estado == KerberosIA.ESTADO_PATRULLA and ia.alarma is False
    assert ia.verJugador(9000) is True        # si lo vuelve a ver, avisa otra vez


def test_actualizarAlarma_en_patrulla_no_hace_nada():
    ia = KerberosIA.KerberosIA()
    ia.actualizarAlarma(10 ** 9)
    assert ia.estado == KerberosIA.ESTADO_PATRULLA


# ================= Enemigos =================
@pytest.mark.parametrize("orientacion, angulo", [(0, 270), (1, 0), (2, 90), (3, 180)])
def test_enemigo_mira_hacia_donde_camina(orientacion, angulo):
    e = player.Enemigo()
    e.orientacion = orientacion
    assert e.anguloVision() == angulo


def test_jefe_barre_girando():
    j = player.Enemigo()
    j.isJefeEnemigo = True
    j.angle = 123
    assert j.anguloVision() == 123
    j.visionRotar()
    assert j.anguloVision() == pytest.approx(124.5)


def test_metodo_vision_sigue_disponible():
    e = player.Enemigo()
    assert isinstance(e.conoVision, KerberosIA.VisionEnemigo)
    assert e.vision((0, 0)) is None


# ================= En el juego =================
@pytest.fixture
def juego(app):
    app.prepararNivel(nivel_real(0))
    app.on_init()
    app.on_render()
    return app


def libre(app, c):
    return 0 <= c < len(app.maze.MazeLaberinto) and app.maze.MazeLaberinto[c] == 1


def buscar(app, patron):
    # Primera casilla visible y dirección en las que las casillas siguientes cumplen el patrón
    # ('.' suelo, '#' pared).
    for c in range(len(app.maze.MazeLaberinto)):
        if not libre(app, c) or not MazeLab.Maze.elementoVisibleCasilla(c):
            continue
        for d, paso in PASO.items():
            casillas = [c + paso * (i + 1) for i in range(len(patron))]
            if all(MazeLab.Maze.elementoVisibleCasilla(x) and libre(app, x) == (t == ".")
                   for x, t in zip(casillas, patron)):
                return c, d, casillas
    raise AssertionError(f"no hay ninguna casilla con el patrón {patron}")


def colocar(sprite, casilla):
    pos = MazeLab.Maze.centroCasilla(casilla)
    sprite.x, sprite.y = pos.x - sprite.rect.width // 2, pos.y - sprite.rect.height // 2
    sprite.rect.topleft = (sprite.x, sprite.y)


def preparar(app, patron, distancia_jugador):
    # Un enemigo mirando en la dirección del patrón y el jugador a 'distancia_jugador' casillas.
    origen, d, casillas = buscar(app, patron)
    vigilante = enemigos_normales(app)[0]
    for otro in list(app.EnemigosGroup):
        if otro is not vigilante:
            otro.kill()
    colocar(vigilante, origen)
    vigilante.orientacion = d
    colocar(app.player, casillas[distancia_jugador - 1])
    return vigilante


def test_enemigo_ve_al_jugador_y_da_la_alarma(monkeypatch, juego):
    sonidos = []
    monkeypatch.setattr(juego, "sonidoAlarma", types.SimpleNamespace(play=lambda **k: sonidos.append(k)))
    vigilante = preparar(juego, "...", 3)
    # El jefe, en la misma casilla que el vigilante pero mirando hacia el otro lado (no ve al jugador).
    jefe = juego.JefeEnemigo
    juego.EnemigosGroup.add(jefe)
    colocar(jefe, MazeLab.Maze.calcularCasilla(*vigilante.rect.center))
    jefe.angle = (vigilante.anguloVision() + 180) % 360
    juego.vigilar()
    assert jefe.kia.estado == KerberosIA.ESTADO_PATRULLA
    assert vigilante.kia.estado == KerberosIA.ESTADO_ALARMA
    assert vigilante.alarma is True
    assert sonidos == [{"maxtime": 1500}]
    assert jefe.kia.playerDetectado is True
    assert jefe.kia.casillaJugador == MazeLab.Maze.calcularCasilla(*juego.player.rect.center)
    juego.vigilar()                                    # lo sigue viendo: no repite la alarma
    assert len(sonidos) == 1


def test_enemigo_no_ve_a_traves_de_la_pared(juego):
    vigilante = preparar(juego, "#.", 2)               # pared en medio, jugador a 2 casillas
    juego.vigilar()
    assert vigilante.kia.estado == KerberosIA.ESTADO_PATRULLA
    assert vigilante.conoVision.ve(juego.player.rect.center, [s.rect for s in juego.maze.MazeParedes]) is False


def test_enemigo_no_ve_lo_que_tiene_detras(juego):
    vigilante = preparar(juego, "..", 2)
    vigilante.orientacion = (vigilante.orientacion + 2) % 4   # da la espalda
    juego.vigilar()
    assert vigilante.kia.estado == KerberosIA.ESTADO_PATRULLA


def test_enemigo_no_ve_lejos(juego):
    vigilante = preparar(juego, ".....", 5)            # 5 casillas = 160 px > alcance (128)
    juego.vigilar()
    assert vigilante.kia.estado == KerberosIA.ESTADO_PATRULLA


def test_puerta_corta_la_vision(juego):
    vigilante = preparar(juego, "...", 3)
    entre = MazeLab.Maze.centroCasilla(MazeLab.Maze.calcularCasilla(*vigilante.rect.center))
    medio = ((entre.x + juego.player.rect.centerx) // 2, (entre.y + juego.player.rect.centery) // 2)
    puerta = MazeLab.Puerta(medio[0], medio[1], 1)
    puerta.rect = pygame.Rect(0, 0, 20, 20)
    puerta.rect.center = medio
    juego.maze.MazePuertas.add(puerta)
    juego.vigilar()
    assert vigilante.kia.estado == KerberosIA.ESTADO_PATRULLA


def test_alarma_vuelve_a_patrulla(monkeypatch, juego):
    vigilante = preparar(juego, "...", 3)
    juego.vigilar()
    assert vigilante.kia.estado == KerberosIA.ESTADO_ALARMA
    juego.player.rect.topleft = (2000, 2000)           # el jugador se esconde
    juego.vigilar()
    assert vigilante.kia.estado == KerberosIA.ESTADO_ALARMA
    vigilante.kia.ultimaVezVisto -= KerberosIA.DURACION_ALARMA_MS
    juego.vigilar()
    assert vigilante.kia.estado == KerberosIA.ESTADO_PATRULLA


def test_jefe_tambien_vigila(monkeypatch, juego):
    jefe = juego.JefeEnemigo
    for e in enemigos_normales(juego):
        e.kill()
    origen, d, casillas = buscar(juego, "...")
    colocar(jefe, origen)
    jefe.angle = Luces.ANGULO_ORIENTACION[d]
    colocar(juego.player, casillas[2])
    juego.vigilar()
    assert jefe.kia.estado == KerberosIA.ESTADO_ALARMA and jefe.alarma is True
    assert jefe.kia.playerDetectado is True


def test_alarma_sin_jefe_vivo(juego):
    vigilante = preparar(juego, "...", 3)
    juego.JefeEnemigo.kill()
    juego.vigilar()
    assert vigilante.kia.estado == KerberosIA.ESTADO_ALARMA


def test_cada_enemigo_tiene_su_cono(juego):
    for e in enemigos_normales(juego):
        assert e.conoVision.alcance == Laberinto.ALCANCE_VISION_ENEMIGO
    assert juego.JefeEnemigo.conoVision.alcance == Laberinto.ALCANCE_VISION_JEFE
    juego.on_loop()
    for e in juego.EnemigosGroup:
        assert len(e.conoVision.poligono()) == e.conoVision.num_rayos + 1


# ================= Dibujo =================
def color_en(app, punto):
    return app.pantalla.get_at((round(punto[0]), round(punto[1])))[:3]


def test_conos_se_pintan_y_cambian_de_color(juego):
    vigilante = preparar(juego, "...", 3)
    juego.player.rect.topleft = (2000, 2000)
    juego.vigilar()
    mitad = vigilante.conoVision.puntos[len(vigilante.conoVision.puntos) // 2]
    punto = ((vigilante.rect.centerx + mitad[0]) / 2, (vigilante.rect.centery + mitad[1]) / 2)
    juego.visionEnemigos = False
    juego.on_render()
    sin_cono = color_en(juego, punto)
    juego.visionEnemigos = True
    juego.on_render()
    amarillo = color_en(juego, punto)
    assert amarillo != sin_cono and amarillo[0] > sin_cono[0] and amarillo[2] <= sin_cono[2] + 5
    vigilante.kia.estado = KerberosIA.ESTADO_ALARMA
    juego.on_render()
    rojo = color_en(juego, punto)
    assert rojo[0] > rojo[1] + 40                      # claramente rojizo


def test_bocadillo_de_alarma_del_enemigo(juego):
    vigilante = preparar(juego, "...", 3)
    juego.vigilar()
    juego.on_render()
    bocadillo = (vigilante.rect.centerx, vigilante.rect.top - 20)
    assert color_en(juego, bocadillo) == (255, 255, 255)
    vigilante.bubble_start_time -= Laberinto.DURACION_BOCADILLO_ALARMA_MS
    juego.on_render()
    assert vigilante.alarma is False


def test_enemigos_muertos_no_tienen_cono(juego):
    e = enemigos_normales(juego)[0]
    juego.on_loop()
    e.kill()
    juego.on_render()                                  # no falla y no lo pinta
    assert e not in juego.EnemigosGroup
