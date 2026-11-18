# Pantalla de Nuevo Juego (Laberinto.pantallaNuevaPartida): Empezar, Dificultad y Nivel.
import pygame
import pytest

import Laberinto
from Laberinto import App, DIFICULTADES
from test_laberinto import Salida, app, lanzar  # noqa: F401 (app es un fixture)
from test_niveles import raton, tandas

# Botones (300x40 centrados en x=432): Empezar y 440-480, Dificultad 490-530, Nivel 540-580, Volver 690-730.
EMPEZAR, DIFICULTAD, NIVEL, VOLVER = (432, 460), (432, 510), (432, 560), (432, 710)
NIVELES = ["Level_0.json", "Level_1.json", "Level_2.json", "Level_3.json", "Level_4.json", "Level_5.json"]


def pulsar(monkeypatch, app, *clics):
    # Cada clic llega en su propia tanda de eventos; al acabarlos, la pantalla se corta con Salida.
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (10, 10))
    tandas(monkeypatch, *[[c if isinstance(c, pygame.event.EventType) else raton(c)] for c in clics])
    with pytest.raises(Salida) as salida:
        app.pantallaNuevaPartida()
    return str(salida.value)


# ---- Botones de la pantalla ----

def test_orden_de_los_botones_empezar_justo_encima_de_dificultad():
    acciones = [accion for _, accion in App.BOTONES_NUEVA_PARTIDA]
    assert acciones[:3] == ["empezar", "dificultad", "nivel"]
    dy = dict((accion, y) for y, accion in App.BOTONES_NUEVA_PARTIDA)
    assert dy["dificultad"] - dy["empezar"] == 50          # 40 de botón + 10 de separación


def test_nuevo_juego_abre_la_pantalla_nueva(monkeypatch, app):
    lanzar(monkeypatch, app, "pantallaNuevaPartida")
    lanzar(monkeypatch, app, "on_execute")
    tandas(monkeypatch, [raton((500, 450))])
    with pytest.raises(Salida, match="pantallaNuevaPartida"):
        app.menu()


def test_niveles_disponibles_son_los_json(app):
    assert app.nivelesDisponibles() == NIVELES


def test_por_defecto_medio_y_el_nivel_inicial(monkeypatch, app):
    monkeypatch.setattr(Laberinto, "NIVEL_INICIAL", "Level_0.json")
    pulsar(monkeypatch, app)
    assert app.dificultad == "Medio" and app.nivelElegido == "Level_0.json"
    assert app.textoBotonNuevaPartida("dificultad") == "Dificultad: Medio"
    assert app.textoBotonNuevaPartida("nivel") == "Nivel: Level_0"


def test_sin_nivel_inicial_elige_el_primero(monkeypatch, app):
    pulsar(monkeypatch, app)                                # en los tests NIVEL_INICIAL es None
    assert app.nivelElegido == "Level_0.json"


def test_clic_en_dificultad_va_rotando(monkeypatch, app):
    vistas = []
    monkeypatch.setattr(app, "definirDificultad",
                        lambda d, original=app.definirDificultad: vistas.append(d) or original(d))
    pulsar(monkeypatch, app, DIFICULTAD, DIFICULTAD, DIFICULTAD)
    assert vistas == ["Difícil", "Fácil", "Medio"]


def test_clic_derecho_en_dificultad_va_hacia_atras(monkeypatch, app):
    pulsar(monkeypatch, app, raton(DIFICULTAD, boton=3))
    assert app.dificultad == "Fácil"


def test_clic_en_nivel_va_rotando_y_da_la_vuelta(monkeypatch, app):
    pulsar(monkeypatch, app, *[NIVEL] * 5)
    assert app.nivelElegido == "Level_5.json"
    pulsar(monkeypatch, app, NIVEL)
    assert app.nivelElegido == "Level_0.json"
    pulsar(monkeypatch, app, raton(NIVEL, boton=3))
    assert app.nivelElegido == "Level_5.json"


def test_volver_y_escape_vuelven_al_menu(monkeypatch, app):
    lanzar(monkeypatch, app, "menu")
    assert pulsar(monkeypatch, app, VOLVER) == "menu"
    assert pulsar(monkeypatch, app, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)) == "menu"


def test_quit_sale(monkeypatch, app):
    tandas(monkeypatch, [pygame.event.Event(pygame.QUIT)])
    with pytest.raises(SystemExit):
        app.pantallaNuevaPartida()


