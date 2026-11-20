# Editor de niveles MazeMapCreator: modelo (mapa.py) e interfaz (mazeMapCreator.py).
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
import mazeMapCreator as mmc  # noqa: E402
from levels_parser import LevelParser  # noqa: E402
from mapa import BORRAR, ENEMIGO, INICIO, PARED, SUELO, Mapa  # noqa: E402

NIVELES = os.path.join(RAIZ, "Levels")


def json_nivel(ancho, alto, fondo=None, objetos=None, inicio=(1, 1), nombres=None, **extra):
    nombres = nombres or ["Floor", "Wall", "Exit", "Gold", "DogDown1", "Door"]
    fondo = fondo or [[2 if x in (0, ancho - 1) or y in (0, alto - 1) else 1 for x in range(ancho)]
                      for y in range(alto)]
    objetos = objetos or [fila[:] for fila in fondo]          # Objects repite el fondo
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
    assert m.fondo[11] == [PARED] * 6               # borde nuevo: pared
    assert m.fondo[10] == [PARED] + [SUELO] * 4 + [PARED]   # el resto de casillas nuevas: suelo


def test_agrandar_pone_suelo_y_cierra_el_borde_nuevo():
    m = Mapa(10, 10)
    m.redimensionar(15, 13)
    assert all(m.fondo[y][x] == SUELO for y in range(10, 12) for x in range(1, 14))
    assert all(m.fondo[y][x] == SUELO for y in range(1, 12) for x in range(10, 14))
    assert m.fondo[12] == [PARED] * 15 and all(f[14] == PARED for f in m.fondo)
    assert all(m.fondo[y][9] == PARED for y in range(10)) and m.fondo[9][5] == PARED   # lo antiguo, igual


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
    assert avisos == ["Las dimensiones del fichero no cuadran con sus casillas: se usa 48x32"]
    assert modelo.erroresDimensiones(datos) == ["width es 27 pero las casillas tienen 48 columnas",
                                                "height es 27 pero las casillas tienen 32 filas"]


def test_importar_convierte_los_ids_por_nombre():
    # Los niveles antiguos tienen otros tileNames: se traducen por nombre a los ids de Level_0.
    datos = json_nivel(6, 5, inicio=(2, 1))
    objetos = datos["layers"][1]["tiles"]
    objetos[1][1], objetos[2][3], objetos[3][4] = 3, 4, 6     # Exit, Gold, Door
    m, avisos = Mapa.desdeJson(datos)
    assert avisos == [] and m.inicio == (2, 1)
    assert m.objetos == {(1, 1): "Exit", (3, 2): "Gold", (4, 3): "Door"}
    datos = m.aJson()
    assert datos["tileNames"] == modelo.TILE_NAMES
    ids = {n: i + 1 for i, n in enumerate(modelo.TILE_NAMES)}
    assert datos["layers"][1]["tiles"][1][1] == ids["Exit"] and datos["layers"][1]["tiles"][3][4] == ids["Door"]


def test_exportar_objects_repite_el_fondo():
    m = Mapa(6, 5)
    m.pintar(2, 2, "Gold")
    fondo, objetos = (c["tiles"] for c in m.aJson()["layers"])
    ids = {n: i + 1 for i, n in enumerate(modelo.TILE_NAMES)}
    assert objetos[2][2] == ids["Gold"]
    assert all(objetos[y][x] == fondo[y][x] for y in range(5) for x in range(6) if (x, y) != (2, 2))
    assert 0 not in sum(objetos, [])


def test_importar_formato_antiguo_con_ceros():
    datos = json_nivel(6, 5)
    datos["layers"][1]["tiles"] = [[0] * 6 for _ in range(5)]
    datos["layers"][1]["tiles"][2][2] = 4                       # Gold
    m, avisos = Mapa.desdeJson(datos)
    assert m.objetos == {(2, 2): "Gold"}
    assert avisos == ["La capa Objects tiene 29 casilla(s) vacías (formato antiguo): al exportar se rellenan "
                      "con Floor y Wall"]
    assert m.problemas() == ["El nivel no tiene salida ('Exit')"]      # lo exportado ya no tiene ceros


