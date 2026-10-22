import time

import pygame
import pytest

import KerberosIA
import player
from player import BIAS, SCREEN_HEIGHT, SCREEN_WIDTH
from MazeLab import NUM_CASILLAS_H as H
from conftest import centro


@pytest.fixture
def jugador():
    return player.Player()


@pytest.fixture
def enemigo():
    e = player.Enemigo()
    e.x, e.y = 200, 300
    return e


@pytest.fixture
def jefe(conexiones):
    j = player.Enemigo()
    j.isJefeEnemigo = True
    j.conexiones = conexiones
    j.pasarConexionesIA()
    return j


# ---------- Funciones del módulo ----------
def test_load_image_ok():
    img = player.load_image("player.png", "./Resources", alpha=True)
    assert isinstance(img, pygame.Surface)
    img2 = player.load_image("player.png", "./Resources")
    assert img2.get_size() == img.get_size()


def test_load_image_inexistente_sale():
    with pytest.raises(SystemExit):
        player.load_image("no_existe.png", "./Resources")


@pytest.mark.parametrize("otro, lado", [
    (pygame.Rect(18, 0, 20, 20), "izquierda"),
    (pygame.Rect(-18, 0, 20, 20), "derecha"),
    (pygame.Rect(0, 18, 20, 20), "arriba"),
    (pygame.Rect(0, -18, 20, 20), "abajo"),
])
def test_detectar_colision_lados(otro, lado):
    assert player.detectar_colision(pygame.Rect(0, 0, 20, 20), otro) == lado


def test_detectar_colision_sin_contacto():
    assert player.detectar_colision(pygame.Rect(0, 0, 10, 10), pygame.Rect(50, 50, 10, 10)) is None


# ---------- Disparos ----------
def test_disparo_jugador_y_enemigo():
    bala = player.Disparos(100, 300, True, 0)
    assert bala.image.get_size() == (10, 20)
    assert (bala.rect.x, bala.rect.y, bala.x, bala.y) == (100, 300, 100, 300)
    bala_e = player.Disparos(100, 300, False, 2)
    assert bala_e.image.get_size() == (8, 18)


@pytest.mark.parametrize("orient", [1, 3])
def test_disparo_horizontal_rota_imagen(orient):
    assert player.Disparos(100, 300, True, orient).image.get_size() == (20, 10)


@pytest.mark.parametrize("orient, dx, dy", [(0, 0, -3), (1, 3, 0), (2, 0, 3), (3, -3, 0)])
def test_disparo_update_mueve(orient, dx, dy):
    bala = player.Disparos(400, 500, True, orient)
    bala.update()
    assert (bala.rect.x, bala.rect.y) == (400 + dx, 500 + dy)


@pytest.mark.parametrize("x, y, orient", [
    (1, 500, 3),                    # sale por la izquierda
    (SCREEN_WIDTH, 500, 1),         # sale por la derecha
    (400, BIAS, 0),                 # entra en la cabecera
    (400, SCREEN_HEIGHT, 2),        # sale por abajo
])
def test_disparo_update_elimina_fuera_de_pantalla(x, y, orient):
    grupo = pygame.sprite.Group()
    bala = player.Disparos(x, y, True, orient)
    grupo.add(bala)
    bala.update()
    assert not grupo.has(bala)


def test_disparo_municion():
    bala = player.Disparos(0, 200, True, 0)
    bala.definirMunicion(5)
    bala.actualizarMunicion(2, 0)
    assert bala.municion == 3
    bala.actualizarMunicion(4, 1)
    assert bala.municion == 7
    bala.actualizarMunicion(4, 9)  # sentido desconocido: no cambia
    assert bala.municion == 7


def test_disparo_rotarBala():
    assert player.Disparos(0, 200, True, 0).rotarBala(90).get_size() == (20, 10)


# ---------- Player ----------
def test_player_init(jugador):
    assert jugador.image.get_size() == (22, 22)
    assert jugador.rect.size == (22, 22)
    assert jugador.mask is not None
    assert jugador.flagDisparo is False


