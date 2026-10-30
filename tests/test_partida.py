# Partida guardada (Code/partida.py): se guarda al salir del nivel o al cambiar de aplicación
# y se continúa desde el botón "Continuar partida" del menú principal.
import json
import sqlite3

import pygame
import pytest

import Laberinto
import MazeLab
import player
from estadisticas import Estadisticas
from partida import PartidaGuardada
from test_laberinto import Salida, app, enemigos_normales, lanzar, mover_jugador  # noqa: F401
from test_niveles import nivel_real, raton, tandas

JUGADOR = "Memmaker650"


# ================= PartidaGuardada (base de datos) =================
def estado_minimo(**cambios):
    estado = {"nivel": 2, "puntos": 120, "vida": 40, "tiempo_ms": 65_432, "datos": [1, 2, "ñ"]}
    estado.update(cambios)
    return estado


def test_guardar_y_cargar(tmp_path):
    ruta = str(tmp_path / "bd.db")
    assert PartidaGuardada.cargar(ruta, JUGADOR) is None
    assert PartidaGuardada.existe(ruta, JUGADOR) is False
    PartidaGuardada.guardar(ruta, JUGADOR, estado_minimo(), "salir")
    assert PartidaGuardada.cargar(ruta, JUGADOR) == estado_minimo()
    assert PartidaGuardada.existe(ruta, JUGADOR) is True


def test_resumen(tmp_path):
    ruta = str(tmp_path / "bd.db")
    assert PartidaGuardada.resumen(ruta, JUGADOR) is None
    PartidaGuardada.guardar(ruta, JUGADOR, estado_minimo(), "segundo plano")
    r = PartidaGuardada.resumen(ruta, JUGADOR)
    assert (r["nivel"], r["puntos"], r["vida"], r["tiempo_segundos"], r["motivo"]) == (2, 120, 40, 65.43, "segundo plano")
    assert "T" in r["fecha"]


def test_una_partida_por_jugador(tmp_path):
    ruta = str(tmp_path / "bd.db")
    PartidaGuardada.guardar(ruta, JUGADOR, estado_minimo(puntos=1))
    PartidaGuardada.guardar(ruta, JUGADOR, estado_minimo(puntos=2))
    PartidaGuardada.guardar(ruta, "Otra", estado_minimo(puntos=3))
    assert PartidaGuardada.cargar(ruta, JUGADOR)["puntos"] == 2
    assert PartidaGuardada.cargar(ruta, "Otra")["puntos"] == 3
    con = sqlite3.connect(ruta)
    assert con.execute("SELECT count(*) FROM partida_guardada").fetchone() == (2,)
    con.close()


def test_borrar(tmp_path):
    ruta = str(tmp_path / "bd.db")
    PartidaGuardada.guardar(ruta, JUGADOR, estado_minimo())
    PartidaGuardada.guardar(ruta, "Otra", estado_minimo())
    PartidaGuardada.borrar(ruta, JUGADOR)
    assert not PartidaGuardada.existe(ruta, JUGADOR)
    assert PartidaGuardada.existe(ruta, "Otra")
    PartidaGuardada.borrar(ruta, JUGADOR)  # borrar sin partida no falla


def test_no_toca_las_tablas_existentes(tmp_path):
    ruta = str(tmp_path / "bd.db")
    con = sqlite3.connect(ruta)
    con.execute("CREATE TABLE partida (id integer PRIMARY KEY, fecha Date, jugador text NOT NULL, "
                "puntuacion integer, nivel integer NOT NULL)")
    con.commit()
    con.close()
    PartidaGuardada.guardar(ruta, JUGADOR, estado_minimo())
    con = sqlite3.connect(ruta)
    assert con.execute("SELECT count(*) FROM partida").fetchone() == (0,)
    con.close()


# ================= Estado de la partida =================
@pytest.fixture
def juego(app):
    app.on_init()
    app.on_render()
    app.on_loop()
    return app


def matar(app, enemigo):
    while enemigo.alive():
        bala = player.Disparos(0, 300, True, 1)
        bala.rect.center = enemigo.rect.center
        app.player.balas.add(bala)
        app.player.flagDisparo = False
        app.on_loop()


def coger(app, grupo):
    sprite = next(iter(grupo))
    mover_jugador(app, sprite.rect.x + 5, sprite.rect.y + 5)
    app.on_loop()
    return MazeLab.Maze.calcularCasilla(sprite.rect.x, sprite.rect.y)