def test_importar_objects_que_no_coincide_con_el_fondo():
    datos = json_nivel(6, 5)
    datos["layers"][1]["tiles"][2][2] = 2                       # Objects dice Wall; el fondo, Floor
    datos["layers"][1]["tiles"][0][0] = 1                       # Objects dice Floor; el fondo, Wall
    m, avisos = Mapa.desdeJson(datos)
    assert avisos == ["La capa Objects no coincide con el fondo en 2 casilla(s): se usa el fondo"]
    assert m.fondo[2][2] == SUELO and m.fondo[0][0] == PARED


def test_importar_avisa_de_lo_raro():
    fondo = [[2] * 5, [2, 1, 3, 1, 2], [2, 1, 1, 1], [2] * 5, [2] * 5]
    objetos = [[0] * 5 for _ in range(5)]
    objetos[1][1] = 9                                          # id que no existe
    m, avisos = Mapa.desdeJson(json_nivel(5, 5, fondo=fondo, objetos=objetos, inicio=(9, 9)))
    assert m.fondo[1][2] == PARED and m.fondo[2][4] == PARED and m.inicio is None
    assert any("no cuadran con sus casillas" in a for a in avisos)
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
    m = Mapa(65, 30)
    assert m.problemas()[0] == "El juego admite como máximo 64x64 casillas; este mapa mide 65x30"
    m.redimensionar(64, 64)
    assert not any("como máximo" in p for p in m.problemas())
    assert not any("como máximo" in p for p in Mapa().problemas())    # 32x32 ya cabe (scroll vertical)


def test_maximo_igual_que_el_del_juego():
    import MazeLab
    assert (modelo.MAX_ANCHO_JUEGO, modelo.MAX_ALTO_JUEGO) == (MazeLab.MAX_CASILLAS_H, MazeLab.MAX_CASILLAS_VERTI)


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


# ---------- Errores de dimensiones: mandan las casillas y se ofrece corregir el fichero ----------

def nivel_mal(carpeta, nombre="Mal.json"):
    # Cabecera 27x27, casillas 30x20; la fila 3 del fondo y la 5 de objetos más cortas; a Objects le
    # faltan 2 filas. Lleva claves propias (oscuridad, autor) que deben quedar igual.
    datos = json_nivel(30, 20, inicio=(2, 2), oscuridad=0.5)
    datos["width"] = datos["height"] = 27
    datos["autor"] = "Jorge"
    fondo, objetos = datos["layers"][0]["tiles"], datos["layers"][1]["tiles"]
    fondo[3] = fondo[3][:25]
    objetos[1][1] = 3                       # Exit (id 3 en estos tileNames)
    objetos[5] = objetos[5][:10]
    del objetos[18:]
    ruta = carpeta / nombre
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    return ruta, datos


def test_errores_de_dimensiones(tmp_path):
    _, datos = nivel_mal(tmp_path)
    assert modelo.dimensionesReales(datos) == (30, 20)
    assert modelo.erroresDimensiones(datos) == [
        "width es 27 pero las casillas tienen 30 columnas",
        "height es 27 pero las casillas tienen 20 filas",
        "La capa Background tiene 1 fila(s) con menos de 30 columnas (la primera, la 3)",
        "La capa Objects tiene 18 filas de 20",
        "La capa Objects tiene 1 fila(s) con menos de 30 columnas (la primera, la 5)",
    ]


@pytest.mark.parametrize("fichero", [f for f in sorted(os.listdir(NIVELES)) if f.endswith(".json") and f != "Level_3.json"])
def test_los_niveles_del_juego_no_tienen_errores_de_dimensiones(fichero):
    with open(os.path.join(NIVELES, fichero), encoding="utf-8") as f:
        assert modelo.erroresDimensiones(json.load(f)) == []


