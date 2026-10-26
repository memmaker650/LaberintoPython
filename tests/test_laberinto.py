import os
import subprocess
import sys

import pygame
import pytest

import infoPantalla
import Laberinto
import MazeLab
from Laberinto import App, BIAS, CASILLA_PIXEL
from conftest import CODE_DIR


class Salida(Exception):
    """Excepción para cortar los bucles infinitos de los menús en los tests."""


@pytest.fixture
def app(monkeypatch):
    # Atributos de clase de App que se acumularían entre tests.
    monkeypatch.setattr(App, "enemigosArray", [])
    monkeypatch.setattr(App, "PlayerGroup", pygame.sprite.Group())
    monkeypatch.setattr(App, "EnemigosGroup", pygame.sprite.Group())
    monkeypatch.setattr(App, "grupo_explosiones", pygame.sprite.Group())
    monkeypatch.setattr(App, "grupo_humo", pygame.sprite.Group())
    monkeypatch.setattr(App, "casillaObjetosTocados", set())
    monkeypatch.setattr(App, "HeadPuntuacion", infoPantalla.panelPuntuacion())
    monkeypatch.setattr(App, "HeadHuesos", infoPantalla.infoHuesos())
    monkeypatch.setattr(App, "HeadBarraDeVida", infoPantalla.barraDeVida())
    monkeypatch.setattr(App, "flagInit", True)
    monkeypatch.setattr(MazeLab.Maze, "pintaKasillaNumSuelo", MazeLab.Maze.pintaKasillaNumSuelo)
    # pygame.quit() dejaría sin pantalla al resto de tests.
    monkeypatch.setattr(pygame, "quit", lambda: None)
    pygame.event.clear()
    a = App()
    a.tocaMenu = False
    return a


@pytest.fixture
def juego(app):
    # Juego inicializado y primer frame pintado (coloca al jugador y crea los objetos).
    app.on_init()
    app.on_render()
    return app


def mover_jugador(app, x, y):
    app.player.x, app.player.y = x, y
    app.player.prev_x, app.player.prev_y = x, y


def enemigos_normales(app):
    return [e for e in app.enemigosArray if not e.isJefeEnemigo]


# ---------- Funciones y clases auxiliares ----------
def test_load_image():
    assert isinstance(Laberinto.load_image("player.png", "Resources", alpha=True), pygame.Surface)
    assert isinstance(Laberinto.load_image("player.png", "Resources"), pygame.Surface)