def jugar_un_rato(app):
    # Coge objetos, mata a un enemigo, recibe una herida y dispara.
    casilla_hueso = coger(app, app.maze.MazeHueso)
    coger(app, app.maze.MazeLlave)
    coger(app, app.maze.MazeBotiquin)
    muerto = enemigos_normales(app)[0]
    matar(app, muerto)
    app.herirJugador(10)
    app.estadisticas.registrarDisparo()
    app.player.municion = 7
    mover_jugador(app, 40, Laberinto.BIAS + 40)
    app.player.orientacion = 2
    app.on_loop()
    return casilla_hueso, muerto


def test_estadoPartida_es_json(juego):
    jugar_un_rato(juego)
    estado = juego.estadoPartida()
    assert json.loads(json.dumps(estado)) == estado
    assert estado["fichero"] is None and estado["nivel"] == 1
    assert estado["jugador"]["x"] == 40 and estado["jugador"]["municion"] == 7
    assert estado["jugador"]["objetos"]["llaveFinNivel"] is True
    assert estado["flagsObjetos"]["flagLlave"] is False and estado["flagsObjetos"]["flagBotiquin"] is False
    assert sum(1 for e in estado["enemigos"] if e["vida"] == 0) == 1
    assert estado["estadisticas"]["enemigosMuertos"] == 1


def nueva_app_restaurada(monkeypatch, estado):
    # Simula volver a abrir el juego: App nueva y estado restaurado.
    for nombre in ("enemigosArray", "EnemigosGroup", "PlayerGroup"):
        monkeypatch.setattr(Laberinto.App, nombre, [] if nombre == "enemigosArray" else pygame.sprite.Group())
    otra = Laberinto.App()
    otra.restaurarPartida(estado)
    otra.tocaMenu = False  # como al pulsar "Continuar partida"
    otra.on_init()
    return otra


def test_restaurar_partida_completa(monkeypatch, juego):
    casilla_hueso, muerto = jugar_un_rato(juego)
    estado = juego.estadoPartida()
    puntos, vida, huesos = juego.HeadPuntuacion.puntos, juego.HeadBarraDeVida.vida, juego.HeadHuesos.NumeroHuesos

    otra = nueva_app_restaurada(monkeypatch, estado)
    # Jugador
    assert (otra.player.x, otra.player.y, otra.player.orientacion) == (40, Laberinto.BIAS + 40, 2)
    assert otra.player.municion == 7 and otra.player.llaveFinNivel is True
    assert otra.flagInit is False
    # Marcadores
    assert (otra.HeadPuntuacion.puntos, otra.HeadBarraDeVida.vida, otra.HeadHuesos.NumeroHuesos) == (puntos, vida, huesos)
    # Objetos cogidos: no vuelven a aparecer
    assert casilla_hueso in otra.casillaObjetosTocados
    assert otra.maze.flagLlave is False and otra.maze.flagBotiquin is False
    otra.on_render()
    assert len(otra.maze.MazeLlave) == 0 and len(otra.maze.MazeBotiquin) == 0
    casillas_huesos = {MazeLab.Maze.calcularCasilla(h.rect.x, h.rect.y) for h in otra.maze.MazeHueso}
    assert casilla_hueso not in casillas_huesos
    # Enemigos: el muerto sigue muerto, los demás en su sitio
    indice = juego.enemigosArray.index(muerto)
    assert not otra.enemigosArray[indice].alive()
    assert otra.enemigosArray[indice] not in otra.EnemigosGroup
    for original, copia in zip(juego.enemigosArray, otra.enemigosArray):
        if original.alive():
            assert (copia.x, copia.y, copia.vida) == (original.x, original.y, original.vida)
    assert (otra.JefeEnemigo.x, otra.JefeEnemigo.y) == (juego.JefeEnemigo.x, juego.JefeEnemigo.y)
    assert otra.JefeEnemigo.vida == Laberinto.VIDA_JEFE
    # Estadísticas acumuladas
    assert otra.estadisticas.estado() == juego.estadisticas.estado()


def test_restaurar_sigue_el_tiempo(monkeypatch, juego):
    juego.tiempo_inicio = pygame.time.get_ticks() - 42_000
    estado = juego.estadoPartida()
    otra = nueva_app_restaurada(monkeypatch, estado)
    jugado = pygame.time.get_ticks() - otra.tiempo_inicio
    assert 42_000 <= jugado < 43_000
    assert otra.estadisticas.inicio_ms == otra.tiempo_inicio
    assert otra.tiempoJugado_ms == 0  # sólo se aplica una vez


def test_restaurar_jefe_muerto(monkeypatch, juego):
    matar(juego, juego.JefeEnemigo)
    otra = nueva_app_restaurada(monkeypatch, juego.estadoPartida())
    assert not otra.JefeEnemigo.alive()
    for _ in range(3):
        otra.on_loop()
        otra.on_render()


