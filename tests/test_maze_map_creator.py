# Editor de niveles MazeMapCreator: modelo (mapa.py) e interfaz (maze_map_creator.py).
import json
import os
import sys

import pygame
import pytest

from conftest import RAIZ

DIR_EDITOR = os.path.join(RAIZ, "MazeMapCreator")
if DIR_EDITOR not in sys.path:
    sys.path.insert(0, DIR_EDITOR)

import mapa as modelo  # noqa: E402
import maze_map_creator as mmc  # noqa: E402
from levels_parser import LevelParser  # noqa: E402
from mapa import BORRAR, ENEMIGO, INICIO, PARED, SUELO, Mapa  # noqa: E402

NIVELES = os.path.join(RAIZ, "Levels")


def json_nivel(ancho, alto, fondo=None, objetos=None, inicio=(1, 1), nombres=None, **extra):
    nombres = nombres or ["Floor", "Wall", "Exit", "Gold", "DogDown1", "Door"]
    fondo = fondo or [[2 if x in (0, ancho - 1) or y in (0, alto - 1) else 1 for x in range(ancho)]
                      for y in range(alto)]
    objetos = objetos or [[0] * ancho for _ in range(alto)]
    return dict(tileNames=nombres, width=ancho, height=alto, tileWidth=32, tileHeight=32,
                playerSpawnX=inicio[0], playerSpawnY=inicio[1],
                layers=[{"name": "Background", "tiles": fondo}, {"name": "Objects", "tiles": objetos}], **extra)


# ---------- Modelo ----------

def test_mapa_nuevo_32x32_con_borde_de_pared():
    m = Mapa()
    assert (m.ancho, m.alto) == (32, 32) and m.inicio == (1, 1) and m.objetos == {}
    assert all(c == PARED for c in m.fondo[0] + m.fondo[-1] + [f[0] for f in m.fondo] + [f[-1] for f in m.fondo])
    assert m.fondo[5][5] == SUELO


@pytest.mark.parametrize("ancho, alto", [(2, 10), (10, 201), (0, 0)])
def test_tamano_no_valido(ancho, alto):
    with pytest.raises(ValueError):
        Mapa(ancho, alto)


def test_pintar_suelo_pared_y_objetos():
    m = Mapa(10, 8)
    assert m.pintar(0, 0, "Gold") is True           # un objeto sobre pared la convierte en suelo
    assert m.fondo[0][0] == SUELO and m.objetos[(0, 0)] == "Gold"
    assert m.pintar(0, 0, "Gold") is False          # sin cambios
    assert m.pintar(0, 0, PARED) is True            # la pared quita el objeto
    assert m.fondo[0][0] == PARED and (0, 0) not in m.objetos
    m.pintar(3, 3, ENEMIGO)
    m.pintar(3, 3, BORRAR)
    assert (3, 3) not in m.objetos and m.fondo[3][3] == SUELO
    assert m.pintar(99, 99, SUELO) is False


def test_inicio_del_jugador_es_unico():
    m = Mapa(10, 8)
    m.pintar(5, 0, INICIO)
    assert m.inicio == (5, 0) and m.fondo[0][5] == SUELO


def test_boton_derecho_quita_objeto_y_luego_pone_pared():
    m = Mapa(10, 8)
    m.pintar(4, 4, "Door")
    m.borrar(4, 4)
    assert (4, 4) not in m.objetos and m.fondo[4][4] == SUELO
    m.borrar(4, 4)
    assert m.fondo[4][4] == PARED


def test_herramienta_desconocida():
    with pytest.raises(ValueError):
        Mapa(5, 5).pintar(1, 1, "Dragón")


def test_redimensionar_conserva_lo_que_cabe():
    m = Mapa(10, 10)
    m.pintar(2, 2, "Exit")
    m.pintar(8, 8, "Gold")
    m.pintar(7, 7, INICIO)
    m.redimensionar(6, 12)
    assert (m.ancho, m.alto) == (6, 12) and len(m.fondo) == 12 and {len(f) for f in m.fondo} == {6}
    assert m.objetos == {(2, 2): "Exit"} and m.inicio is None
    assert m.fondo[11] == [PARED] * 6               # casillas nuevas: pared


def test_estado_y_restaurar():
    m = Mapa(6, 6)
    antes = m.estado()
    m.pintar(2, 2, "Gold")
    m.redimensionar(8, 8)
    m.restaurar(antes)
    assert m.estado() == antes and (m.ancho, m.alto) == (6, 6)


