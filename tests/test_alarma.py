# Luz de alarma (Code/Luces.py: LuzAlarma), su carga desde los niveles JSON ("Alarm") y el
# enemigo que corre a encenderla tras ver al jugador (Laberinto + KerberosIA.rumbo).
import pygame
import pytest

import Luces
import MazeLab
from Luces import DURACION_LUZ_ALARMA_MS, LuzAlarma
from test_laberinto import app  # noqa: F401 (fixture)
from test_niveles import nivel, nivel_real, F, W

CASILLA_ALARMA_LEVEL_0 = 573   # (12, 14) del JSON + el marco de 1 casilla


def parecido(color, esperado, tolerancia=3):
    # La lámpara se escala (suavizado): los colores pueden variar en un par de niveles.
    return all(abs(a - b) <= tolerancia for a, b in zip(color[:3], esperado[:3]))


@pytest.fixture
def alarma():
    return LuzAlarma(100, (64, 200, 32, 32))


# ---------- LuzAlarma ----------
def test_alarma_apagada_por_defecto(alarma):
    assert alarma.encendida(0) is False
    assert alarma.haces(0, []) == []
    assert alarma.angulo(0) == 0.0


def test_alarma_dura_30_segundos(alarma):
    alarma.encender(1000)
    assert alarma.encendida(1000)
    assert alarma.encendida(1000 + DURACION_LUZ_ALARMA_MS - 1)
    assert not alarma.encendida(1000 + DURACION_LUZ_ALARMA_MS)
    assert alarma.encendida_ms is None        # se apaga sola


def test_volver_a_encender_reinicia_los_30_segundos(alarma):
    alarma.encender(0)
    alarma.encender(20000)
    assert alarma.encendida(20000 + DURACION_LUZ_ALARMA_MS - 1)