def test_restaurar_nivel_json_oscuro(monkeypatch, app):
    app.prepararNivel(nivel_real(2))
    app.HeadNivel.definirNumeroNivel(2)
    app.on_init()
    app.on_render()
    app.on_loop()
    estado = app.estadoPartida()
    assert estado["fichero"] == "Level_2.json"
    otra = nueva_app_restaurada(monkeypatch, estado)
    assert otra.ficheroNivel == "Level_2.json" and otra.HeadNivel.NumeroNivel == 2
    assert otra.linterna is not None
    assert len(otra.maze.posicionesEnemigos) == 41


def test_restaurar_camara_desplazada(monkeypatch, juego):
    estado = juego.estadoPartida()
    estado["camara"] = 15
    otra = nueva_app_restaurada(monkeypatch, estado)
    assert otra.maze.posicionCamara == 15 and otra.maze.movimientoCamara == 2
    xs = {p.rect.x for p in otra.maze.MazeParedes}
    assert min(xs) == -2 * Laberinto.CASILLA_PIXEL


def test_restaurar_nivel_que_ya_no_existe(app):
    with pytest.raises(FileNotFoundError):
        app.restaurarPartida({"fichero": "Level_99.json"})


# ================= Cuándo se guarda =================
def eventos_juego(app, *evs):
    pygame.event.clear()
    for ev in evs:
        pygame.event.post(ev)


def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def test_escape_guarda_la_partida(app, bd_de_prueba):
    app.HeadPuntuacion.puntos = 77
    eventos_juego(app, tecla(pygame.K_ESCAPE))
    with pytest.raises(SystemExit):
        app.on_execute()
    assert PartidaGuardada.cargar(bd_de_prueba, JUGADOR)["puntos"] == 77
    assert PartidaGuardada.resumen(bd_de_prueba, JUGADOR)["motivo"] == "salir"


def test_cerrar_la_ventana_guarda_la_partida(app, bd_de_prueba):
    eventos_juego(app, pygame.event.Event(pygame.QUIT))
    with pytest.raises(SystemExit):
        app.on_execute()
    assert PartidaGuardada.resumen(bd_de_prueba, JUGADOR)["motivo"] == "cerrar"


@pytest.mark.parametrize("tipo", Laberinto.EVENTOS_SEGUNDO_PLANO)
def test_cambiar_de_aplicacion_guarda_la_partida(monkeypatch, app, bd_de_prueba, tipo):
    motivos = []
    original = PartidaGuardada.guardar
    monkeypatch.setattr(PartidaGuardada, "guardar",
                        staticmethod(lambda r, j, e, m="salir": motivos.append(m) or original(r, j, e, m)))
    eventos_juego(app, pygame.event.Event(tipo), tecla(pygame.K_ESCAPE))
    with pytest.raises(SystemExit):
        app.on_execute()
    assert motivos == ["segundo plano", "salir"]  # sigue jugando hasta que sale con ESC


def test_eventos_de_segundo_plano():
    nombres = {pygame.event.event_name(t) for t in Laberinto.EVENTOS_SEGUNDO_PLANO}
    assert {"WindowFocusLost", "WindowMinimized", "AppWillEnterBackground"} <= nombres


def test_no_guarda_tras_morir_o_completar(juego, bd_de_prueba):
    for resultado in ("muerto", "completado"):
        juego.resultadoPartida = resultado
        assert juego.guardarPartida("salir") is False
    assert not PartidaGuardada.existe(bd_de_prueba, JUGADOR)


def test_guardar_con_error_de_bd(monkeypatch, juego, tmp_path):
    monkeypatch.setattr(Laberinto, "RUTA_BD", str(tmp_path))  # carpeta: sqlite no la abre
    assert juego.guardarPartida("salir") is False
    assert juego.hayPartidaGuardada() is False


@pytest.mark.parametrize("completado", [False, True])
def test_fin_del_nivel_borra_la_partida_guardada(monkeypatch, juego, bd_de_prueba, completado):
    juego.guardarPartida("salir")
    monkeypatch.setattr(juego, "pantallaFinal", lambda *a, **k: None)
    monkeypatch.setattr(juego, "menu", lambda: None)
    juego.terminarPartida(completado)
    assert not PartidaGuardada.existe(bd_de_prueba, JUGADOR)


# ================= Continuar partida =================
def test_continuarPartida_sin_partida_avisa(monkeypatch, app):
    dialogos = []
    monkeypatch.setattr(app, "dialogoConfirmacion", lambda t, d=(), **k: dialogos.append((t, k)))
    lanzar(monkeypatch, app, "on_execute")
    assert app.continuarPartida() is False
    assert dialogos == [("No hay ninguna partida guardada", {"textoSi": "Aceptar", "textoNo": None})]