@pytest.mark.parametrize("fichero", [f for f in sorted(os.listdir(NIVELES)) if f.endswith(".json")])
def test_importar_y_exportar_los_niveles_del_juego(tmp_path, fichero):
    # Importar y exportar no cambia el mapa: fondo, objetos, inicio y oscuridad son los mismos.
    original = LevelParser(NIVELES).load_by_name(fichero) if fichero != "Level_3.json" else None
    m, avisos = Mapa.importar(os.path.join(NIVELES, fichero))
    m.exportar(tmp_path / fichero)
    copia = LevelParser(str(tmp_path)).load_by_name(fichero)
    assert (copia.width, copia.height) == (m.ancho, m.alto)
    if original is not None:
        assert avisos == []
        assert (copia.width, copia.height, copia.playerSpawnX, copia.playerSpawnY, copia.oscuridad) == \
               (original.width, original.height, original.playerSpawnX, original.playerSpawnY, original.oscuridad)
        assert copia.casillas_suelo() == original.casillas_suelo()
        assert copia.objetos() == original.objetos()


def test_importar_cabecera_que_no_cuadra_con_las_casillas():
    # Como Level_3.json: dice 27x27 pero las casillas son 48x32.
    datos = json_nivel(48, 32)
    datos["width"] = datos["height"] = 27
    m, avisos = Mapa.desdeJson(datos)
    assert (m.ancho, m.alto) == (48, 32)
    assert avisos == ["La cabecera dice 27x27 pero las casillas son 48x32: se usa 48x32"]


def test_importar_convierte_los_ids_por_nombre():
    # Los niveles antiguos tienen otros tileNames: se traducen por nombre a los ids de Level_0.
    objetos = [[0] * 6 for _ in range(5)]
    objetos[1][1], objetos[2][3], objetos[3][4] = 3, 4, 6     # Exit, Gold, Door
    m, avisos = Mapa.desdeJson(json_nivel(6, 5, objetos=objetos, inicio=(2, 1)))
    assert avisos == [] and m.inicio == (2, 1)
    assert m.objetos == {(1, 1): "Exit", (3, 2): "Gold", (4, 3): "Door"}
    datos = m.aJson()
    assert datos["tileNames"] == modelo.TILE_NAMES
    ids = {n: i + 1 for i, n in enumerate(modelo.TILE_NAMES)}
    assert datos["layers"][1]["tiles"][1][1] == ids["Exit"] and datos["layers"][1]["tiles"][3][4] == ids["Door"]


def test_importar_avisa_de_lo_raro():
    fondo = [[2] * 5, [2, 1, 3, 1, 2], [2, 1, 1, 1], [2] * 5, [2] * 5]
    objetos = [[0] * 5 for _ in range(5)]
    objetos[1][1] = 9                                          # id que no existe
    m, avisos = Mapa.desdeJson(json_nivel(5, 5, fondo=fondo, objetos=objetos, inicio=(9, 9)))
    assert m.fondo[1][2] == PARED and m.fondo[2][4] == PARED and m.inicio is None
    assert any("filas más cortas" in a for a in avisos)
    assert any("no eran Floor ni Wall" in a for a in avisos)
    assert any("id 9" in a for a in avisos)
    assert any("fuera del mapa" in a for a in avisos)


def test_importar_sin_fondo():
    with pytest.raises(ValueError):
        Mapa.desdeJson({"layers": []})


def test_exportar_como_los_niveles_del_juego(tmp_path):
    m = Mapa(6, 5)
    m.oscuridad = 0.9
    m.exportar(tmp_path / "Level_9.json")
    texto = (tmp_path / "Level_9.json").read_text(encoding="utf-8")
    assert json.loads(texto) == m.aJson()
    assert "        [2, 2, 2, 2, 2, 2]," in texto              # una fila del mapa por línea
    assert json.loads(texto)["oscuridad"] == 0.9
    assert "oscuridad" not in Mapa(6, 5).aJson()


def test_problemas_como_los_del_juego():
    m = Mapa(12, 10)
    assert "El nivel no tiene salida ('Exit')" in m.problemas()
    m.pintar(5, 5, "Exit")
    assert m.problemas() == []
    m.pintar(1, 1, PARED)                                      # el jugador queda sobre pared
    assert any("pared" in p for p in m.problemas())
    m.inicio = None
    assert "Falta la casilla de inicio del jugador" in m.problemas()


def test_problema_mapa_mas_grande_que_el_juego():
    m = Mapa()                                                 # 32x32 por defecto
    assert m.problemas()[0] == "El juego admite como máximo 40x27 casillas; este mapa mide 32x32"
    m.redimensionar(40, 27)
    assert not any("como máximo" in p for p in m.problemas())


# ---------- Interfaz ----------

@pytest.fixture
def editor(monkeypatch, tmp_path):
    monkeypatch.setattr(modelo, "DIR_NIVELES", str(tmp_path))
    pantalla = pygame.display.set_mode(mmc.TAMANO_VENTANA)
    e = mmc.Editor(pantalla)
    e.dibujar()
    return e