def test_corregir_cambia_solo_lo_que_esta_mal(tmp_path):
    _, datos = nivel_mal(tmp_path)
    corregido = modelo.corregirDimensiones(datos)
    assert modelo.erroresDimensiones(corregido) == []
    assert (corregido["width"], corregido["height"]) == (30, 20)
    fondo, objetos = corregido["layers"][0]["tiles"], corregido["layers"][1]["tiles"]
    assert fondo[3] == datos["layers"][0]["tiles"][3] + [2] * 5          # pared (id de Wall)
    assert objetos[5] == datos["layers"][1]["tiles"][5] + fondo[5][10:]  # Objects repite el fondo
    assert objetos[18:] == fondo[18:]
    # Lo demás, igual (y en el mismo orden): tileNames, inicio, oscuridad, claves propias, filas bien.
    assert list(corregido) == list(datos)
    for clave in ("tileNames", "playerSpawnX", "playerSpawnY", "oscuridad", "autor", "tileWidth"):
        assert corregido[clave] == datos[clave]
    assert fondo[:3] == datos["layers"][0]["tiles"][:3]
    assert datos["width"] == 27 and len(datos["layers"][1]["tiles"]) == 18   # el original no se toca


def test_textoNivel_respeta_el_formato_de_los_niveles():
    for fichero in ("Level_0.json", "Level_1.json"):
        ruta = os.path.join(NIVELES, fichero)
        with open(ruta, encoding="utf-8") as f:
            texto = f.read()
        assert modelo.textoNivel(json.loads(texto)) == texto


def test_importar_con_errores_abre_el_aviso(editor, tmp_path):
    ruta, _ = nivel_mal(tmp_path)
    antes = ruta.read_text(encoding="utf-8")
    assert editor.importar(str(ruta)) is True
    assert (editor.mapa.ancho, editor.mapa.alto) == (30, 20)               # mandan las casillas
    assert editor.dialogo == "corregir" and len(editor.erroresFichero) == 5
    editor.dibujar()
    assert ruta.read_text(encoding="utf-8") == antes                       # aún no se ha tocado


def test_corregir_desde_el_aviso_reescribe_el_fichero(editor, tmp_path):
    ruta, datos = nivel_mal(tmp_path)
    editor.importar(str(ruta))
    si, _ = editor.botonesDialogo()
    clic(editor, si.center)
    assert editor.dialogo is None and editor.erroresFichero == []
    corregido = json.loads(ruta.read_text(encoding="utf-8"))
    assert corregido == modelo.corregirDimensiones(datos)
    assert corregido["tileNames"] == datos["tileNames"] and corregido["autor"] == "Jorge"
    assert "Corregido Mal.json: ahora mide 30x20" in editor.mensaje
    nivel = LevelParser(str(tmp_path)).load_by_name("Mal.json")             # el juego ya lo acepta
    assert (nivel.width, nivel.height) == (30, 20)
    # Volver a importarlo ya no pregunta.
    editor.importar(str(ruta))
    assert editor.dialogo is None


def test_no_corregir_deja_el_fichero_igual(editor, tmp_path):
    ruta, _ = nivel_mal(tmp_path)
    antes = ruta.read_text(encoding="utf-8")
    editor.importar(str(ruta))
    _, no = editor.botonesDialogo()
    clic(editor, no.center)
    assert editor.dialogo is None and ruta.read_text(encoding="utf-8") == antes and editor.cambios
    editor.importar(str(ruta))
    tecla(editor, pygame.K_ESCAPE)                                         # ESC también es "No"
    assert editor.dialogo is None and ruta.read_text(encoding="utf-8") == antes
    editor.importar(str(ruta))
    tecla(editor, pygame.K_RETURN)                                         # INTRO es "Corregir"
    assert modelo.erroresDimensiones(json.loads(ruta.read_text(encoding="utf-8"))) == []