def test_player_inicio(jugador):
    for _ in range(20):
        jugador.inicio(800, 900)
        assert 0 <= jugador.x <= 800 and BIAS <= jugador.y <= 900
        assert (jugador.prev_x, jugador.prev_y) == (jugador.x, jugador.y)


def test_player_stop(jugador):
    jugador.stop()
    assert (jugador.speedH, jugador.speedV) == (0, 0)


def test_player_andar_acelera_y_reinicia(jugador):
    jugador.speedH = jugador.speedV = 5
    jugador.andar()
    assert (jugador.speedH, jugador.speedV) == (6, 6)
    jugador.andar()
    assert (jugador.speedH, jugador.speedV) == (2, 2)


@pytest.mark.parametrize("metodo, dx, dy, orient", [
    ("moveRight", 3, 0, 1), ("moveLeft", -3, 0, 3),
    ("moveUp", 0, -3, 0), ("moveDown", 0, 3, 2),
])
def test_player_movimientos(jugador, metodo, dx, dy, orient):
    jugador.x, jugador.y = 100, 300
    jugador.speedH = jugador.speedV = 2
    getattr(jugador, metodo)()
    assert (jugador.x, jugador.y) == (100 + dx, 300 + dy)
    assert (jugador.prev_x, jugador.prev_y) == (100, 300)
    assert jugador.orientacion == orient


def test_player_vida(jugador):
    jugador.asignarVida(50)
    jugador.cambiarVida(-20)
    assert jugador.vida == 30


def test_player_getPosicion(jugador):
    jugador.casilla = 77
    assert jugador.getPosicion() == 77


def test_player_log_y_pintar(jugador):
    jugador.logMovimiento("Derecha", 1, 2)
    jugador.pintarJugador()


def test_player_update_sincroniza_rect(jugador):
    jugador.x, jugador.y = 123, 456
    jugador.update()
    assert (jugador.rect.x, jugador.rect.y) == (123, 456)


def test_player_disparo(jugador):
    jugador.municion = 2
    jugador.orientacion = 1
    jugador.disparo()
    assert jugador.municion == 1
    assert jugador.flagDisparo is True
    assert len(jugador.balas) == 1
    assert jugador.bala.orientacion == 1


def test_player_disparo_sin_municion(jugador):
    jugador.municion = 0
    jugador.disparo()
    assert len(jugador.balas) == 0
    assert jugador.flagDisparo is False


def test_player_dibujaDanoPlayer(jugador):
    roja = jugador.dibujaDañoPlayer()
    assert roja.get_size() == jugador.image.get_size()
    assert roja is not jugador.image
    # Ningún píxel conserva más verde/azul que el original.
    for x in range(0, 22, 5):
        for y in range(0, 22, 5):
            o, r = jugador.image.get_at((x, y)), roja.get_at((x, y))
            assert r.g <= o.g and r.b <= o.b


def test_player_rotar(jugador):
    assert jugador.rotar(90).get_size() == (22, 22)


def test_player_escalaGrises(jugador):
    gris = jugador.escalaGrises()
    assert gris.get_size() == (22, 22)
    for x in range(0, 22, 5):
        c = gris.get_at((x, 11))
        assert c.r == c.g == c.b


# ---------- Enemigo ----------
def test_enemigo_init(enemigo):
    assert enemigo.vida == 100 and enemigo.municion == 100
    assert enemigo.orientacion == 2
    assert enemigo.isJefeEnemigo is False
    assert isinstance(enemigo.kia, KerberosIA.KerberosIA)
    assert enemigo.imageEnemigo.get_size() == (22, 22)
    assert enemigo.imageJefeEnemigo.get_size() == (22, 22)
    assert enemigo.visionImage.get_size() == (40, 60)


def test_enemigo_lista_recorridos_propia_y_compartida_con_ia():
    a, b = player.Enemigo(), player.Enemigo()
    assert a.posicionesRecorridas is not b.posicionesRecorridas
    assert a.kia.KasRecorridas is a.posicionesRecorridas