@pytest.mark.parametrize("carpeta", ["Code", "tests", "."])
def test_arranca_desde_cualquier_carpeta(carpeta):
    # Reproduce el error de lanzar el juego desde Code/: importar Laberinto carga todas las imágenes.
    raiz = os.path.dirname(CODE_DIR)
    codigo = ("import sys, types; "
              "sys.modules['plyer'] = types.SimpleNamespace(notification=types.SimpleNamespace(notify=lambda **k: None), orientation=None); "
              f"sys.path.insert(0, {CODE_DIR!r}); "
              "import Laberinto, os; print(os.getcwd())")
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    r = subprocess.run([sys.executable, "-c", codigo], cwd=os.path.join(raiz, carpeta),
                       env=env, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().splitlines()[-1] == raiz


def test_load_image_inexistente_sale():
    with pytest.raises(SystemExit):
        Laberinto.load_image("no_existe.png", "Resources")


def test_posicion():
    p = Laberinto.posicion(4, 5)
    assert (p.x, p.y) == (4, 5)


def test_clases_de_datos():
    assert Laberinto.estadisticasSquid.puntos == 0
    assert Laberinto.partidaGuardada.nivel == 0


# ---------- Construcción ----------
def test_app_init_coloca_enemigos_en_suelo(app):
    assert len(app.enemigosArray) == app.numEnemigos
    for e in app.enemigosArray:
        assert app.maze.esAlcanzable(e.x, e.y)
        assert e in app.EnemigosGroup


def test_app_init_coloca_jefe_en_suelo(app):
    jefe = app.JefeEnemigo
    assert jefe.isJefeEnemigo
    cx, cy = jefe.x + jefe.rect.width // 2, jefe.y + jefe.rect.height // 2
    assert app.maze.esAlcanzable(cx, cy)
    assert jefe.kia.casilla == jefe.casilla


def test_app_init_jefe_en_centro_de_casilla(app):
    jefe = app.JefeEnemigo
    assert MazeLab.Maze.estaCentroCasilla(jefe.x + jefe.rect.width // 2, jefe.y + jefe.rect.height // 2)


def test_app_init_conexiones(app):
    assert app.conexiones and all(app.maze.maze[c] == 1 for c in app.conexiones)


def test_on_init_prepara_personajes(juego):
    assert juego.player in juego.PlayerGroup
    assert juego.JefeEnemigo in juego.EnemigosGroup
    for e in juego.enemigosArray + [juego.JefeEnemigo]:
        assert e.kia.conexiones is juego.conexiones
    assert juego.floor_surf is not None and juego.wall_surf is not None
    assert juego.imagePlayer_roja.get_size() == juego.player.image.get_size()


def test_primer_render_coloca_jugador_en_inicio(juego):
    pos = MazeLab.Maze.calcularPixelPorCasilla(juego.maze.posicionInitJugador)
    assert (juego.player.x, juego.player.y) == (pos.x, pos.y)
    assert juego.flagInit is False


# ---------- Métodos auxiliares ----------
def test_verInfoEnemigos(app):
    app.verInfoEnemigos()


def test_dibujar_cruz(app, superficie):
    superficie.fill((0, 0, 0))
    app.dibujar_cruz(superficie, 100, 300)
    assert superficie.get_at((100, 300))[:3] == (255, 165, 0)
    assert superficie.get_at((96, 300))[:3] == (255, 165, 0)


def test_dibujarCaminoEnemigo(app):
    e = app.enemigosArray[0]
    e.cargarCasillaRecorrido(41)
    e.cargarCasillaRecorrido(42)
    app.pantalla.fill((0, 0, 0))
    app.dibujarCaminoEnemigo(e)
    # Línea amarilla entre los centros de las casillas 41 y 42.
    medio_x = (MazeLab.Maze.centroCasilla(41).x + MazeLab.Maze.centroCasilla(42).x) // 2
    assert app.pantalla.get_at((medio_x, MazeLab.Maze.centroCasilla(41).y))[:3] == (255, 255, 0)


def test_inventarioJuego(app):
    assert app.inventarioJuego() is None


def test_rebuildMap(juego):
    juego.map_surface.fill((1, 2, 3))
    juego.rebuildMap()
    assert juego.map_surface.get_at((5, BIAS + 5))[:3] != (1, 2, 3)


# ---------- on_loop: colisiones ----------
def test_colision_jugador_pared_revierte(juego):
    mover_jugador(juego, 40, BIAS + 40)       # casilla 41 (suelo)
    juego.player.x, juego.player.y = 5, BIAS + 5  # se mete en la pared 0
    juego.on_loop()
    assert (juego.player.x, juego.player.y) == (40, BIAS + 40)


def test_colision_jugador_enemigo(juego):
    e = enemigos_normales(juego)[0]
    mover_jugador(juego, e.x, e.y)
    juego.on_loop()
    assert juego.impactoEnemigo and juego.impactoPlayer and juego.efecto_rojo
    assert juego.enemigoImpactado is e
    assert juego.textoBocadillo == "INTRUSO encontrado !! Jefe aquí !!!"
    assert juego.JefeEnemigo.kia.playerDetectado is True
    jefe = juego.JefeEnemigo
    inicio = MazeLab.Maze.calcularCasilla(jefe.x + 11, jefe.y + 11)
    destino = MazeLab.Maze.calcularCasilla(juego.player.x + 11, juego.player.y + 11)
    assert jefe.kia.path == jefe.kia.calcular_camino_BFS(inicio, destino)


def test_colision_jugador_jefe_avisa_a_todos(juego):
    jefe = juego.JefeEnemigo
    mover_jugador(juego, jefe.x, jefe.y)
    juego.on_loop()
    assert juego.impactoJefeEnemigo is True
    assert juego.textoBocadillo == "Hay un INTRUSO !! Venid"
    destino = MazeLab.Maze.calcularCasilla(juego.player.x + 11, juego.player.y + 11)
    for e in juego.EnemigosGroup:
        assert e.kia.playerDetectado is True
        assert e.kia.casillaJugador == destino


def test_colision_enemigo_pared_revierte(juego):
    e = enemigos_normales(juego)[0]
    e.x, e.y = 5, BIAS + 5  # dentro de la pared 0
    juego.on_loop()
    # update() lo baja 1 px y la colisión lo devuelve a la posición previa.
    assert (e.x, e.y) == (5, BIAS + 5)


def test_colision_jefe_pared_lo_recentra(juego):
    jefe = juego.JefeEnemigo
    cx, cy = MazeLab.Maze.centroCasilla(41).x, MazeLab.Maze.centroCasilla(41).y
    jefe.x, jefe.y = cx - 11, cy - 11 - 20  # medio metido en la pared de arriba
    juego.on_loop()
    assert jefe.kia.colisionParedes is True or jefe.kia.casilla == 41
    assert (jefe.rect.x, jefe.rect.y) == (jefe.x, jefe.y)
    assert MazeLab.Maze.estaCentroCasilla(jefe.x + 11, jefe.y + 11)


def test_colision_enemigo_puerta_revierte(juego):
    puerta = next(iter(juego.maze.MazePuertas))
    e = enemigos_normales(juego)[0]
    e.x, e.y = puerta.rect.centerx - 11, puerta.rect.centery - 11
    y0 = e.y
    juego.on_loop()
    assert e.y == y0


def test_colision_jugador_puerta_revierte(juego):
    puerta = next(iter(juego.maze.MazePuertas))
    mover_jugador(juego, puerta.rect.centerx - 11, puerta.rect.centery - 30)
    juego.player.y = puerta.rect.centery - 11
    juego.on_loop()
    assert juego.player.y == puerta.rect.centery - 30


def coger(app, grupo):
    sprite = next(iter(grupo))
    mover_jugador(app, sprite.rect.x + 5, sprite.rect.y + 5)
    app.on_loop()
    return sprite


def test_coger_hueso(juego):
    sprite = coger(juego, juego.maze.MazeHueso)
    assert juego.HeadPuntuacion.puntos == 10
    assert juego.HeadHuesos.NumeroHuesos == 1
    assert MazeLab.Maze.calcularCasilla(sprite.rect.x, sprite.rect.y) in juego.casillaObjetosTocados


def test_coger_hueso_solo_cuenta_una_vez(juego):
    coger(juego, juego.maze.MazeHueso)
    juego.on_loop()
    assert juego.HeadPuntuacion.puntos == 10


def test_coger_oro(juego):
    coger(juego, juego.maze.MazeOro)
    assert juego.HeadPuntuacion.puntos == 100


def test_coger_pila_huesos(juego):
    coger(juego, juego.maze.MazePilaHuesos)
    assert juego.HeadPuntuacion.puntos == 50
    assert juego.HeadHuesos.NumeroHuesos == 10
    assert juego.maze.flagPilaHuesos is False


def test_coger_botiquin(juego):
    coger(juego, juego.maze.MazeBotiquin)
    assert juego.HeadBarraDeVida.vida == 90
    assert juego.maze.flagBotiquin is False


def test_coger_llave_puerta(juego):
    coger(juego, juego.maze.MazeLlavePuerta)
    assert juego.player.llavePuerta is True
    assert juego.alerta_activa is True
    assert juego.alerta_texto == "¡Has cogido la llave!"
    assert juego.maze.flagLlavePuerta is False


def test_coger_llave_final(juego):
    coger(juego, juego.maze.MazeLlave)
    assert juego.player.llaveFinNivel is True
    assert juego.maze.flagLlave is False


def test_coger_champi(juego):
    coger(juego, juego.maze.MazeChampi)
    assert juego.player.champi is True
    assert juego.maze.flagChampi is False


def test_coger_granada(juego):
    coger(juego, juego.maze.MazeGranada)
    assert juego.player.granada is True
    assert juego.maze.flagGranada is False


def test_tocar_bandera_no_la_elimina(juego):
    coger(juego, juego.maze.MazeBandera)
    assert len(juego.maze.MazeBandera) > 0


def test_bala_jugador_contra_pared(juego):
    juego.player.flagDisparo = True
    bala = Laberinto.player.Disparos(4, BIAS + 4, True, 1)
    juego.player.balas.add(bala)
    juego.on_loop()
    assert not juego.player.balas.has(bala)


def test_bala_enemigo_contra_pared(juego):
    jefe = juego.JefeEnemigo
    jefe.flagDisparo = True
    bala = Laberinto.player.Disparos(4, BIAS + 4, False, 1)
    jefe.balas.add(bala)
    juego.on_loop()
    assert not jefe.balas.has(bala)


def test_scroll_camara_desplaza_todo(juego):
    mover_jugador(juego, 40, BIAS + 40)
    e = enemigos_normales(juego)[0]
    x_enemigo = e.x
    pared = next(iter(juego.maze.MazeParedes))
    x_pared = pared.rect.x
    puerta = next(iter(juego.maze.MazePuertas))
    x_puerta = puerta.x
    juego.maze.movimientoCamara = 1
    juego.maze.flagCamaraCambio = True
    juego.on_loop()
    assert juego.player.x == 40 - CASILLA_PIXEL
    assert e.x == x_enemigo - CASILLA_PIXEL == e.rect.x
    assert pared.rect.x == x_pared - CASILLA_PIXEL
    assert puerta.x == x_puerta - CASILLA_PIXEL
    assert juego.maze.flagCamaraCambio is False


# ---------- on_render ----------
def test_render_en_pausa(juego):
    juego.pause = True
    juego.on_render()


def test_render_hud(juego):
    for attr in ("llavePuerta", "llaveFinNivel", "pistola", "granada", "laser"):
        setattr(juego.player, attr, True)
    juego.tiempo_inicio = pygame.time.get_ticks() - 10_000
    juego.on_render()
    assert juego.HeadReloj.tiempoInteger in (79, 80)
    assert juego.HeadReloj.textoReloj  # se ha convertido a texto


def test_render_reloj_no_baja_de_cero(juego):
    juego.tiempo_inicio = pygame.time.get_ticks() - 1_000_000
    juego.on_render()
    assert juego.HeadReloj.tiempoInteger == 0


def test_render_alerta_caduca(juego):
    juego.alerta_activa = True
    juego.alerta_inicio_ms = pygame.time.get_ticks()
    juego.on_render()
    assert juego.alerta_activa is True
    juego.alerta_inicio_ms = -10_000
    juego.on_render()
    assert juego.alerta_activa is False


def test_render_humo_termina(juego):
    juego.flagHumo, juego.humo_timer = True, 1
    juego.on_render()
    assert juego.flagHumo is False


def test_render_explosion_termina(juego):
    juego.flagExplosion, juego.explosion_timer = True, 1
    juego.on_render()
    assert juego.flagExplosion is False


def test_render_bocadillo(juego):
    juego.enemigoImpactado = enemigos_normales(juego)[0]
    juego.flagPintarBocadilloTexto, juego.bocadillo_timer = True, 2
    juego.impactoEnemigo, juego.textoBocadillo = True, "Hola"
    juego.on_render()
    assert juego.bocadillo_timer == 1
    juego.impactoEnemigo, juego.impactoJefeEnemigo = False, True
    juego.on_render()
    assert juego.bocadillo_timer == 0


def test_render_efecto_rojo(juego):
    juego.enemigoImpactado = enemigos_normales(juego)[0]
    juego.efecto_rojo = True
    juego.impactoPlayer = juego.impactoEnemigo = juego.impactoJefeEnemigo = True
    juego.tiempo_rojo = pygame.time.get_ticks()
    juego.on_render()
    assert juego.efecto_rojo is True
    juego.tiempo_rojo = -10_000
    juego.on_render()
    assert juego.efecto_rojo is False


def test_render_alarma_jefe_caducada(juego):
    juego.JefeEnemigo.alarma = True
    juego.JefeEnemigo.bubble_start_time = -100_000
    juego.on_render()
    assert juego.JefeEnemigo.alarma is False


def test_render_alarma_jefe_activa(juego):
    juego.JefeEnemigo.alarma = True
    juego.JefeEnemigo.bubble_start_time = pygame.time.get_ticks()
    juego.on_render()
    assert juego.JefeEnemigo.alarma is True
    # Con el bocadillo ya desvaneciéndose (alpha < 255) también se pinta.
    juego.JefeEnemigo.bubble_start_time = pygame.time.get_ticks() - 9_000
    juego.on_render()
    assert juego.JefeEnemigo.alarma is True


def test_render_disparos(juego):
    juego.player.disparo()
    juego.JefeEnemigo.disparo()
    juego.on_render()


def test_render_con_flags_de_depuracion(juego, capsys):
    juego.flagPrint_info = True
    juego.on_render()
    assert "Casillas con puerta" in capsys.readouterr().out


# ---------- Menús ----------
def clic(monkeypatch, pos, *extra):
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: pos)
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
    for ev in extra:
        pygame.event.post(ev)


def lanzar(monkeypatch, app, nombre):
    def falso(*a, **k):
        raise Salida(nombre)
    monkeypatch.setattr(app, nombre, falso)


def test_menu_escape_sale(app):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    with pytest.raises(SystemExit):
        app.menu()
    assert app.salir is True


def test_menu_quit_sale(app):
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    with pytest.raises(SystemExit):
        app.menu()


@pytest.mark.parametrize("pos, destino", [
    ((500, 450), "on_execute"),    # Nuevo Juego  (botón en y 440-480)
    ((500, 510), "menuOpciones"),  # Opciones     (botón en y 490-530)
])
def test_menu_botones(monkeypatch, app, pos, destino):
    lanzar(monkeypatch, app, destino)
    clic(monkeypatch, pos)
    with pytest.raises(Salida, match=destino):
        app.menu()
    assert app.tocaMenu is False


def test_menu_cargar_partida_no_abre_opciones(monkeypatch, app):
    # Antes, pulsar "Cargar Partida" (y 540-580) abría Opciones.
    lanzar(monkeypatch, app, "menuOpciones")
    lanzar(monkeypatch, app, "on_execute")
    clic(monkeypatch, (500, 560), pygame.event.Event(pygame.QUIT))
    with pytest.raises(SystemExit):
        app.menu()


def test_menu_clic_usa_posicion_del_evento(monkeypatch, app):
    # El ratón "está" fuera de los botones, pero el evento de clic ocurre sobre Opciones.
    lanzar(monkeypatch, app, "menuOpciones")
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (10, 10))
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(500, 510), button=1))
    with pytest.raises(Salida, match="menuOpciones"):
        app.menu()


