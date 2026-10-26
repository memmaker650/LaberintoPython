# Niveles JSON: análisis de coherencia, carga en el laberinto, diálogo de confirmación
# y carga desde el menú "Seleccionar Nivel".
import json
import os

import pygame
import pytest

import Laberinto
import MazeLab
from levels_parser import Layer, LevelData, LevelParser, informe_niveles
from test_laberinto import Salida, app, clic, lanzar  # noqa: F401 (app es un fixture)

H = MazeLab.NUM_CASILLAS_H
LEVELS_DIR = os.path.join(os.path.dirname(__file__), "..", "Levels")
NOMBRES = ["Floor", "Wall", "Bone", "DogDown1", "Exit"]
F, W, B, D, E = 1, 2, 3, 4, 5  # ids de tile (empiezan en 1)


def nivel_real(n):
    return LevelParser(LEVELS_DIR).load_by_name(f"Level_{n}.json")


def nivel(fondo, objetos=None, spawn=(1, 1), nombres=NOMBRES):
    alto, ancho = len(fondo), len(fondo[0])
    objetos = objetos or [[0] * ancho for _ in range(alto)]
    return LevelData(path="prueba.json", tileNames=list(nombres), width=ancho, height=alto,
                     tileWidth=32, tileHeight=32, playerSpawnX=spawn[0], playerSpawnY=spawn[1],
                     layers=[Layer("Background", fondo), Layer("Objects", objetos)])


# Nivel 5x4 cerrado y correcto: un pasillo con un hueso, un perro y la salida.
FONDO_OK = [
    [W, W, W, W, W],
    [W, F, F, F, W],
    [W, F, W, F, W],
    [W, W, W, W, W],
]
OBJETOS_OK = [
    [0, 0, 0, 0, 0],
    [0, 0, B, D, 0],
    [0, 0, 0, E, 0],
    [0, 0, 0, 0, 0],
]


def con(tabla, x, y, valor):
    copia = [fila[:] for fila in tabla]
    copia[y][x] = valor
    return copia


# ================= Análisis (levels_parser) =================
def test_tile_name_y_es_suelo():
    n = nivel(FONDO_OK, OBJETOS_OK)
    assert n.tile_name(1) == "Floor" and n.tile_name(5) == "Exit"
    assert n.tile_name(0) is None and n.tile_name(9) is None
    assert n.es_suelo(1, 1) and not n.es_suelo(0, 0)
    assert n.casillas_suelo() == {(1, 1), (2, 1), (3, 1), (1, 2), (3, 2)}


def test_alcanzables_y_zonas():
    n = nivel(FONDO_OK)
    assert n.alcanzables_desde(1, 1) == n.casillas_suelo()
    assert n.alcanzables_desde(0, 0) == set()
    assert n.zonas_suelo() == [5]
    partido = nivel(con(FONDO_OK, 2, 1, W))
    assert partido.zonas_suelo() == [2, 2]


def test_objetos():
    assert nivel(FONDO_OK, OBJETOS_OK).objetos() == {
        "Bone": [(2, 1)], "DogDown1": [(3, 1)], "Exit": [(3, 2)]}


def test_analizar_nivel_correcto():
    assert nivel(FONDO_OK, OBJETOS_OK).analizar() == []


@pytest.mark.parametrize("cambio, mensaje", [
    (lambda: nivel(FONDO_OK, OBJETOS_OK, spawn=(9, 9)), "fuera del mapa"),
    (lambda: nivel(FONDO_OK, OBJETOS_OK, spawn=(0, 0)), "sobre una pared"),
    (lambda: nivel(con(FONDO_OK, 2, 1, W), OBJETOS_OK), "no se pueden alcanzar desde el inicio"),
    (lambda: nivel(con(FONDO_OK, 2, 1, W), OBJETOS_OK), "dividido en 2 zonas"),
    (lambda: nivel(con(FONDO_OK, 0, 1, F), OBJETOS_OK), "borde no está cerrado"),
    (lambda: nivel(FONDO_OK, con(OBJETOS_OK, 1, 1, F)), "tile 'Floor'"),
    (lambda: nivel(FONDO_OK, con(OBJETOS_OK, 0, 0, B)), "'Bone' están sobre una pared"),
    (lambda: nivel(FONDO_OK, con(OBJETOS_OK, 1, 2, 9)), "id 9"),
    (lambda: nivel(FONDO_OK, con(OBJETOS_OK, 3, 2, 0)), "no tiene salida"),
    (lambda: nivel(FONDO_OK, con(OBJETOS_OK, 1, 2, E)), "2 salidas"),
    (lambda: nivel(con(FONDO_OK, 2, 2, B), OBJETOS_OK), "no son Floor ni Wall"),
])
def test_analizar_detecta_problemas(cambio, mensaje):
    problemas = cambio().analizar()
    assert any(mensaje in p for p in problemas), problemas