def test_enemigo_inicio(enemigo):
    enemigo.inicio(800, 900)
    assert 0 <= enemigo.x <= 800 and BIAS <= enemigo.y <= 900
    assert (enemigo.prev_x, enemigo.prev_y) == (enemigo.x, enemigo.y)


def test_enemigo_definirJefeEnemigo(enemigo):
    enemigo.definirJefeEnemigo()
    assert enemigo.isJefeEnemigo is True


def test_enemigo_pasarConexionesIA(enemigo, conexiones):
    enemigo.conexiones = conexiones
    enemigo.pasarConexionesIA()
    assert enemigo.kia.conexiones is conexiones


def test_enemigo_inicioCelda_y_getPosicion(enemigo):
    enemigo.inicioCelda(55)
    assert enemigo.getPosicion() == 55


@pytest.mark.parametrize("metodo, dx, dy, orient", [
    ("moveRight", 1, 0, 1), ("moveLeft", -1, 0, 3),
    ("moveUp", 0, -1, 0), ("moveDown", 0, 1, 2),
])
def test_enemigo_movimientos(enemigo, metodo, dx, dy, orient):
    getattr(enemigo, metodo)()
    assert (enemigo.x, enemigo.y) == (200 + dx, 300 + dy)
    assert (enemigo.prev_x, enemigo.prev_y) == (200, 300)
    assert enemigo.orientacion == orient


def test_enemigo_moveStop(enemigo):
    enemigo.moveStop()
    assert (enemigo.x, enemigo.y, enemigo.prev_x, enemigo.prev_y) == (200, 300, 200, 300)


def test_enemigo_log(enemigo):
    enemigo.logPosicionEnemigo()
    enemigo.logMovimiento("Abajo", 1, 2)
    assert enemigo.vision((0, 0)) is None


def test_enemigo_visionRotar(enemigo):
    enemigo.angle = 359
    enemigo.visionRotar()
    assert enemigo.angle == pytest.approx(0.5)


def test_enemigo_update_normal_baja(enemigo):
    enemigo.update()
    assert enemigo.y == 301
    assert (enemigo.rect.x, enemigo.rect.y) == (200, 301)
    assert enemigo.prev_y == 300


def test_jefe_update_en_centro_usa_ia(jefe):
    # Centro de la casilla 41; la IA patrulla y elige una dirección válida.
    cx, cy = centro(41)
    jefe.x, jefe.y = cx - jefe.rect.width // 2, cy - jefe.rect.height // 2
    jefe.update()
    assert jefe.kia.casilla == 41
    assert jefe.kia.ultimaCasilla == 41
    assert jefe.orientacion in jefe.conexiones[41]
    assert (jefe.x, jefe.y) != (cx - 11, cy - 11)


def test_jefe_update_fuera_de_centro_sigue_recto(jefe):
    cx, cy = centro(42)
    jefe.x, jefe.y = cx - 11 + 3, cy - 11
    jefe.orientacion = 1
    jefe.update()
    assert (jefe.x, jefe.y) == (cx - 11 + 4, cy - 11)
    assert jefe.kia.ultimaCasilla == -1


def test_jefe_sigue_camino_bfs(jefe):
    cx, cy = centro(41)
    jefe.x, jefe.y = cx - 11, cy - 11
    jefe.kia.playerDetectado = True
    jefe.kia.casillaJugador = 41 + 3
    jefe.update()
    assert jefe.orientacion == 1
    assert jefe.x == cx - 11 + 1


@pytest.mark.parametrize("d, dx, dy", [(0, 0, -1), (1, 1, 0), (2, 0, 1), (3, -1, 0), (7, 0, 1)])
def test_enemigo_elegirDireccion(enemigo, d, dx, dy):
    enemigo.elegirDireccion(d)
    assert (enemigo.x, enemigo.y) == (200 + dx, 300 + dy)