# Botones de los dos menús: (menú, y relativa a la mitad de la pantalla, color al pasar el ratón).
BOTONES_MENUS = [
    ("menu", -60, Laberinto.color_darkorange), ("menu", -10, Laberinto.color_darkorange),
    ("menu", 40, Laberinto.color_darkorange), ("menu", 190, Laberinto.color_rojobrillante),
    ("menuOpciones", -60, Laberinto.color_darkorange), ("menuOpciones", -10, Laberinto.color_darkorange),
    ("menuOpciones", 40, Laberinto.color_darkorange), ("menuOpciones", 190, Laberinto.color_overblue),
]


@pytest.mark.parametrize("nombre_menu, dy, color_hover", BOTONES_MENUS)
def test_menus_resaltan_el_boton_bajo_el_raton(monkeypatch, app, nombre_menu, dy, color_hover):
    w, h = app.pantalla.get_size()
    # Ratón dentro del botón, cerca de su borde superior (donde antes fallaba el resaltado).
    raton = (w // 2 + 100, h // 2 + dy + 3)
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: raton)
    monkeypatch.setattr(pygame.display, "update", lambda: (_ for _ in ()).throw(Salida("frame")))
    with pytest.raises(Salida):
        getattr(app, nombre_menu)()
    assert app.pantalla.get_at((w // 2 + 2, h // 2 + dy + 2))[:3] == color_hover


def test_menu_boton_salir(monkeypatch, app):
    clic(monkeypatch, (500, 700))
    with pytest.raises(SystemExit):
        app.menu()
    assert app.salir is True


@pytest.mark.parametrize("raton", [(500, 450), (500, 500), (500, 550), (500, 700), (10, 10)])
def test_menu_pinta_estados_hover(monkeypatch, app, raton):
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: raton)
    monkeypatch.setattr(pygame.display, "update", lambda: (_ for _ in ()).throw(Salida("frame")))
    with pytest.raises(Salida):
        app.menu()


@pytest.mark.parametrize("pos, destino", [
    ((500, 445), "seleccionNivel"),  # Seleccionar Nivel (y 440-480)
    ((500, 495), "seleccionNivel"),  # Estadísticas (y 490-530; de momento abre Selección de Nivel)
    ((500, 700), "menu"),            # Volver (y 690-730)
])
def test_menuOpciones_botones(monkeypatch, app, pos, destino):
    lanzar(monkeypatch, app, destino)
    clic(monkeypatch, pos)
    with pytest.raises(Salida, match=destino):
        app.menuOpciones()


def test_menuOpciones_inventario(monkeypatch, app):
    llamadas = []
    monkeypatch.setattr(app, "inventarioJuego", lambda: llamadas.append(1))
    clic(monkeypatch, (500, 560), pygame.event.Event(pygame.QUIT))  # Inventario (y 540-580)
    with pytest.raises(SystemExit):
        app.menuOpciones()
    assert llamadas == [1]


@pytest.mark.parametrize("pos", [(500, 790), (500, 900)])
def test_menuOpciones_sin_zonas_fantasma(monkeypatch, app, pos):
    # Antes había zonas de clic sin botón en +290 y +400 que volvían al menú principal.
    lanzar(monkeypatch, app, "menu")
    clic(monkeypatch, pos, pygame.event.Event(pygame.QUIT))
    with pytest.raises(SystemExit):
        app.menuOpciones()


@pytest.mark.parametrize("raton", [(500, 450), (500, 500), (500, 550), (500, 700), (10, 10)])
def test_menuOpciones_pinta_estados_hover(monkeypatch, app, raton):
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: raton)
    monkeypatch.setattr(pygame.display, "update", lambda: (_ for _ in ()).throw(Salida("frame")))
    with pytest.raises(Salida):
        app.menuOpciones()