def test_analizar_objeto_inalcanzable():
    fondo = [
        [W, W, W, W, W],
        [W, F, W, F, W],
        [W, W, W, W, W],
    ]
    objetos = [[0] * 5, [0, 0, 0, E, 0], [0] * 5]
    assert any("'Exit' no se pueden alcanzar" in p for p in nivel(fondo, objetos).analizar())


def test_analizar_sin_suelo_y_sin_capas():
    assert nivel([[W, W], [W, W]]).analizar() == ["El nivel no tiene ninguna casilla de suelo"]
    sin_capa = nivel(FONDO_OK)
    sin_capa.layers = sin_capa.layers[:1]
    assert sin_capa.analizar() == ["Falta la capa 'Objects'"]


def test_mismo_mapa():
    a, b = nivel(FONDO_OK, OBJETOS_OK), nivel(FONDO_OK, OBJETOS_OK)
    assert a.mismo_mapa(b)
    assert not a.mismo_mapa(nivel(FONDO_OK))


# ---------- Los niveles reales de la carpeta Levels ----------
@pytest.mark.parametrize("n", range(6))
def test_levels_sin_problemas(n):
    assert nivel_real(n).analizar() == []


@pytest.mark.parametrize("n", range(6))
def test_levels_sin_tile_floor_en_objetos(n):
    assert "Floor" not in nivel_real(n).objetos()


def test_level_1_fondo_invertido():
    n = nivel_real(1)
    # Borde de pared y sala interior de suelo, con el inicio dentro.
    assert not n.es_suelo(0, 0) and n.es_suelo(1, 1)
    assert len(n.casillas_suelo()) == 23 * 23
    assert n.es_suelo(n.playerSpawnX, n.playerSpawnY)


def test_level_1_salida_en_la_esquina_opuesta_al_inicio():
    n = nivel_real(1)
    opuesta = (n.width - 1 - n.playerSpawnX, n.height - 1 - n.playerSpawnY)
    assert n.objetos()["Exit"] == [opuesta] == [(1, 23)]


def test_level_1_todos_los_perros_sobre_suelo():
    n = nivel_real(1)
    perros = n.objetos()["DogDown1"]
    assert len(perros) == 40
    assert all(n.es_suelo(x, y) for x, y in perros)
    assert (1, 12) in perros and (0, 12) not in perros


@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_levels_2_a_5_borde_cerrado_con_marco(n):
    nv = nivel_real(n)
    assert (nv.width, nv.height) == (27, 27)
    assert (nv.playerSpawnX, nv.playerSpawnY) == (25, 1)
    borde = [(x, y) for x in range(27) for y in range(27) if x in (0, 26) or y in (0, 26)]
    assert not any(nv.es_suelo(x, y) for x, y in borde)
    assert nv.mismo_mapa(nivel_real(0))


def test_informe_niveles():
    texto = informe_niveles(LEVELS_DIR)
    assert "Level_0.json: 27x27" in texto
    assert "Es idéntico a Level_0.json, Level_2.json, Level_3.json, Level_4.json" in texto
    assert "Level_1.json: 25x25, inicio (23, 1)" in texto
    assert "1 Exit, oscuro (90%)" in texto


def test_informe_niveles_ok(tmp_path):
    datos = {"tileNames": NOMBRES, "width": 5, "height": 4, "tileWidth": 32, "tileHeight": 32,
             "playerSpawnX": 1, "playerSpawnY": 1,
             "layers": [{"name": "Background", "tiles": FONDO_OK}, {"name": "Objects", "tiles": OBJETOS_OK}]}
    (tmp_path / "Level_1.json").write_text(json.dumps(datos), encoding="utf-8")
    assert informe_niveles(str(tmp_path)).splitlines()[-1] == "  - OK"


