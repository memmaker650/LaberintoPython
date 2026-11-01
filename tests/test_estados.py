# Estados de los enemigos: normal (ronda), alerta (ha oído un ruido) y alarma (ha visto o tocado
# al jugador). Ruidos: disparos, balas contra las paredes y el grito de alarma de otro enemigo.
import types

import pygame
import pytest

import KerberosIA
import Laberinto
import MazeLab
import player
from KerberosIA import ESTADO_ALARMA, ESTADO_ALERTA, ESTADO_NORMAL
from test_laberinto import Salida, app, enemigos_normales, mover_jugador  # noqa: F401
from test_vision import buscar, colocar

H = MazeLab.NUM_CASILLAS_H
RADIO = KerberosIA.RADIO_RUIDO_CASILLAS


# ================= Propagación del sonido =================
def conexiones_de(*filas):
    laberinto = [0] * (H * MazeLab.NUM_CASILLAS_VERTI)
    for y, fila in enumerate(filas):
        for x, c in enumerate(fila):
            if c == ".":
                laberinto[y * H + x] = 1
    return MazeLab.Maze.precalcular_conexiones(laberinto, H, MazeLab.NUM_CASILLAS_VERTI)


PASILLO = conexiones_de("#" * 14, "#............#", "#" * 14)          # fila 1, x = 1..12


def test_sonido_llega_hasta_6_casillas():
    alcanzadas = KerberosIA.propagarSonido(H + 1, PASILLO)
    assert alcanzadas == {H + 1 + i: i for i in range(RADIO + 1)}


def test_sonido_se_para_en_puerta_cerrada():
    alcanzadas = KerberosIA.propagarSonido(H + 1, PASILLO, bloqueadas={H + 4})
    assert set(alcanzadas) == {H + 1, H + 2, H + 3}


def test_sonido_no_atraviesa_paredes():
    # Dos pasillos paralelos separados por una pared: muy cerca en línea recta, pero sin camino.
    con = conexiones_de("#######", "#.....#", "#######", "#.....#", "#######")
    alcanzadas = KerberosIA.propagarSonido(H + 1, con)
    assert 3 * H + 1 not in alcanzadas


def test_sonido_rodea_por_el_laberinto():
    con = conexiones_de("#####", "#...#", "#.#.#", "#...#", "#####")
    alcanzadas = KerberosIA.propagarSonido(H + 1, con, maximo=4)
    assert alcanzadas[3 * H + 3] == 4                     # da la vuelta: 4 casillas de recorrido


# ================= Estados de la IA =================
def test_estado_por_defecto_es_normal():
    ia = KerberosIA.KerberosIA()
    assert ia.estado == ESTADO_NORMAL and ia.nombreEstado() == "normal"
    assert KerberosIA.NOMBRES_ESTADO[ESTADO_ALERTA] == "alerta"


def test_oir_ruido_pasa_a_alerta():
    ia = KerberosIA.KerberosIA()
    assert ia.oirRuido(1000, (10, 20)) is True
    assert ia.estado == ESTADO_ALERTA and ia.puntoRuido == (10, 20) and ia.ultimoRuido == 1000
    assert ia.oirRuido(2000, (30, 40)) is False           # ya estaba alerta: sólo se actualiza
    assert ia.ultimoRuido == 2000 and ia.puntoRuido == (30, 40)


def test_ruido_no_baja_la_alarma():
    ia = KerberosIA.KerberosIA()
    ia.verJugador(1000)
    assert ia.oirRuido(1500, (0, 0)) is False
    assert ia.estado == ESTADO_ALARMA


def test_ver_al_jugador_estando_alerta_da_la_alarma():
    ia = KerberosIA.KerberosIA()
    ia.oirRuido(1000, (0, 0))
    assert ia.verJugador(1200) is True and ia.estado == ESTADO_ALARMA


def test_alerta_vuelve_a_normal_sin_mas_ruidos():
    ia = KerberosIA.KerberosIA()
    ia.oirRuido(1000, (0, 0))
    ia.actualizarEstado(1000 + KerberosIA.DURACION_ALERTA_MS - 1)
    assert ia.estado == ESTADO_ALERTA
    ia.oirRuido(5000, (0, 0))                             # otro ruido: la alerta se alarga
    ia.actualizarEstado(1000 + KerberosIA.DURACION_ALERTA_MS)
    assert ia.estado == ESTADO_ALERTA
    ia.actualizarEstado(5000 + KerberosIA.DURACION_ALERTA_MS)
    assert ia.estado == ESTADO_NORMAL and ia.puntoRuido is None


def test_actualizar_en_normal_no_hace_nada():
    ia = KerberosIA.KerberosIA()
    ia.actualizarEstado(10 ** 9)
    assert ia.estado == ESTADO_NORMAL