def test_level_3_se_puede_corregir_sin_tocar_el_original(editor, tmp_path):
    copia = tmp_path / "Level_3.json"
    copia.write_text(open(os.path.join(NIVELES, "Level_3.json"), encoding="utf-8").read(), encoding="utf-8")
    original = json.loads(copia.read_text(encoding="utf-8"))
    editor.importar(str(copia))
    if editor.dialogo == "corregir":                                       # mientras siga mal definido
        editor.dibujar()
        editor.corregirFichero()
        corregido = json.loads(copia.read_text(encoding="utf-8"))
        assert (corregido["width"], corregido["height"]) == modelo.dimensionesReales(original)
        assert corregido["layers"] == original["layers"]


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


# ---------- Zoom, desplazamiento y cámara del juego ----------

def mapa_grande(editor, ancho=64, alto=64):
    editor.mapa = Mapa(ancho, alto)
    editor.mapaCambiado()
    editor.verMapaNuevo()


def rueda(editor, x=0, y=0):
    editor.manejar(pygame.event.Event(pygame.MOUSEWHEEL, x=x, y=y, flipped=False))


def test_limites_de_la_camara_como_en_el_juego():
    import MazeLab
    assert (modelo.CAMARA_ANCHO, modelo.CAMARA_ALTO) == (MazeLab.NUM_CASILLAS_CAMARA, MazeLab.FILAS_CAMARA)
    assert (modelo.REJILLA_MINIMA_H, modelo.REJILLA_MINIMA_VERTI) == (MazeLab.REJILLA_MINIMA_H,
                                                                     MazeLab.REJILLA_MINIMA_VERTI)
    assert Mapa(64, 50).limitesCamara() == (64 - 27, 50 - 27)
    assert Mapa(32, 20).limitesCamara() == (40 - 27, 0)       # la rejilla del juego mide al menos 40x27
    assert Mapa(20, 20).limitesCamara() == (0, 0)             # todo el suelo cabe: cámara fija en horizontal
    m = Mapa(64, 64)
    assert m.camaraCentradaEn(32, 32) == (19, 19)
    assert m.camaraCentradaEn(0, 0) == (0, 0) and m.camaraCentradaEn(63, 63) == (37, 37)


def test_zoom_y_desplazamiento_para_editar_todo_el_mapa(editor):
    mapa_grande(editor)
    assert editor.zoom is None and editor.rectMapa().size == (64 * 10, 64 * 10)   # entero en la ventana
    for _ in range(10):
        tecla(editor, pygame.K_PLUS)
    c = editor.tamanoCasilla()
    assert c > 20 and editor.rectMapa().height > editor.zonaMapa().height
    editor.dibujar()
    assert editor.superficieMapa.get_size() == editor.zonaMapa().size              # sólo la parte visible
    # La esquina de abajo a la derecha no se ve hasta desplazarse; luego se puede pintar.
    for _ in range(100):
        rueda(editor, y=-1)
        tecla(editor, pygame.K_RIGHT)
    rect, zona = editor.rectMapa(), editor.zonaMapa()
    assert rect.bottomright == zona.bottomright
    elegir(editor, "Gold")
    clic(editor, centro_casilla(editor, 62, 62))
    assert editor.mapa.objetos[(62, 62)] == "Gold"
    editor.dibujar()
    assert editor.casillaEn((zona.x + 1, zona.y + 1)) != (0, 0)
    for _ in range(100):
        rueda(editor, y=1)
        rueda(editor, x=-1)
    assert editor.rectMapa().topleft == zona.topleft
    tecla(editor, pygame.K_0)
    assert editor.zoom is None


def test_arrastrar_con_el_boton_central(editor):
    mapa_grande(editor)
    for _ in range(6):
        tecla(editor, pygame.K_PLUS)
    zona = editor.zonaMapa()
    editor.vista = [0, 0]
    editor.manejar(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=zona.center, button=2))
    editor.manejar(pygame.event.Event(pygame.MOUSEMOTION, pos=zona.topleft, rel=(-100, -80), buttons=(0, 1, 0)))
    editor.manejar(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=zona.topleft, button=2))
    assert editor.vista == [100, 80] and not editor.mapa.objetos