# ================= Carga en el laberinto (MazeLab) =================
def test_maze_desde_nivel_real():
    n = nivel_real(2)
    m = MazeLab.Maze(n)
    assert m.desplazamientoNivel == (1, 0)
    assert m.maze.count(1) == len(n.casillas_suelo())
    assert len(m.MazeParedes) == m.maze.count(0)
    sx, sy = n.playerSpawnX + 1, n.playerSpawnY
    assert m.casillaInicioJugador() == sy * H + sx
    assert m.mazeDataExtra.count(2) == 19        # huesos
    assert m.mazeDataExtra.count(4) == 1         # salida -> bandera de fin de nivel
    assert len(m.posicionesEnemigos) == 41       # perros -> posiciones de enemigos
    # Todo lo que no es del nivel es pared (marco cerrado).
    assert all(v == 0 for v in m.maze[:H])
    assert all(m.maze[y * H] == 0 for y in range(MazeLab.NUM_CASILLAS_VERTI))


def test_maze_nivel_de_27_filas_no_se_desplaza_en_vertical():
    m = MazeLab.Maze(nivel_real(0))
    assert m.desplazamientoNivel == (1, 0)
    assert m.casillaInicioJugador() == 2 * H + 3


def test_maze_ignora_objetos_sobre_pared():
    m = MazeLab.Maze(nivel(FONDO_OK, con(con(OBJETOS_OK, 0, 0, B), 4, 3, D)))
    assert m.mazeDataExtra.count(2) == 1          # sólo el hueso sobre suelo
    assert m.posicionesEnemigos == [2 * H + 4]   # el perro sobre pared no cuenta


def test_maze_desde_level_1():
    m = MazeLab.Maze(nivel_real(1))
    assert m.desplazamientoNivel == (1, 1)
    assert m.mazeDataExtra.count(2) == 16
    assert m.mazeDataExtra.index(4) == 24 * H + 2  # salida en (1, 23) + desplazamiento
    assert len(m.posicionesEnemigos) == 40
    assert m.casillaInicioJugador() == 2 * H + 24


def test_maze_desde_nivel_pequeno():
    m = MazeLab.Maze(nivel(FONDO_OK, OBJETOS_OK))
    assert m.mazeDataExtra[2 * H + 3] == 2       # hueso en (2,1) + desplazamiento
    assert m.mazeDataExtra[3 * H + 4] == 4       # salida
    assert m.posicionesEnemigos == [2 * H + 4]
    assert m.casillaInicioJugador() == 2 * H + 2


def test_maze_nivel_demasiado_grande():
    fondo = [[F] * (H + 1)]
    with pytest.raises(ValueError, match="máximo"):
        MazeLab.Maze(nivel(fondo, spawn=(0, 0)))


def test_maze_inicio_invalido_no_borra_el_laberinto_actual(maze):
    paredes = len(MazeLab.Maze.MazeParedes)
    with pytest.raises(ValueError, match="inicio del jugador"):
        MazeLab.Maze(nivel(FONDO_OK, OBJETOS_OK, spawn=(0, 0)))
    assert len(MazeLab.Maze.MazeParedes) == paredes


def test_maze_no_acumula_paredes_al_recargar():
    MazeLab.Maze()
    m = MazeLab.Maze(nivel_real(2))
    assert len(m.MazeParedes) == m.maze.count(0)


def test_maze_por_defecto_inicio_jugador():
    assert MazeLab.Maze().casillaInicioJugador() == 977


