import random

import pytest

import KerberosIA
from MazeLab import NUM_CASILLAS_H as H
from conftest import centro

PASO = {0: -H, 1: 1, 2: H, 3: -1}


@pytest.fixture
def kia(conexiones):
    ia = KerberosIA.KerberosIA()
    ia.conexiones = conexiones
    return ia


def colocar(ia, casilla):
    ia.casilla = casilla
    ia.definirPosicion(*centro(casilla))


def casilla_con(conexiones, n):
    return next(c for c, d in sorted(conexiones.items()) if len(d) == n)


# ---------- posicion ----------
def test_posicion():
    p = KerberosIA.posicion()
    assert (p.x, p.y) == (0, 0)
    p.cargar(7, 8)
    assert (p.x, p.y) == (7, 8)


# ---------- Estado ----------
def test_valores_iniciales():
    ia = KerberosIA.KerberosIA(10, 20)
    assert ia.estado == 0 and ia.alarma is False and ia.playerDetectado is False
    assert ia.casillasLibres == [False] * 4
    assert ia.path == [] and ia.KasRecorridas == set()
    assert (ia.posicion.x, ia.posicion.y) == (10, 20)


def test_definirPosicion():
    ia = KerberosIA.KerberosIA()
    ia.definirPosicion(3, 4)
    assert (ia.posicion.x, ia.posicion.y) == (3, 4)


def test_detectarPlayer_no_falla():
    KerberosIA.KerberosIA().detectarPlayer()


def test_cambiarEstado():
    ia = KerberosIA.KerberosIA()
    ia.cambiarEstado(3)
    assert ia.estado == 3


@pytest.mark.parametrize("estado, detectado, ordenJefe, nuevo, alarma", [
    (0, True, False, 1, False),
    (0, False, False, 0, False),
    (1, True, False, 2, False),
    (2, False, False, 1, True),
    (0, False, True, 3, False),
])
def test_cambioEstado(estado, detectado, ordenJefe, nuevo, alarma):
    ia = KerberosIA.KerberosIA()
    ia.estado, ia.playerDetectado, ia.ordenJefe = estado, detectado, ordenJefe
    ia.cambioEstado()
    assert ia.estado == nuevo
    assert ia.alarma is alarma


def test_gritarAlarma():
    ia = KerberosIA.KerberosIA()
    ia.gritarAlarma()
    assert ia.alarma is True


@pytest.mark.parametrize("antes, despues", [(0, 2), (2, 0), (1, 3), (3, 1)])
def test_cambiarSentido(antes, despues):
    ia = KerberosIA.KerberosIA()
    ia.orientacion = antes
    ia.cambiarSentido()
    assert ia.orientacion == despues


def test_reiniciar_arrays():
    ia = KerberosIA.KerberosIA()
    ia.casillasLibres[1] = True
    ia.casillasLibresVuelta[2] = True
    ia.reiniciarArraySiguientesCasillas()
    ia.reiniciarArraySiguientesCasillasVuelta()
    assert ia.casillasLibres == [False] * 4
    assert ia.casillasLibresVuelta == [False] * 4


# ---------- Geometría ----------
def test_esInterseccion(kia, conexiones):
    kia.casilla = casilla_con(conexiones, 3)
    assert kia.esInterseccion() is True
    kia.casilla = casilla_con(conexiones, 2)
    assert kia.esInterseccion() is False
    kia.casilla = 0  # pared: sin conexiones
    assert kia.esInterseccion() is False


@pytest.mark.parametrize("direccion", [0, 1, 2, 3])
def test_calcularDireccion(direccion):
    ia = KerberosIA.KerberosIA()
    assert ia.calcularDireccion(500, 500 + PASO[direccion]) == direccion


def test_calcularDireccion_no_adyacente_devuelve_orientacion():
    ia = KerberosIA.KerberosIA()
    ia.orientacion = 3
    assert ia.calcularDireccion(500, 600) == 3


@pytest.mark.parametrize("direccion", [0, 1, 2, 3])
def test_obtenerCasillaSiguiente_y_mover(direccion):
    ia = KerberosIA.KerberosIA()
    assert ia.obtenerCasillaSiguiente(500, direccion) == 500 + PASO[direccion]
    assert ia.mover(500, direccion) == 500 + PASO[direccion]


def test_obtenerCasillaSiguiente_direccion_invalida():
    ia = KerberosIA.KerberosIA()
    assert ia.obtenerCasillaSiguiente(500, 9) == 500
    assert ia.mover(500, 9) is None


def test_casillas_recorridas():
    ia = KerberosIA.KerberosIA()
    assert ia._casillas_recorridas() == set()
    ia.KasRecorridas = [(41, 1.0), (42, 2.0), 43]
    assert ia._casillas_recorridas() == {41, 42, 43}


# ---------- Elección de dirección ----------
def test_elegirDireccionEvitar_sin_opciones(kia):
    kia.casilla = 0
    kia.orientacion = 2
    assert kia.elegirDireccionEvitar() == 2


def test_elegirDireccionEvitar_callejon_da_media_vuelta(kia, conexiones):
    c = casilla_con(conexiones, 1)
    kia.casilla = c
    unica = conexiones[c][0]
    kia.orientacion = (unica + 2) % 4
    assert kia.elegirDireccionEvitar() == unica


def test_elegirDireccionEvitar_no_da_media_vuelta(kia, conexiones):
    c = casilla_con(conexiones, 2)
    kia.casilla = c
    d1, d2 = conexiones[c]
    kia.orientacion = (d1 + 2) % 4  # venimos de d1
    assert kia.elegirDireccionEvitar() == d2