def clic(editor, pos, boton=1):
    editor.manejar(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=boton))
    editor.manejar(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=boton))


def centro_casilla(editor, x, y):
    rect, c = editor.rectMapa(), editor.tamanoCasilla()
    return rect.x + x * c + c // 2, rect.y + y * c + c // 2


def escribir(editor, texto):
    editor.manejar(pygame.event.Event(pygame.TEXTINPUT, text=texto))


def tecla(editor, key, mod=0):
    editor.manejar(pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod, unicode=""))


def elegir(editor, herramienta):
    i = [h for h, _, _ in mmc.ELEMENTOS].index(herramienta)
    clic(editor, editor.rectElemento(i).center)
    assert editor.herramienta == herramienta


def test_disposicion(editor):
    # Elementos a la izquierda, tamaño arriba a la derecha y el mapa ocupando el centro.
    ancho, alto = editor.pantalla.get_size()
    assert all(editor.rectElemento(i).right <= mmc.ANCHO_PANEL for i in range(len(mmc.ELEMENTOS)))
    assert editor.rectElemento(len(mmc.ELEMENTOS) - 1).bottom <= alto
    assert editor.botones["aplicar"].right == ancho - mmc.MARGEN and editor.botones["aplicar"].top < mmc.ALTO_BARRA
    assert editor.campos[0].rect.right < editor.campos[1].rect.x < editor.botones["aplicar"].x
    assert [c.texto for c in editor.campos] == ["32", "32"]
    rect = editor.rectMapa()
    assert rect.left >= mmc.ANCHO_PANEL and rect.top >= mmc.ALTO_BARRA and rect.size == (32 * 21, 32 * 21)
    assert editor.casillaEn(rect.topleft) == (0, 0) and editor.casillaEn((5, 5)) is None


def test_hay_un_elemento_por_cada_objeto_del_juego():
    herramientas = {h for h, _, _ in mmc.ELEMENTOS}
    assert set(modelo.OBJETOS) | {SUELO, PARED, INICIO, BORRAR} == herramientas


def test_iconos_de_todos_los_elementos(editor):
    for herramienta, _, fichero in mmc.ELEMENTOS:
        assert editor.icono(herramienta, 26).get_size() == (26, 26)
        if fichero:
            assert editor.iconos.get(fichero) is not None or herramienta in (SUELO, PARED), fichero


def test_pintar_con_el_raton_y_arrastrar(editor):
    elegir(editor, "Gold")
    clic(editor, centro_casilla(editor, 3, 3))
    assert editor.mapa.objetos[(3, 3)] == "Gold" and editor.cambios
    elegir(editor, PARED)
    editor.manejar(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=centro_casilla(editor, 2, 5), button=1))
    editor.manejar(pygame.event.Event(pygame.MOUSEMOTION, pos=centro_casilla(editor, 9, 5), rel=(0, 0), buttons=(1, 0, 0)))
    editor.manejar(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=centro_casilla(editor, 9, 5), button=1))
    assert all(editor.mapa.fondo[5][x] == PARED for x in range(2, 10))   # sin huecos aunque el ratón salte
    assert len(editor.deshacer) == 2                                      # un deshacer por trazo
    editor.dibujar()


def test_boton_derecho_borra(editor):
    elegir(editor, "Door")
    clic(editor, centro_casilla(editor, 4, 4))
    clic(editor, centro_casilla(editor, 4, 4), boton=3)
    assert (4, 4) not in editor.mapa.objetos


def test_deshacer(editor):
    elegir(editor, PARED)
    clic(editor, centro_casilla(editor, 6, 6))
    tecla(editor, pygame.K_z, pygame.KMOD_META)
    assert editor.mapa.fondo[6][6] == SUELO
    clic(editor, editor.botones["deshacer"].center)
    assert editor.mensaje == "No hay nada que deshacer."


def test_cambiar_tamano_desde_los_campos(editor):
    clic(editor, editor.campos[0].rect.center)
    for _ in range(2):
        tecla(editor, pygame.K_BACKSPACE)
    escribir(editor, "4a0")                                   # sólo cuenta lo numérico
    tecla(editor, pygame.K_TAB)
    tecla(editor, pygame.K_BACKSPACE)
    tecla(editor, pygame.K_BACKSPACE)
    escribir(editor, "27")
    tecla(editor, pygame.K_RETURN)
    assert (editor.mapa.ancho, editor.mapa.alto) == (40, 27)
    editor.dibujar()
    assert editor.rectMapa().size == (40 * editor.tamanoCasilla(), 27 * editor.tamanoCasilla())
    tecla(editor, pygame.K_z, pygame.KMOD_CTRL)
    assert (editor.mapa.ancho, editor.mapa.alto) == (32, 32) and editor.campos[0].texto == "32"