# ================= En el juego =================
@pytest.fixture
def juego(app, monkeypatch):
    app.on_init()
    app.on_render()
    monkeypatch.setattr(app, "sonidoAlarma", types.SimpleNamespace(play=lambda **k: None))
    return app


def solo(app, cuantos):
    # Deja vivos sólo 'cuantos' enemigos normales (y quita al jefe) para controlar la prueba.
    vivos = enemigos_normales(app)[:cuantos]
    for e in list(app.EnemigosGroup):
        if e not in vivos:
            e.kill()
    return vivos


def en_casilla(sprite, casilla):
    colocar(sprite, casilla)
    return sprite


# ---------- Ruido de disparos ----------
def test_ruido_cerca_pone_en_alerta_y_lejos_no(juego):
    cerca, lejos = solo(juego, 2)
    punto = (400, 500)
    cerca.rect.center = (400 + RADIO * 32 - 2, 500)
    lejos.rect.center = (400 + RADIO * 32 + 2, 500)
    juego.hacerRuido(punto)
    assert cerca.kia.estado == ESTADO_ALERTA and cerca.kia.puntoRuido == punto
    assert cerca.avisoAlerta_ms is not None
    assert lejos.kia.estado == ESTADO_NORMAL


def test_disparo_se_oye_a_traves_de_paredes(juego):
    # El disparo es fuerte: cuenta la distancia en línea recta aunque haya paredes en medio.
    origen, d, casillas = buscar(juego, "#.")
    oyente, = solo(juego, 1)
    en_casilla(oyente, casillas[1])
    disparo = MazeLab.Maze.centroCasilla(origen)
    juego.hacerRuido((disparo.x, disparo.y))              # a 2 casillas, con una pared en medio
    assert oyente.kia.estado == ESTADO_ALERTA


def test_tecla_espacio_hace_ruido(monkeypatch, juego):
    monkeypatch.setattr(juego, "vigilar", lambda: None)   # que nadie vea al jugador
    oyente, = solo(juego, 1)
    oyente.rect.center = (juego.player.rect.centerx + 64, juego.player.rect.centery)
    oyente.update = lambda: None
    juego.player.municion = 3
    pygame.event.clear()
    for k in (pygame.K_SPACE, pygame.K_ESCAPE):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k))
    with pytest.raises(SystemExit):
        juego.on_execute()
    assert oyente.kia.estado == ESTADO_ALERTA


def test_sin_municion_no_hay_ruido(monkeypatch, juego):
    monkeypatch.setattr(juego, "vigilar", lambda: None)
    oyente, = solo(juego, 1)
    oyente.rect.center = (juego.player.rect.centerx + 64, juego.player.rect.centery)
    oyente.update = lambda: None
    juego.player.municion = 0
    pygame.event.clear()
    for k in (pygame.K_SPACE, pygame.K_ESCAPE):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k))
    with pytest.raises(SystemExit):
        juego.on_execute()
    assert oyente.kia.estado == ESTADO_NORMAL


def test_bala_contra_la_pared_hace_ruido_donde_golpea(monkeypatch, juego):
    monkeypatch.setattr(juego, "vigilar", lambda: None)
    mover_jugador(juego, 40, Laberinto.BIAS + 40)         # jugador arriba a la izquierda
    cerca, lejos = solo(juego, 2)
    for e in (cerca, lejos):
        e.update = lambda: None
    impacto = (840, 900)                                   # lejos del jugador (más de 6 casillas)
    cerca.rect.center = (impacto[0] - 100, impacto[1])
    lejos.rect.center = (40, 400)
    pared = next(p for p in juego.maze.MazeParedes if p.rect.collidepoint(impacto))
    bala = player.Disparos(0, 300, True, 1)
    bala.rect.center = pared.rect.center
    juego.player.balas.add(bala)
    juego.player.flagDisparo = False
    juego.on_loop()
    assert not juego.player.balas.has(bala)
    assert cerca.kia.estado == ESTADO_ALERTA
    assert lejos.kia.estado == ESTADO_NORMAL


# ---------- Grito de alarma ----------
def test_grito_lo_oyen_hasta_6_casillas_de_recorrido(juego):
    origen, d, casillas = buscar(juego, "." * (RADIO + 1))
    quien, cerca, lejos = solo(juego, 3)
    en_casilla(quien, origen)
    en_casilla(cerca, casillas[RADIO - 1])                 # a 6 casillas
    en_casilla(lejos, casillas[RADIO])                     # a 7 casillas
    oyentes = juego.gritarAlarma(quien)
    assert oyentes == [cerca]
    assert cerca.kia.estado == ESTADO_ALERTA and cerca.kia.puntoRuido == quien.rect.center
    assert lejos.kia.estado == ESTADO_NORMAL
    assert quien.kia.estado == ESTADO_NORMAL               # el que grita no se oye a sí mismo