# ================= prepararNivel (App) =================
def _lejos(c, inicio):
    return abs(c % H - inicio % H) + abs(c // H - inicio // H) >= 4


def test_prepararNivel_coloca_enemigos_en_perros_del_nivel(app):
    app.prepararNivel(nivel_real(2))
    perros = set(app.maze.posicionesEnemigos)
    inicio = app.maze.casillaInicioJugador()
    casillas = [e.casilla for e in app.enemigosArray] + [app.JefeEnemigo.casilla]
    assert len(set(casillas)) == len(casillas) == app.numEnemigos + 1
    assert all(c in perros and _lejos(c, inicio) for c in casillas)
    jefe = app.JefeEnemigo
    assert MazeLab.Maze.estaCentroCasilla(jefe.x + 11, jefe.y + 11)


def test_prepararNivel_sin_perros_usa_suelo_visible(app):
    app.prepararNivel()
    inicio = app.maze.casillaInicioJugador()
    for e in app.enemigosArray:
        assert app.maze.MazeLaberinto[e.casilla] == 1
        assert MazeLab.Maze.elementoVisibleCasilla(e.casilla)
        assert _lejos(e.casilla, inicio)


def test_prepararNivel_reinicia_la_partida(app):
    app.casillaObjetosTocados.add(5)
    app.flagInit = False
    app.rebuild_map = False
    app.prepararNivel(nivel_real(0))
    assert app.casillaObjetosTocados == set()
    assert app.flagInit is True and app.rebuild_map is True
    assert all(e in app.EnemigosGroup for e in app.enemigosArray)


def test_prepararNivel_sin_sitio_para_enemigos(app):
    fondo = [[W] * 5, [W, F, F, F, W], [W] * 5]
    with pytest.raises(ValueError, match="suficientes casillas"):
        app.prepararNivel(nivel(fondo, [[0] * 5, [0, 0, 0, E, 0], [0] * 5]))


@pytest.mark.parametrize("n", [0, 1, 2])
def test_jugar_nivel_cargado(app, n):
    app.prepararNivel(nivel_real(n))
    app.on_init()
    for _ in range(30):
        app.on_loop()
        app.on_render()
    pos = MazeLab.Maze.calcularPixelPorCasilla(app.maze.casillaInicioJugador())
    assert (app.player.x, app.player.y) == (pos.x, pos.y)
    assert app.maze.posicionInitJugador == app.maze.casillaInicioJugador()


# ================= Diálogo de confirmación =================
def eventos(*evs):
    pygame.event.clear()
    for ev in evs:
        pygame.event.post(ev)


def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def raton(pos, boton=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=boton)


@pytest.mark.parametrize("k, esperado", [
    (pygame.K_RETURN, True), (pygame.K_KP_ENTER, True), (pygame.K_ESCAPE, False),
])
def test_dialogo_teclado(app, k, esperado):
    eventos(tecla(k))
    assert app.dialogoConfirmacion("¿Seguro?") is esperado


def test_dialogo_botones_raton(app):
    # Primera llamada sólo para conocer dónde quedan los botones.
    eventos(tecla(pygame.K_ESCAPE))
    app.dialogoConfirmacion("¿Seguro?", ["detalle"])
    si, no = app.botonDialogoSi.center, app.botonDialogoNo.center
    eventos(raton(si))
    assert app.dialogoConfirmacion("¿Seguro?", ["detalle"]) is True
    eventos(raton(no))
    assert app.dialogoConfirmacion("¿Seguro?", ["detalle"]) is False


def test_dialogo_ignora_clics_fuera_y_boton_derecho(app):
    eventos(tecla(pygame.K_ESCAPE))
    app.dialogoConfirmacion("x")
    si = app.botonDialogoSi.center
    eventos(raton((5, 5)), raton(si, boton=3), tecla(pygame.K_RETURN))
    assert app.dialogoConfirmacion("x") is True


def test_dialogo_un_solo_boton_centrado(app):
    eventos(tecla(pygame.K_RETURN))
    assert app.dialogoConfirmacion("Error", ["algo"], textoSi="Aceptar", textoNo=None) is True
    assert app.botonDialogoNo is None
    assert app.botonDialogoSi.centerx == app.pantalla.get_width() // 2


def test_dialogo_pinta_caja_y_resalta(monkeypatch, app):
    eventos(tecla(pygame.K_ESCAPE))
    app.dialogoConfirmacion("x")
    si = app.botonDialogoSi
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: si.center)
    monkeypatch.setattr(pygame.display, "update", lambda: (_ for _ in ()).throw(Salida("frame")))
    pygame.event.clear()
    with pytest.raises(Salida):
        app.dialogoConfirmacion("x")
    assert app.pantalla.get_at((si.left + 10, si.centery))[:3] == Laberinto.color_darkorange
    assert app.pantalla.get_at((app.botonDialogoNo.left + 10, app.botonDialogoNo.centery))[:3] == \
        Laberinto.color_darkblue