# ---- Empezar ----

def test_empezar_carga_el_nivel_y_la_dificultad_elegidos(monkeypatch, app):
    lanzar(monkeypatch, app, "on_execute")
    assert pulsar(monkeypatch, app, DIFICULTAD, NIVEL, NIVEL, EMPEZAR) == "on_execute"
    assert app.dificultad == "Difícil" and app.ficheroNivel == "Level_2.json"
    assert app.HeadNivel.NumeroNivel == 2
    assert len(app.enemigosArray) == DIFICULTADES["Difícil"]["enemigos"] == 7
    assert app.enemigosArray[0].conoVision.alcance == 5 * Laberinto.CASILLA_PIXEL
    assert app.tocaMenu is False


def test_intro_empieza(monkeypatch, app):
    lanzar(monkeypatch, app, "on_execute")
    assert pulsar(monkeypatch, app, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)) == "on_execute"
    assert app.ficheroNivel == "Level_0.json" and app.HeadNivel.NumeroNivel == 0


@pytest.mark.parametrize("dificultad, enemigos, vision", [("Fácil", 3, 3), ("Medio", 5, 4), ("Difícil", 7, 5)])
def test_dificultad_cambia_enemigos_y_vision(monkeypatch, app, dificultad, enemigos, vision):
    lanzar(monkeypatch, app, "on_execute")
    with pytest.raises(Salida):
        app.empezarPartida("Level_1.json", dificultad)
    assert len(app.enemigosArray) == len(app.EnemigosGroup) == enemigos
    assert {e.conoVision.alcance for e in app.enemigosArray} == {vision * Laberinto.CASILLA_PIXEL}


def test_medio_es_como_antes(app):
    assert DIFICULTADES["Medio"] == {"enemigos": 5, "dano": 1.0, "vision": 4}
    assert app.alcanceVisionEnemigo() == Laberinto.ALCANCE_VISION_ENEMIGO


@pytest.mark.parametrize("dificultad, dano, queda", [("Fácil", 10, 95), ("Medio", 10, 90), ("Difícil", 10, 85),
                                                     ("Fácil", 1, 99)])
def test_dificultad_cambia_el_dano_al_jugador(app, dificultad, dano, queda):
    app.definirDificultad(dificultad)
    app.HeadBarraDeVida.vida = 100
    app.herirJugador(dano)
    assert app.HeadBarraDeVida.vida == queda


def test_dificultad_desconocida(app):
    with pytest.raises(ValueError):
        app.definirDificultad("Imposible")


def test_nivel_que_no_carga_avisa_y_sigue_en_la_pantalla(monkeypatch, app, tmp_path):
    (tmp_path / "Level_9.json").write_text("{ roto", encoding="utf-8")
    monkeypatch.setattr(Laberinto, "DIR_NIVELES", str(tmp_path))
    lanzar(monkeypatch, app, "on_execute")
    titulos = []
    monkeypatch.setattr(app, "dialogoConfirmacion", lambda t, d=(), **k: titulos.append(t) or True)
    assert app.empezarPartida("Level_9.json", "Medio") is False
    assert titulos == ["No se puede cargar Level_9.json"]


@pytest.mark.parametrize("fichero, numero", [("Level_0.json", 0), ("Level_12.json", 12), ("mio.json", 0), (None, 0)])
def test_numero_de_nivel_del_fichero(fichero, numero):
    assert App.numeroDeNivel(fichero) == numero


# ---- Partida guardada ----

def test_la_partida_guardada_conserva_la_dificultad(monkeypatch, app):
    lanzar(monkeypatch, app, "on_execute")
    with pytest.raises(Salida):
        app.empezarPartida("Level_1.json", "Fácil")
    estado = app.estadoPartida()
    assert estado["dificultad"] == "Fácil" and len(estado["enemigos"]) == 3
    app.definirDificultad("Difícil")
    app.restaurarPartida(estado)
    assert app.dificultad == "Fácil" and len(app.enemigosArray) == 3


def test_partida_antigua_sin_dificultad_es_medio(monkeypatch, app):
    estado = app.estadoPartida()
    del estado["dificultad"]
    app.definirDificultad("Fácil")
    app.restaurarPartida(estado)
    assert app.dificultad == "Medio" and len(app.enemigosArray) == 5