def test_tamano_no_valido_avisa(editor):
    editor.campos[0].texto = "500"
    clic(editor, editor.botones["aplicar"].center)
    assert "entre 3 y 200" in editor.mensaje and editor.mapa.ancho == 32 and editor.campos[0].texto == "32"


def test_nuevo_con_el_tamano_de_los_campos(editor):
    editor.mapa.pintar(3, 3, "Gold")
    editor.campos[0].texto, editor.campos[1].texto = "20", "15"
    clic(editor, editor.botones["nuevo"].center)
    assert (editor.mapa.ancho, editor.mapa.alto) == (20, 15) and editor.mapa.objetos == {}


def test_exportar_e_importar_desde_los_dialogos(editor, tmp_path):
    editor.mapa.pintar(5, 5, "Exit")
    tecla(editor, pygame.K_s, pygame.KMOD_META)
    assert editor.dialogo == "exportar" and editor.textoFichero == "Level_0.json"
    for _ in range(len("Level_0.json")):
        tecla(editor, pygame.K_BACKSPACE)
    escribir(editor, "Mio")
    editor.dibujar()
    tecla(editor, pygame.K_RETURN)
    assert editor.dialogo is None and (tmp_path / "Mio.json").exists() and not editor.cambios
    assert LevelParser(str(tmp_path)).load_by_name("Mio.json").objetos() == {"Exit": [(5, 5)]}

    editor.mapa = Mapa(10, 10)
    clic(editor, editor.botones["importar"].center)
    assert editor.dialogo == "importar"
    editor.dibujar()
    fichero, fila = editor.filasLista()[0]
    clic(editor, fila.center)
    assert fichero == "Mio.json" and editor.mapa.objetos == {(5, 5): "Exit"} and editor.dialogo is None
    assert editor.ruta == str(tmp_path / "Mio.json")


def test_exportar_pide_confirmacion_para_sobrescribir_otro(editor, tmp_path):
    (tmp_path / "Level_1.json").write_text("viejo", encoding="utf-8")
    editor.abrirDialogo("exportar")
    editor.textoFichero = "Level_1"
    editor.confirmarExportar()
    assert editor.dialogo == "sobrescribir"
    editor.dibujar()
    si, no = editor.botonesDialogo()
    clic(editor, no.center)
    assert editor.dialogo == "exportar" and (tmp_path / "Level_1.json").read_text(encoding="utf-8") == "viejo"
    editor.confirmarExportar()
    clic(editor, si.center)
    assert json.loads((tmp_path / "Level_1.json").read_text(encoding="utf-8"))["width"] == 32
    # El fichero ya es el suyo: volver a exportar no pregunta.
    editor.abrirDialogo("exportar")
    editor.confirmarExportar()
    assert editor.dialogo is None


def test_importar_fichero_roto_avisa(editor, tmp_path):
    (tmp_path / "roto.json").write_text("{ no", encoding="utf-8")
    assert editor.importar(str(tmp_path / "roto.json")) is False
    assert "No se puede importar roto.json" in editor.mensaje and editor.mapa.ancho == 32


def test_arrastrar_un_json_a_la_ventana(editor, tmp_path):
    ruta = tmp_path / "otro.json"
    ruta.write_text(json.dumps(json_nivel(12, 9)), encoding="utf-8")
    editor.manejar(pygame.event.Event(pygame.DROPFILE, file=str(ruta)))
    assert (editor.mapa.ancho, editor.mapa.alto) == (12, 9) and [c.texto for c in editor.campos] == ["12", "9"]


def test_importa_level_3_aunque_la_cabecera_no_cuadre(editor):
    assert editor.importar(os.path.join(NIVELES, "Level_3.json")) is True
    editor.dibujar()


def test_salir_con_cambios_pregunta(editor):
    editor.manejar(pygame.event.Event(pygame.QUIT))
    assert editor.salir is True                               # sin cambios sale directamente
    editor.salir = False
    editor.mapa.pintar(3, 3, "Gold")
    editor.mapaCambiado()
    editor.manejar(pygame.event.Event(pygame.QUIT))
    assert editor.dialogo == "salir" and editor.salir is False
    editor.dibujar()
    tecla(editor, pygame.K_ESCAPE)
    assert editor.dialogo is None and editor.salir is False
    editor.manejar(pygame.event.Event(pygame.QUIT))
    tecla(editor, pygame.K_RETURN)
    assert editor.salir is True


def test_la_ventana_cambia_de_tamano(editor):
    editor.pantalla = pygame.display.set_mode((900, 700))
    editor.dibujar()
    rect = editor.rectMapa()
    assert editor.superficieMapa.get_size() == rect.size and rect.right <= 900 - mmc.MARGEN