def test_dialogo_quit_sale(app):
    eventos(pygame.event.Event(pygame.QUIT))
    with pytest.raises(SystemExit):
        app.dialogoConfirmacion("x")


def test_partirTexto():
    fuente = pygame.font.SysFont("Corbel", 24)
    texto = "uno dos tres cuatro cinco seis siete ocho nueve diez " * 3
    lineas = App_partir(texto, fuente, 200)
    assert len(lineas) > 1
    assert all(fuente.size(l)[0] <= 200 for l in lineas)
    assert " ".join(lineas) == texto.strip()
    assert App_partir("", fuente, 200) == []
    assert App_partir("palabramuylargaquenocabe", fuente, 10) == ["palabramuylargaquenocabe"]


def App_partir(texto, fuente, ancho):
    return Laberinto.App.partirTexto(texto, fuente, ancho)


# ================= Confirmar y cargar un nivel =================
def test_confirmarCargaNivel_cancelar_y_avisa_de_problemas(monkeypatch, app, tmp_path):
    # Nivel válido para cargar, pero sin salida: el diálogo lo avisa.
    datos = {"tileNames": NOMBRES, "width": 5, "height": 4, "tileWidth": 32, "tileHeight": 32,
             "playerSpawnX": 1, "playerSpawnY": 1,
             "layers": [{"name": "Background", "tiles": FONDO_OK},
                        {"name": "Objects", "tiles": con(OBJETOS_OK, 3, 2, 0)}]}
    (tmp_path / "Level_1.json").write_text(json.dumps(datos), encoding="utf-8")
    monkeypatch.setattr(Laberinto, "DIR_NIVELES", str(tmp_path))
    maze_antes = app.maze
    dialogos = []
    monkeypatch.setattr(app, "dialogoConfirmacion", lambda t, d=(), **k: dialogos.append((t, d)) or False)
    lanzar(monkeypatch, app, "on_execute")
    assert app.confirmarCargaNivel(1) is False
    assert app.maze is maze_antes
    titulo, detalle = dialogos[0]
    assert titulo == "¿Cargar el Nivel 1?"
    assert detalle[0] == "Fichero Level_1.json: 5x4 casillas"
    assert detalle[1] == "Aviso: el nivel tiene 1 problema(s). El nivel no tiene salida ('Exit')"


def test_confirmarCargaNivel_nivel_sin_problemas_no_avisa(monkeypatch, app):
    dialogos = []
    monkeypatch.setattr(app, "dialogoConfirmacion", lambda t, d=(), **k: dialogos.append(d) or False)
    app.confirmarCargaNivel(3)
    assert dialogos == [["Fichero Level_3.json: 27x27 casillas"]]


def test_confirmarCargaNivel_avisa_de_nivel_oscuro(monkeypatch, app):
    dialogos = []
    monkeypatch.setattr(app, "dialogoConfirmacion", lambda t, d=(), **k: dialogos.append(d) or False)
    app.confirmarCargaNivel(2)
    assert dialogos == [["Fichero Level_2.json: 27x27 casillas",
                         "Nivel oscuro: sólo verás lo que ilumine tu linterna."]]


def test_confirmarCargaNivel_si_carga_y_empieza(monkeypatch, app):
    monkeypatch.setattr(app, "dialogoConfirmacion", lambda *a, **k: True)
    lanzar(monkeypatch, app, "on_execute")
    with pytest.raises(Salida, match="on_execute"):
        app.confirmarCargaNivel(0)
    assert app.maze.desplazamientoNivel == (1, 0)
    assert app.HeadNivel.NumeroNivel == 0
    assert app.tocaMenu is False


def test_confirmarCargaNivel_con_teclado(monkeypatch, app):
    # Recorrido real: el diálogo se responde con INTRO.
    lanzar(monkeypatch, app, "on_execute")
    eventos(tecla(pygame.K_RETURN))
    with pytest.raises(Salida):
        app.confirmarCargaNivel(3)
    assert len(app.maze.posicionesEnemigos) == 41