@pytest.mark.parametrize("dy, numero", [(dy, n) for dy, n in App.BOTONES_NIVEL if n])
def test_seleccionNivel_boton_pide_confirmacion(monkeypatch, app, dy, numero):
    pedidos = []

    def confirmar(n):
        pedidos.append(n)
        raise Salida("confirmar")
    monkeypatch.setattr(app, "confirmarCargaNivel", confirmar)
    # Clic en el borde superior del botón (antes esa franja no respondía).
    clic(monkeypatch, (500, 500 + dy + 2))
    with pytest.raises(Salida):
        app.seleccionNivel()
    assert pedidos == [numero]


def test_seleccionNivel_volver(monkeypatch, app):
    lanzar(monkeypatch, app, "menu")
    clic(monkeypatch, (500, 720))
    with pytest.raises(Salida, match="menu"):
        app.seleccionNivel()


def test_seleccionNivel_cancelar_sigue_en_el_menu(monkeypatch, app):
    # Si el diálogo se cancela, el menú sigue funcionando (y se puede salir).
    monkeypatch.setattr(app, "confirmarCargaNivel", lambda n: False)
    clic(monkeypatch, (500, 450), pygame.event.Event(pygame.QUIT))
    with pytest.raises(SystemExit):
        app.seleccionNivel()