def test_enemigo_revertir_movimiento(enemigo):
    enemigo.moveRight()
    enemigo.revertir_movimiento()
    assert (enemigo.x, enemigo.y) == (200, 300)


@pytest.mark.parametrize("antes, despues", [(0, 2), (2, 0), (1, 3), (3, 1)])
def test_enemigo_cambiar_direccion(enemigo, antes, despues):
    enemigo.orientacion = antes
    enemigo.speedV = 1
    enemigo.cambiar_direccion()
    assert enemigo.orientacion == despues
    assert enemigo.kia.orientacion == despues
    assert enemigo.speedV == -1


def test_jefe_cambiar_direccion_avisa_a_la_ia(jefe):
    jefe.orientacion = 1
    jefe.cambiar_direccion()
    assert jefe.kia.colisionParedes is True
    assert jefe.orientacion == 1


def test_enemigo_detectarColision_no_hace_nada(enemigo):
    assert enemigo.detectarColision() is None


def test_enemigo_rotar(enemigo):
    assert enemigo.rotar(90).get_size() == (22, 22)


def test_enemigo_imagenActual(enemigo):
    assert enemigo.imagenActual() is enemigo.imageEnemigo
    enemigo.definirJefeEnemigo()
    assert enemigo.imagenActual() is enemigo.imageJefeEnemigo


def test_enemigo_escalaGrises(enemigo):
    gris = enemigo.escalaGrises()
    assert gris.get_size() == (22, 22)
    c = gris.get_at((11, 11))
    assert c.r == c.g == c.b


def test_cargarCasillaRecorrido_sin_duplicados(enemigo):
    enemigo.cargarCasillaRecorrido(41)
    enemigo.cargarCasillaRecorrido(41)
    enemigo.cargarCasillaRecorrido(42)
    assert [c for c, _ in enemigo.posicionesRecorridas] == [41, 42]


def test_borrarRecorridosAntiguos(enemigo):
    lista = enemigo.posicionesRecorridas
    lista.append((10, time.time() - 60))
    lista.append((11, time.time()))
    enemigo.borrarRecorridosAntiguos()
    assert [c for c, _ in enemigo.posicionesRecorridas] == [11]
    # Se modifica en sitio: la IA sigue viendo la misma lista.
    assert enemigo.posicionesRecorridas is lista is enemigo.kia.KasRecorridas


def test_bocadilloTexto_dibuja(enemigo, superficie):
    superficie.fill((0, 0, 0))
    enemigo.bocadilloTexto(superficie, "Hola", 300, 400, 255)
    # El bocadillo (blanco) queda por encima del punto indicado.
    assert superficie.get_at((300, 400 - 15))[:3] == (255, 255, 255)
    assert player.Enemigo.fontBocadillo is not None


def test_bocadilloTexto_reutiliza_fuente(enemigo, superficie):
    enemigo.bocadilloTexto(superficie, "a", 100, 300, 255)
    fuente = player.Enemigo.fontBocadillo
    enemigo.bocadilloTexto(superficie, "b", 100, 300, 128)
    assert player.Enemigo.fontBocadillo is fuente


def test_restarRelojBocadilloTexto(enemigo):
    enemigo.bubble_start_time = -1
    enemigo.restarRelojBocadilloTexto()
    assert enemigo.bubble_start_time >= 0


def test_enemigo_disparo(enemigo):
    enemigo.update()
    enemigo.municion = 1
    enemigo.disparo()
    assert enemigo.municion == 0 and enemigo.flagDisparo is True
    assert enemigo.bala in enemigo.balas
    assert enemigo.bala.isPlayer is False
    enemigo.disparo()  # sin munición
    assert len(enemigo.balas) == 1


@pytest.mark.parametrize("es_jefe", [False, True])
def test_enemigo_dibujaDano(enemigo, es_jefe):
    roja = enemigo.dibujaDaño(es_jefe)
    original = enemigo.imageJefeEnemigo if es_jefe else enemigo.imageEnemigo
    assert roja.get_size() == original.get_size()
    assert roja is not original