def test_continuarPartida_restaura_y_juega(monkeypatch, juego, bd_de_prueba):
    juego.HeadPuntuacion.puntos = 321
    juego.guardarPartida("salir")
    juego.HeadPuntuacion.puntos = 0
    lanzar(monkeypatch, juego, "on_execute")
    with pytest.raises(Salida, match="on_execute"):
        juego.continuarPartida()
    assert juego.HeadPuntuacion.puntos == 321
    assert juego.tocaMenu is False


def test_continuarPartida_nivel_borrado(monkeypatch, juego, bd_de_prueba):
    estado = juego.estadoPartida()
    estado["fichero"] = "Level_99.json"
    PartidaGuardada.guardar(bd_de_prueba, JUGADOR, estado)
    titulos = []
    monkeypatch.setattr(juego, "dialogoConfirmacion", lambda t, d=(), **k: titulos.append(t))
    lanzar(monkeypatch, juego, "on_execute")
    assert juego.continuarPartida() is False
    assert titulos == ["No se puede continuar la partida"]


def test_continuarPartida_estado_corrupto(monkeypatch, juego, bd_de_prueba):
    PartidaGuardada.guardar(bd_de_prueba, JUGADOR, {"nivel": 1})  # le faltan datos
    titulos = []
    monkeypatch.setattr(juego, "dialogoConfirmacion", lambda t, d=(), **k: titulos.append(t))
    assert juego.continuarPartida() is False
    assert titulos == ["No se puede continuar la partida"]


# ================= Menú principal =================
def test_continuar_es_el_primer_boton():
    assert Laberinto.App.BOTONES_MENU[0][1:3] == ("Continuar partida", "continuar")
    posiciones = [dy for dy, *_ in Laberinto.App.BOTONES_MENU]
    assert posiciones == sorted(posiciones)


def pintar_menu(monkeypatch, app, raton_pos):
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: raton_pos)
    monkeypatch.setattr(pygame.display, "update", lambda: (_ for _ in ()).throw(Salida("frame")))
    with pytest.raises(Salida):
        app.menu()


def test_menu_continuar_desactivado_sin_partida(monkeypatch, app):
    pintar_menu(monkeypatch, app, (600, 393))  # ratón encima
    assert app.pantalla.get_at((434, 392))[:3] == Laberinto.App.COLOR_BOTON_DESACTIVADO
    grises = [x for x in range(432, 662) if app.pantalla.get_at((x, 410))[:3] == Laberinto.App.COLOR_TEXTO_DESACTIVADO]
    assert grises


def test_menu_continuar_activo_con_partida(monkeypatch, juego):
    juego.guardarPartida("salir")
    pintar_menu(monkeypatch, juego, (600, 393))
    assert juego.pantalla.get_at((434, 392))[:3] == Laberinto.color_darkorange
    blancos = [x for x in range(432, 662) if juego.pantalla.get_at((x, 410))[:3] == (255, 255, 255)]
    assert blancos and min(blancos) > 432 and max(blancos) < 662   # texto dentro del botón


def test_menu_clic_en_continuar(monkeypatch, app):
    lanzar(monkeypatch, app, "continuarPartida")
    tandas(monkeypatch, [raton((500, 395))])
    with pytest.raises(Salida, match="continuarPartida"):
        app.menu()


def test_menu_continuar_sin_partida_sigue_en_el_menu(monkeypatch, app):
    dialogos = []
    monkeypatch.setattr(app, "dialogoConfirmacion", lambda t, d=(), **k: dialogos.append(t))
    tandas(monkeypatch, [raton((500, 395))], [pygame.event.Event(pygame.QUIT)])
    with pytest.raises(SystemExit):
        app.menu()
    assert dialogos == ["No hay ninguna partida guardada"]


def test_flujo_completo_salir_y_continuar(monkeypatch, juego, bd_de_prueba):
    # Juega, sale con ESC (se guarda), vuelve a abrir el juego y pulsa "Continuar partida".
    jugar_un_rato(juego)
    puntos = juego.HeadPuntuacion.puntos
    eventos_juego(juego, tecla(pygame.K_ESCAPE))
    with pytest.raises(SystemExit):
        juego.on_execute()

    for nombre in ("enemigosArray", "EnemigosGroup", "PlayerGroup"):
        monkeypatch.setattr(Laberinto.App, nombre, [] if nombre == "enemigosArray" else pygame.sprite.Group())
    nueva = Laberinto.App()
    nueva.HeadPuntuacion.puntos = 0  # los marcadores son atributos de clase: se ponen a cero a mano
    lanzar(monkeypatch, nueva, "on_execute")
    tandas(monkeypatch, [raton((500, 395))])
    with pytest.raises(Salida, match="on_execute"):
        nueva.menu()
    assert nueva.HeadPuntuacion.puntos == puntos
    assert nueva.estadisticas.enemigosMuertos == 1