def test_seleccionNivel_quit(app):
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    with pytest.raises(SystemExit):
        app.seleccionNivel()


@pytest.mark.parametrize("dy, numero", App.BOTONES_NIVEL)
def test_seleccionNivel_resalta_boton_y_pinta_texto(monkeypatch, app, dy, numero):
    raton = (600, 500 + dy + 3)
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: raton)
    monkeypatch.setattr(pygame.display, "update", lambda: (_ for _ in ()).throw(Salida("frame")))
    with pytest.raises(Salida):
        app.seleccionNivel()
    esperado = Laberinto.color_overblue if numero is None else Laberinto.color_darkorange
    assert app.pantalla.get_at((434, 500 + dy + 2))[:3] == esperado
    # El texto (blanco) está dentro del rectángulo del botón.
    blancos = [x for x in range(482, 600) if app.pantalla.get_at((x, 500 + dy + 22))[:3] == (255, 255, 255)]
    assert blancos


def test_on_init_con_menu(monkeypatch, app):
    app.tocaMenu = True
    lanzar(monkeypatch, app, "menu")
    with pytest.raises(Salida):
        app.on_init()


# ---------- on_execute: teclado ----------
def teclas(*eventos):
    pygame.event.clear()
    for tipo, tecla in eventos:
        pygame.event.post(pygame.event.Event(tipo, key=tecla))
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))