def test_el_zoom_no_baja_de_ver_el_mapa_entero(editor):
    tamano = editor.tamanoCasilla()
    tecla(editor, pygame.K_MINUS)
    assert editor.zoom is None and editor.tamanoCasilla() == tamano
    editor.calcularBotones()
    clic(editor, editor.botones["zoomMas"].center)
    assert editor.tamanoCasilla() > tamano
    clic(editor, editor.botones["zoomMenos"].center)
    assert editor.zoom is None


@pytest.fixture
def mayusculas(monkeypatch):
    # Simula tener pulsada (o no) la tecla Mayúsculas mientras se hace clic.
    pulsada = {"si": False}
    monkeypatch.setattr(pygame.key, "get_mods", lambda: pygame.KMOD_SHIFT if pulsada["si"] else 0)
    return pulsada


def test_camara_centrada_donde_diga_el_usuario(editor, mayusculas):
    mapa_grande(editor)
    editor.mapa.pintar(40, 40, SUELO)
    editor.calcularBotones()
    clic(editor, editor.botones["camara"].center)
    assert editor.verCamara and editor.camara == (0, 0)          # empieza donde el jugador
    assert editor.zoom is None                                    # se sigue viendo el nivel entero
    estado = editor.mapa.estado()
    mayusculas["si"] = True
    clic(editor, centro_casilla(editor, 40, 40))
    assert editor.camara == (27, 27) and editor.mapa.estado() == estado     # mover la cámara no pinta
    # Arrastrar con Mayúsculas la lleva con el ratón y las flechas la mueven (sin salir del mundo).
    editor.manejar(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=centro_casilla(editor, 20, 20), button=1))
    editor.manejar(pygame.event.Event(pygame.MOUSEMOTION, pos=centro_casilla(editor, 30, 25), rel=(0, 0), buttons=(1, 0, 0)))
    editor.manejar(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=centro_casilla(editor, 30, 25), button=1))
    assert editor.camara == (17, 12) and editor.mapa.estado() == estado
    tecla(editor, pygame.K_RIGHT)
    tecla(editor, pygame.K_DOWN, pygame.KMOD_SHIFT)
    assert editor.camara == (18, 17)
    for _ in range(30):
        tecla(editor, pygame.K_RIGHT, pygame.KMOD_SHIFT)
    assert editor.camara == (37, 17)
    # Sin Mayúsculas se pinta como siempre, también fuera de la cámara.
    mayusculas["si"] = False
    elegir(editor, "Gold")
    clic(editor, centro_casilla(editor, 5, 5))
    assert editor.mapa.objetos[(5, 5)] == "Gold" and editor.verCamara and editor.camara == (37, 17)
    tecla(editor, pygame.K_c)
    assert not editor.verCamara