def test_grito_no_atraviesa_paredes(juego):
    origen, d, casillas = buscar(juego, "#.")
    quien, otro = solo(juego, 2)
    en_casilla(quien, origen)
    en_casilla(otro, casillas[1])
    distancia = KerberosIA.propagarSonido(origen, juego.conexiones).get(casillas[1])
    juego.gritarAlarma(quien)
    assert (otro.kia.estado == ESTADO_ALERTA) == (distancia is not None)


@pytest.fixture
def puerta_entre_habitaciones(juego):
    # La puerta de la casilla 967 (laberinto por defecto) es la única salida de la habitación
    # de abajo a la izquierda: a un lado la casilla 965 y al otro la 969.
    puerta = next(p for p in juego.maze.MazePuertas if p.casilla == 967)
    return puerta, 965, 969


def test_grito_no_sale_de_una_habitacion_cerrada(juego, puerta_entre_habitaciones):
    puerta, dentro, fuera = puerta_entre_habitaciones
    assert puerta.abierta is False
    quien, otro = solo(juego, 2)
    en_casilla(quien, dentro)
    en_casilla(otro, fuera)
    assert juego.gritarAlarma(quien) == []
    assert otro.kia.estado == ESTADO_NORMAL


def test_grito_sale_si_la_puerta_esta_abierta(juego, puerta_entre_habitaciones):
    puerta, dentro, fuera = puerta_entre_habitaciones
    puerta.abierta = True
    quien, otro = solo(juego, 2)
    en_casilla(quien, dentro)
    en_casilla(otro, fuera)
    assert juego.gritarAlarma(quien) == [otro]
    assert otro.kia.estado == ESTADO_ALERTA


def test_grito_dentro_de_la_habitacion_cerrada_se_oye(juego, puerta_entre_habitaciones):
    puerta, dentro, fuera = puerta_entre_habitaciones
    quien, otro = solo(juego, 2)
    en_casilla(quien, dentro)
    en_casilla(otro, dentro - 2)
    assert juego.gritarAlarma(quien) == [otro]


def test_ver_al_jugador_hace_gritar(monkeypatch, juego):
    from test_vision import preparar
    vigilante = preparar(juego, "...", 3)
    origen = MazeLab.Maze.calcularCasilla(*vigilante.rect.center)
    alcanzadas = KerberosIA.propagarSonido(origen, juego.conexiones)
    companero = player.Enemigo()
    companero.kia.conexiones = juego.conexiones
    otra = next(c for c, dist in alcanzadas.items() if dist >= 2 and c not in
                {MazeLab.Maze.calcularCasilla(*juego.player.rect.center)})
    en_casilla(companero, otra)
    companero.orientacion = 0
    companero.conoVision.alcance = 1                     # que él no vea al jugador
    juego.EnemigosGroup.add(companero)
    juego.vigilar()
    assert vigilante.kia.estado == ESTADO_ALARMA
    assert companero.kia.estado == ESTADO_ALERTA


def test_tocar_al_jugador_da_la_alarma_y_grita(monkeypatch, juego):
    monkeypatch.setattr(juego, "vigilar", lambda: None)
    tocado, companero = solo(juego, 2)
    origen, d, casillas = buscar(juego, "..")
    en_casilla(tocado, origen)
    en_casilla(companero, casillas[1])
    for e in (tocado, companero):
        e.update = lambda: None
    juego.player.x, juego.player.y = tocado.x, tocado.y
    juego.player.prev_x, juego.player.prev_y = tocado.x, tocado.y
    juego.on_loop()
    assert tocado.kia.estado == ESTADO_ALARMA and tocado.alarma is True
    assert companero.kia.estado == ESTADO_ALERTA


def test_jefe_tambien_oye(juego):
    jefe = juego.JefeEnemigo
    for e in enemigos_normales(juego):
        e.kill()
    jefe.rect.center = (300, 500)
    juego.hacerRuido((330, 500))
    assert jefe.kia.estado == ESTADO_ALERTA


# ---------- Visualización ----------
def test_cono_naranja_en_alerta_y_bocadillo(juego):
    e, = solo(juego, 1)
    juego.on_loop()
    juego.hacerRuido(e.rect.center)
    juego.on_render()
    mitad = e.conoVision.puntos[len(e.conoVision.puntos) // 2]
    punto = (round((e.rect.centerx + mitad[0]) / 2), round((e.rect.centery + mitad[1]) / 2))
    r, g, b = juego.pantalla.get_at(punto)[:3]
    assert r > b + 40 and g > b + 20                     # naranja
    assert juego.pantalla.get_at((e.rect.centerx, e.rect.top - 20))[:3] == (255, 255, 255)  # bocadillo
    e.avisoAlerta_ms -= Laberinto.DURACION_AVISO_ALERTA_MS
    juego.on_render()
    assert e.avisoAlerta_ms is None


def test_colores_de_cono_por_estado():
    assert Laberinto.COLOR_CONO_VISION != Laberinto.COLOR_CONO_ALERTA != Laberinto.COLOR_CONO_ALARMA