def ejecutar(app):
    with pytest.raises(SystemExit):
        app.on_execute()
    assert app._running is False


def test_on_execute_escape_termina(app):
    teclas()
    ejecutar(app)


def test_on_execute_quit_termina(app):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    with pytest.raises(SystemExit):
        app.on_execute()
    assert app.salir is True


def test_tecla_pausa(app):
    teclas((pygame.KEYDOWN, pygame.K_p))
    ejecutar(app)
    assert app.pause is True


def test_tecla_pausa_dos_veces(app):
    teclas((pygame.KEYDOWN, pygame.K_p), (pygame.KEYDOWN, pygame.K_p))
    ejecutar(app)
    assert app.pause is False


@pytest.mark.parametrize("tecla, orient", [
    (pygame.K_RIGHT, 1), (pygame.K_LEFT, 3), (pygame.K_UP, 0), (pygame.K_DOWN, 2),
])
def test_teclas_cursor(app, tecla, orient):
    teclas((pygame.KEYDOWN, tecla))
    ejecutar(app)
    assert app.movimiento is True
    assert app.player.orientacion == orient


@pytest.mark.parametrize("tecla", [pygame.K_RIGHT, pygame.K_LEFT, pygame.K_UP, pygame.K_DOWN])
def test_soltar_cursor_para(app, tecla):
    teclas((pygame.KEYDOWN, tecla), (pygame.KEYUP, tecla))
    ejecutar(app)
    assert app.movimiento is False
    assert (app.player.speedH, app.player.speedV) == (0, 0)