def test_confirmarCargaNivel_fichero_inexistente(monkeypatch, app, tmp_path):
    monkeypatch.setattr(Laberinto, "DIR_NIVELES", str(tmp_path))
    dialogos = []
    monkeypatch.setattr(app, "dialogoConfirmacion", lambda t, d=(), **k: dialogos.append((t, k)) or True)
    assert app.confirmarCargaNivel(4) is False
    assert dialogos == [("No se puede cargar el Nivel 4", {"textoSi": "Aceptar", "textoNo": None})]


def test_confirmarCargaNivel_nivel_no_valido(monkeypatch, app, tmp_path):
    datos = {"tileNames": NOMBRES, "width": 5, "height": 4, "tileWidth": 32, "tileHeight": 32,
             "playerSpawnX": 0, "playerSpawnY": 0,  # inicio sobre pared
             "layers": [{"name": "Background", "tiles": FONDO_OK}, {"name": "Objects", "tiles": OBJETOS_OK}]}
    (tmp_path / "Level_1.json").write_text(json.dumps(datos), encoding="utf-8")
    monkeypatch.setattr(Laberinto, "DIR_NIVELES", str(tmp_path))
    maze_antes = app.maze
    titulos = []
    monkeypatch.setattr(app, "dialogoConfirmacion", lambda t, d=(), **k: titulos.append(t) or True)
    assert app.confirmarCargaNivel(1) is False
    assert titulos == ["¿Cargar el Nivel 1?", "No se puede cargar el Nivel 1"]
    assert app.maze is maze_antes


def tandas(monkeypatch, *lotes):
    # Cada llamada a pygame.event.get() devuelve la siguiente tanda (como en el juego real,
    # donde el clic en "Sí" llega cuando el diálogo ya está abierto).
    # Una tanda puede ser una función: se evalúa en ese momento (p. ej. para clicar en el
    # botón del diálogo que está abierto, cuya posición depende de su contenido).
    pendientes = list(lotes)

    def obtener(*a, **k):
        if not pendientes:
            raise Salida("sin más eventos")
        lote = pendientes.pop(0)
        return list(lote() if callable(lote) else lote)
    monkeypatch.setattr(pygame.event, "get", obtener)


def test_menu_nivel_dialogo_si_completo(monkeypatch, app):
    # Del menú al juego: clic en "Nivel 2" -> diálogo -> clic en "Sí" -> empieza la partida.
    lanzar(monkeypatch, app, "on_execute")
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (500, 495))
    tandas(monkeypatch, [raton((500, 495))], [], lambda: [raton(app.botonDialogoSi.center)])
    with pytest.raises(Salida, match="on_execute"):
        app.seleccionNivel()
    assert app.HeadNivel.NumeroNivel == 2
    assert len(app.maze.posicionesEnemigos) == 41


def test_menu_nivel_dialogo_cancelar_completo(monkeypatch, app):
    # Clic en "Nivel 1" -> diálogo -> "Cancelar" -> se vuelve al menú sin cargar nada.
    lanzar(monkeypatch, app, "on_execute")
    maze_antes = app.maze
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (500, 445))
    tandas(monkeypatch, [raton((500, 445))], [], lambda: [raton(app.botonDialogoNo.center)], [])
    with pytest.raises(Salida, match="sin más eventos"):
        app.seleccionNivel()
    assert app.maze is maze_antes


# ================= Cámara y posición inicial =================
def test_nivel_que_cabe_en_pantalla_fija_la_camara():
    m = MazeLab.Maze(nivel_real(2))
    assert m.camaraFija is True
    m.moverCamara(26 * 32 + 5, MazeLab.BIAS + 32 + 5)
    assert m.posicionCamara == 13 and m.flagCamaraCambio is False


def test_laberinto_por_defecto_mantiene_la_camara_movil():
    assert MazeLab.Maze().camaraFija is False


def test_inicio_en_la_ultima_columna_visible(app):
    # Level_2 empieza en la columna 26: el jugador no debe moverse de su casilla de inicio.
    app.prepararNivel(nivel_real(2))
    app.on_init()
    for _ in range(5):
        app.on_loop()
        app.on_render()
    assert MazeLab.Maze.calcularCasilla(app.player.x, app.player.y) == app.maze.casillaInicioJugador()
    assert (app.player.prev_x, app.player.prev_y) == (app.player.x, app.player.y)