def test_haces_giran_360_grados(alarma):
    alarma.encender(0)
    assert alarma.angulo(0) == 0
    assert alarma.angulo(Luces.VUELTA_ALARMA_MS // 4) == pytest.approx(90)
    assert alarma.angulo(Luces.VUELTA_ALARMA_MS) == pytest.approx(0)


def test_dos_haces_opuestos_y_mas_largos_que_la_vision(alarma):
    alarma.encender(0)
    primero, segundo = alarma.haces(0, [])
    centro = pygame.math.Vector2(alarma.rect.center)
    medio = lambda poligono: pygame.math.Vector2(poligono[len(poligono) // 2 + 1]) - centro
    assert primero[0] == segundo[0] == alarma.rect.center
    assert medio(primero).angle_to(medio(segundo)) == pytest.approx(180, abs=1) or \
        medio(primero).angle_to(medio(segundo)) == pytest.approx(-180, abs=1)
    assert medio(primero).length() == pytest.approx(Luces.ALCANCE_HAZ_ALARMA, abs=1)
    assert Luces.ALCANCE_HAZ_ALARMA > 5 * MazeLab.CASILLA_PIXEL   # visión: 4 (5 el jefe)


def test_haces_pasan_por_encima_de_las_paredes(alarma):
    alarma.encender(0)
    pared = pygame.Rect(alarma.rect.right + 10, alarma.rect.top - 50, 32, 132)
    largo = lambda: (pygame.math.Vector2(alarma.haces(0, [pared])[0][len(alarma.haces(0, [pared])[0]) // 2])
                     - alarma.rect.center).length()
    assert largo() == pytest.approx(Luces.ALCANCE_HAZ_ALARMA, abs=1)


def test_haces_cortados_por_paredes_si_se_desactiva(monkeypatch, alarma):
    monkeypatch.setattr(Luces, "HACES_ALARMA_ATRAVIESAN_PAREDES", False)
    alarma.encender(0)
    pared = pygame.Rect(alarma.rect.right + 10, alarma.rect.top - 50, 32, 132)
    poligono = alarma.haces(0, [pared])[0]
    fin = pygame.math.Vector2(poligono[len(poligono) // 2])
    assert (fin - alarma.rect.center).length() < Luces.ALCANCE_HAZ_ALARMA / 2


def test_imagen_apagada_y_encendida_distintas():
    apagada, encendida = LuzAlarma.imagen(False), LuzAlarma.imagen(True)
    assert apagada.get_size() == encendida.get_size() == (32, 32)
    # Reducida al 85 % y centrada: los bordes de la casilla quedan transparentes.
    ocupado = apagada.get_bounding_rect()
    assert ocupado.width <= round(32 * Luces.ESCALA_LAMPARA_ALARMA)
    assert abs(ocupado.centerx - 16) <= 1
    assert apagada.get_at((15, 12)) != encendida.get_at((15, 12))   # cúpula roja oscura / viva
    assert parecido(apagada.get_at((15, 25)), (205, 205, 200))      # base gris


def test_dibujar_y_haces_translucidos(alarma):
    superficie = pygame.Surface((864, 1000))
    superficie.fill((60, 60, 60))
    alarma.dibujar(superficie, 0)
    assert parecido(superficie.get_at((alarma.rect.x + 15, alarma.rect.y + 12)), LuzAlarma.imagen(False).get_at((15, 12)))
    alarma.encender(0)
    alarma.dibujarHaces(superficie, 0, [])
    lejos = (alarma.rect.centerx + Luces.ALCANCE_HAZ_ALARMA - 20, alarma.rect.centery)
    r, g, b, _ = superficie.get_at(lejos)
    assert 60 < r < 255 and g < 60 and b < 60          # rojo translúcido sobre el gris


# ---------- Carga desde los niveles ----------
def test_level_0_tiene_la_alarma():
    maze = MazeLab.Maze(nivel_real(0))
    assert maze.mazeDataExtra[CASILLA_ALARMA_LEVEL_0] == MazeLab.CODIGO_ALARMA


def test_alarma_sobre_pared_se_ignora():
    # El objeto está en (0, 0), que es pared.
    alarma = 6   # id de "Alarm" (empiezan en 1)
    datos = nivel([[W, W, W], [W, F, W], [W, W, W]], [[alarma, 0, 0], [0, 0, 0], [0, 0, 0]],
                  nombres=["Floor", "Wall", "Bone", "DogDown1", "Exit", "Alarm"])
    maze = MazeLab.Maze(datos)
    assert MazeLab.CODIGO_ALARMA not in maze.mazeDataExtra


def test_draw_crea_las_alarmas_y_conserva_su_estado():
    maze = MazeLab.Maze(nivel_real(0))
    superficie = pygame.Surface((MazeLab.ANCHO_MUNDO, 1000))
    suelo = pygame.Surface((32, 32))
    maze.draw(superficie, suelo, suelo)
    assert [a.casilla for a in maze.MazeAlarmas] == [CASILLA_ALARMA_LEVEL_0]
    alarma = maze.MazeAlarmas[0]
    assert alarma.rect.topleft == (13 * 32, 14 * 32 + MazeLab.BIAS)
    alarma.encender(500)
    maze.draw(superficie, suelo, suelo)
    assert maze.MazeAlarmas[0] is alarma and alarma.encendida_ms == 500


def test_nivel_por_defecto_sin_alarmas():
    maze = MazeLab.Maze()
    maze.draw(pygame.Surface((MazeLab.ANCHO_MUNDO, 1000)), pygame.Surface((32, 32)), pygame.Surface((32, 32)))
    assert maze.MazeAlarmas == []


# ---------- En el juego ----------
@pytest.fixture
def juego(app):
    app.on_init()
    app.prepararNivel(nivel_real(0))
    app.rebuild_map = True
    app.on_loop()
    app.on_render()
    app.player.vida = 10 ** 9
    app.player.x, app.player.y = 2000, 2000      # fuera: que nadie lo vea durante la prueba
    return app


def enemigo_normal(juego):
    return next(e for e in juego.EnemigosGroup if not e.isJefeEnemigo)


def test_enemigo_que_ve_al_jugador_va_a_la_alarma(juego):
    e = enemigo_normal(juego)
    juego.darAlarma(e)
    alarma = juego.maze.MazeAlarmas[0]
    assert e.alarmaDestino is alarma and e.kia.rumbo == alarma.casilla


def test_enemigo_enciende_la_alarma_y_vuelve_a_su_zona(juego):
    e = enemigo_normal(juego)
    origen = MazeLab.Maze.calcularCasilla(*e.rect.center)
    alarma = juego.maze.MazeAlarmas[0]
    juego.darAlarma(e)
    for _ in range(3000):
        juego.on_loop()
        if alarma.encendida_ms is not None:
            break
    assert alarma.encendida_ms is not None
    assert MazeLab.Maze.calcularCasilla(*e.rect.center) == alarma.casilla
    assert e.alarmaDestino is None and e.kia.rumbo == origen
    for _ in range(3000):
        juego.on_loop()
        if e.kia.rumbo is None:
            break
    assert e.kia.rumbo is None and MazeLab.Maze.calcularCasilla(*e.rect.center) == origen


def test_solo_va_un_enemigo_por_alarma(juego):
    primero, segundo = [e for e in juego.EnemigosGroup if not e.isJefeEnemigo][:2]
    assert juego.mandarAEncenderAlarma(primero) is not None
    assert juego.mandarAEncenderAlarma(segundo) is None
    assert segundo.kia.rumbo is None


def test_nadie_va_si_la_alarma_ya_esta_encendida(juego):
    juego.maze.MazeAlarmas[0].encender(pygame.time.get_ticks())
    assert juego.mandarAEncenderAlarma(enemigo_normal(juego)) is None


def test_el_jefe_no_va_a_la_alarma(juego):
    assert juego.mandarAEncenderAlarma(juego.JefeEnemigo) is None


def test_sin_alarmas_en_el_nivel_no_cambia_nada(app):
    app.on_init()
    app.on_loop()
    e = next(e for e in app.EnemigosGroup if not e.isJefeEnemigo)
    app.darAlarma(e)
    assert e.alarmaDestino is None and e.kia.rumbo is None


def test_no_va_si_una_puerta_cerrada_corta_el_camino(juego):
    e = enemigo_normal(juego)
    e.kia.casillasBloqueadas = set(juego.conexiones)      # todo bloqueado: no hay camino
    assert juego.mandarAEncenderAlarma(e) is None


def test_render_pinta_la_lampara_y_los_haces(juego):
    alarma = juego.maze.MazeAlarmas[0]
    juego.visionEnemigos = False
    juego.on_render()
    antes = juego.mundo.get_at((alarma.rect.centerx + 100, alarma.rect.centery))
    alarma.encender(pygame.time.get_ticks())
    juego.on_render()
    assert parecido(juego.mundo.get_at((alarma.rect.x + 15, alarma.rect.y + 12)), LuzAlarma.imagen(True).get_at((15, 12)))
    despues = juego.mundo.get_at((alarma.rect.centerx + 100, alarma.rect.centery))
    assert despues.r > antes.r and despues.g < antes.g     # el haz (ángulo 0) tiñe de rojo a la derecha