def test_tecla_espacio_dispara(app):
    app.player.municion = 3
    teclas((pygame.KEYDOWN, pygame.K_SPACE))
    ejecutar(app)
    assert app.player.municion == 2
    assert app.player.flagDisparo is True


def test_tecla_c_alterna_rectangulos(app):
    antes = app.pintaRectángulos
    teclas((pygame.KEYDOWN, pygame.K_c))
    ejecutar(app)
    assert app.pintaRectángulos is (not antes)


def test_tecla_v_alterna_vision(app):
    antes = app.pintaVision
    teclas((pygame.KEYDOWN, pygame.K_v))
    ejecutar(app)
    assert app.pintaVision is (not antes)


def test_tecla_k_alterna_numeros(app):
    antes = MazeLab.Maze.pintaKasillaNumSuelo
    teclas((pygame.KEYDOWN, pygame.K_k))
    ejecutar(app)
    assert MazeLab.Maze.pintaKasillaNumSuelo is (not antes)


def test_tecla_d_abre_puertas(juego):
    teclas((pygame.KEYDOWN, pygame.K_d))
    ejecutar(juego)
    assert juego.maze.MazePuertas and all(p.abierta for p in juego.maze.MazePuertas)


def test_puertas_siguen_abiertas_tras_rebuildMap(juego):
    for p in juego.maze.MazePuertas:
        p.abierta = True
    juego.rebuildMap()
    assert all(p.abierta for p in juego.maze.MazePuertas)