def test_la_camara_no_oscurece_el_resto_del_nivel(editor):
    mapa_grande(editor)
    editor.dibujar()
    rect, c = editor.rectMapa(), editor.tamanoCasilla()
    fuera = (rect.right - c // 2, rect.bottom - c // 2)          # casilla lejos de la cámara
    antes = editor.pantalla.get_at(fuera)
    tecla(editor, pygame.K_c)
    editor.dibujar()
    assert editor.pantalla.get_at(fuera) == antes
    camara = editor.rectCamara()
    assert camara.size == (27 * c, 27 * c)
    assert editor.pantalla.get_at((camara.x + 1, camara.centery))[:3] == mmc.COLOR_CAMARA   # sólo el borde


def test_la_camara_sigue_valida_al_achicar_el_mapa(editor, mayusculas):
    mapa_grande(editor)
    tecla(editor, pygame.K_c)
    mayusculas["si"] = True
    clic(editor, centro_casilla(editor, 60, 60))
    assert editor.camara == (37, 37)
    editor.mapa.redimensionar(50, 30)
    editor.mapaCambiado()
    assert editor.camara == (23, 3)
    editor.dibujar()


def test_importar_vuelve_a_ver_el_mapa_entero(editor, tmp_path):
    mapa_grande(editor)
    tecla(editor, pygame.K_PLUS)
    rueda(editor, y=-5)
    ruta = tmp_path / "Level_7.json"
    ruta.write_text(json.dumps(json_nivel(50, 50)), encoding="utf-8")
    editor.importar(str(ruta))
    assert editor.zoom is None and editor.vista == [0, 0]


# ---------- Puertas de 2 o 3 casillas ----------

def test_puertas_seguidas_son_una_sola():
    m = Mapa(12, 12)
    for p in ((2, 5), (3, 5), (8, 2), (8, 3), (8, 4), (5, 9)):
        m.pintar(*p, "Door")
    assert sorted(m.puertas()) == [[(2, 5), (3, 5)], [(5, 9)], [(8, 2), (8, 3), (8, 4)]]
    assert m.puertaEn(3, 5) == [(2, 5), (3, 5)] and m.puertaEn(5, 9) == [(5, 9)] and m.puertaEn(1, 1) is None
    assert not [p for p in m.problemas() if "puerta" in p.lower()]


def test_puerta_de_mas_de_3_es_un_problema():
    m = Mapa(12, 12)
    for x in range(2, 6):
        m.pintar(x, 5, "Door")
    assert any("de más de 3 casillas" in p for p in m.problemas())
    assert m.puertas() == [[(2, 5), (3, 5), (4, 5)], [(5, 5)]]


def test_el_editor_dibuja_la_puerta_ancha_como_una(editor):
    elegir(editor, "Door")
    for x in (4, 5, 6):
        clic(editor, centro_casilla(editor, x, 8))
    editor.dibujar()
    rect, c = editor.rectMapa(), editor.tamanoCasilla()
    # El marco rodea las 3 casillas: el borde de arriba es del mismo color en las tres.
    for x in (4, 5, 6):
        assert editor.pantalla.get_at((rect.x + x * c + c // 2, rect.y + 8 * c))[:3] == mmc.COLOR_PUERTA_ANCHA
    editor.manejar(pygame.event.Event(pygame.MOUSEMOTION, pos=centro_casilla(editor, 5, 8), rel=(0, 0), buttons=(0, 0, 0)))
    assert editor.mapa.puertaEn(5, 8) == [(4, 8), (5, 8), (6, 8)]


def test_exportar_e_importar_mantiene_la_puerta_ancha(tmp_path):
    m = Mapa(12, 12)
    m.pintar(4, 4, "Door")
    m.pintar(5, 4, "Door")
    m.pintar(9, 9, "Exit")
    ruta = tmp_path / "Level_8.json"
    m.exportar(str(ruta))
    datos = LevelParser(str(tmp_path)).load_by_name("Level_8.json")
    assert datos.puertas() == [[(4, 4), (5, 4)]]
    assert Mapa.importar(str(ruta))[0].puertas() == [[(4, 4), (5, 4)]]


# ---------- Jefe enemigo ----------

def test_el_jefe_es_unico_y_se_exporta(tmp_path):
    m = Mapa(12, 12)
    m.pintar(3, 3, modelo.JEFE)
    m.pintar(8, 8, modelo.JEFE)                      # se mueve: sólo hay uno
    assert [p for p, n in m.objetos.items() if n == modelo.JEFE] == [(8, 8)]
    m.pintar(5, 5, ENEMIGO)
    m.pintar(10, 10, "Exit")
    ruta = tmp_path / "Level_8.json"
    m.exportar(str(ruta))
    datos = LevelParser(str(tmp_path)).load_by_name("Level_8.json")
    assert datos.objetos()[modelo.JEFE] == [(8, 8)] and datos.analizar() == []
    importado, avisos = Mapa.importar(str(ruta))
    assert importado.objetos[(8, 8)] == modelo.JEFE and not avisos


def test_jefe_en_la_paleta(editor):
    elegir(editor, modelo.JEFE)
    clic(editor, centro_casilla(editor, 6, 6))
    clic(editor, centro_casilla(editor, 9, 4))
    assert editor.mapa.objetos.get((9, 4)) == modelo.JEFE and (6, 6) not in editor.mapa.objetos
    assert editor.iconos.get("wilber-eeek.png") is not None