def test_elegirDireccionEvitar_prefiere_no_recorridas(kia, conexiones):
    c = casilla_con(conexiones, 3)
    kia.casilla = c
    opciones = conexiones[c]
    falta = ({0, 1, 2, 3} - set(opciones)).pop()
    kia.orientacion = (falta + 2) % 4  # su opuesta no es una opción: no se descarta nada
    libre = opciones[-1]
    kia.KasRecorridas = [(c + PASO[d], 0) for d in opciones if d != libre]
    assert kia.elegirDireccionEvitar() == libre


def test_elegirDireccionEvitar_descarta_bloqueada(kia, conexiones):
    c = casilla_con(conexiones, 2)
    kia.casilla = c
    d1, d2 = conexiones[c]
    kia.orientacion = 9
    assert kia.elegirDireccionEvitar(direccionBloqueada=d1) == d2
    assert kia.elegirDireccionEvitar(direccionBloqueada=d2) == d1


def test_elegirDireccion_aleatoria_valida(kia, conexiones):
    c = casilla_con(conexiones, 3)
    kia.casilla = c
    kia.orientacion = conexiones[c][0]
    opuesta = (kia.orientacion + 2) % 4
    for _ in range(30):
        d = kia.elegirDireccion()
        assert d in conexiones[c] and d != opuesta


def test_elegirDireccion_callejon_y_sin_opciones(kia, conexiones):
    c = casilla_con(conexiones, 1)
    kia.casilla = c
    unica = conexiones[c][0]
    kia.orientacion = (unica + 2) % 4
    assert kia.elegirDireccion() == unica
    kia.casilla = 0
    assert kia.elegirDireccion() == kia.orientacion


# ---------- BFS ----------
def test_bfs_misma_casilla(kia):
    assert kia.calcular_camino_BFS(41, 41) == [41]


def test_bfs_camino_valido_y_minimo(kia, conexiones):
    camino = kia.calcular_camino_BFS(41, 46)
    assert camino[0] == 41 and camino[-1] == 46
    assert len(camino) == 6  # fila 1 recta: 41..46
    for a, b in zip(camino, camino[1:]):
        assert kia.calcularDireccion(a, b) in conexiones[a]


def test_bfs_camino_largo_es_conexo(kia, conexiones):
    camino = kia.calcular_camino_BFS(41, 977)
    assert camino and camino[0] == 41 and camino[-1] == 977
    for a, b in zip(camino, camino[1:]):
        assert any(a + PASO[d] == b for d in conexiones[a])
    assert len(set(camino)) == len(camino)


def test_bfs_sin_camino(kia):
    assert kia.calcular_camino_BFS(41, 0) == []  # 0 es pared


# ---------- seguirCamino ----------
def test_seguirCamino_vacio_no_cambia(kia):
    kia.orientacion = 2
    kia.seguirCamino()
    assert kia.orientacion == 2


def test_seguirCamino_orienta_hacia_siguiente(kia):
    kia.casilla = 41
    kia.path = [41, 42, 43]
    kia.seguirCamino()
    assert kia.path == [42, 43]
    assert kia.orientacion == 1


def test_seguirCamino_destino_alcanzado(kia):
    kia.casilla = 43
    kia.orientacion = 0
    kia.path = [43]
    kia.seguirCamino()
    assert kia.path == []
    assert kia.orientacion == 0


# ---------- update ----------
def test_update_calcula_casilla_desde_posicion(kia):
    colocar(kia, 41)
    kia.casilla = -1
    kia.update()
    assert kia.casilla == 41


def test_update_colision_paredes(kia, conexiones):
    c = casilla_con(conexiones, 2)
    colocar(kia, c)
    d1, d2 = conexiones[c]
    kia.orientacion = d1
    kia.path = [1, 2, 3]
    kia.colisionParedes = True
    d = kia.update()
    assert kia.colisionParedes is False
    assert kia.path == []
    assert d == kia.orientacion == d2


def test_update_jugador_detectado_sigue_bfs(kia):
    colocar(kia, 41)
    kia.playerDetectado = True
    kia.casillaJugador = 46
    d = kia.update()
    assert d == 1
    assert kia.path == [42, 43, 44, 45, 46]


def test_update_recalcula_si_jugador_se_mueve(kia):
    colocar(kia, 41)
    kia.playerDetectado = True
    kia.casillaJugador = 46
    kia.update()
    kia.casillaJugador = 44
    kia.update()
    assert kia.path[-1] == 44


def test_update_patrulla_callejon(kia, conexiones):
    c = casilla_con(conexiones, 1)
    colocar(kia, c)
    kia.orientacion = (conexiones[c][0] + 2) % 4
    assert kia.update() == conexiones[c][0]
    assert kia.ultimaCasilla == c


def test_update_patrulla_pasillo_e_interseccion(kia, conexiones):
    for n in (2, 3):
        c = casilla_con(conexiones, n)
        colocar(kia, c)
        kia.ultimaCasilla = -1
        kia.orientacion = (conexiones[c][0] + 2) % 4
        d = kia.update()
        assert d in conexiones[c]


def test_update_misma_casilla_no_cambia(kia, conexiones):
    c = casilla_con(conexiones, 3)
    colocar(kia, c)
    kia.ultimaCasilla = c
    kia.orientacion = 7
    assert kia.update() == 7


def test_update_log_debug_imprime(kia, conexiones, capsys):
    kia.log_debug = True
    for n, texto in ((1, "Callejón"), (2, "Pasillo"), (3, "Intersección")):
        colocar(kia, casilla_con(conexiones, n))
        kia.ultimaCasilla = -1
        kia.update()
        assert texto in capsys.readouterr().out