def test_tecla_x_explosion(app):
    teclas((pygame.KEYDOWN, pygame.K_x))
    ejecutar(app)
    assert app.flagExplosion is True
    assert len(app.grupo_explosiones) == 1


def test_tecla_z_humo(app):
    teclas((pygame.KEYDOWN, pygame.K_z))
    ejecutar(app)
    assert app.flagHumo is True
    assert len(app.grupo_humo) == 1


def test_tecla_s_musica_on_off(app):
    teclas((pygame.KEYDOWN, pygame.K_s))
    ejecutar(app)
    assert app.Sound.reproducirMusica is True
    teclas((pygame.KEYDOWN, pygame.K_s))
    ejecutar(app)
    assert app.Sound.reproducirMusica is False


def test_tecla_intro_enemigos_disparan(app):
    teclas((pygame.KEYDOWN, pygame.K_RETURN))
    ejecutar(app)
    assert all(e.flagDisparo for e in app.EnemigosGroup)


def test_tecla_intro_alarma_se_mantiene(app):
    app.JefeEnemigo.bubble_start_time = pygame.time.get_ticks() - 60_000
    teclas((pygame.KEYDOWN, pygame.K_RETURN))
    ejecutar(app)
    assert app.JefeEnemigo.alarma is True


@pytest.mark.parametrize("dy, texto", [(-60, "Seleccionar Nivel"), (-10, "Estadísticas"),
                                       (40, "Inventario Juego"), (190, "Volver")])
def test_menuOpciones_textos_dentro_del_boton(monkeypatch, app, dy, texto):
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (10, 10))
    monkeypatch.setattr(pygame.display, "update", lambda: (_ for _ in ()).throw(Salida("frame")))
    with pytest.raises(Salida):
        app.menuOpciones()
    w, h = app.pantalla.get_size()
    boton = pygame.Rect(w // 2, h // 2 + dy, 230, 40)
    blancos = [(x, y) for y in range(boton.top, boton.bottom) for x in range(w // 2 - 60, w)
               if app.pantalla.get_at((x, y))[:3] == (255, 255, 255)]
    assert blancos, f"no se ha pintado el texto '{texto}'"
    assert all(boton.collidepoint(p) for p in blancos), f"'{texto}' se sale del botón"
    # Centrado: margen izquierdo y derecho parecidos.
    izquierda = min(x for x, _ in blancos) - boton.left
    derecha = boton.right - max(x for x, _ in blancos)
    assert abs(izquierda - derecha) <= 4
