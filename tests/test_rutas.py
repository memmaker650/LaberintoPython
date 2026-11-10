# Carpeta de datos del juego (Code/rutas.py): logs y base de datos fuera del proyecto.
import sqlite3
from pathlib import Path

import pytest

import Laberinto
import rutas
from rutas import carpeta_datos, preparar_carpeta_datos

CASA = Path("/Users/jugador")
FINAL = Path("com.SkullWithGasMask") / "OctopusMaze"


def test_macos():
    assert carpeta_datos("darwin", CASA, {}) == CASA / "Library" / "Application Support" / FINAL


def test_ios_misma_ruta_dentro_del_contenedor_de_la_app():
    contenedor = Path("/var/mobile/Containers/Data/Application/1234-ABCD")
    assert carpeta_datos("ios", contenedor, {}) == contenedor / "Library" / "Application Support" / FINAL


def test_windows():
    assert carpeta_datos("win32", CASA, {"APPDATA": r"C:\Users\jugador\AppData\Roaming"}) == \
        Path(r"C:\Users\jugador\AppData\Roaming") / FINAL
    assert carpeta_datos("win32", CASA, {}) == CASA / "AppData" / "Roaming" / FINAL


def test_linux():
    assert carpeta_datos("linux", CASA, {}) == CASA / ".local" / "share" / FINAL
    assert carpeta_datos("linux", CASA, {"XDG_DATA_HOME": "/datos"}) == Path("/datos") / FINAL


def test_variable_de_entorno_manda(tmp_path):
    assert carpeta_datos("darwin", CASA, {rutas.VARIABLE_CARPETA: str(tmp_path)}) == tmp_path


def test_por_defecto_usa_el_sistema_y_la_casa_actuales(monkeypatch, tmp_path):
    monkeypatch.delenv(rutas.VARIABLE_CARPETA, raising=False)
    monkeypatch.setattr(rutas.sys, "platform", "darwin")
    monkeypatch.setattr(rutas.Path, "home", lambda: tmp_path)
    assert carpeta_datos() == tmp_path / "Library" / "Application Support" / FINAL


def test_carpeta_datos_no_crea_nada(tmp_path):
    carpeta_datos("darwin", tmp_path, {})
    assert list(tmp_path.iterdir()) == []


# ---- Primera vez: se crea la carpeta y se copia la base de datos del proyecto ----

def bd_con_partida(ruta):
    with sqlite3.connect(ruta) as conexion:
        conexion.execute("CREATE TABLE partida_guardada (jugador TEXT, estado TEXT)")
        conexion.execute("INSERT INTO partida_guardada VALUES ('Memmaker650', '{}')")
    return ruta


def test_primera_vez_copia_la_bd_del_proyecto(tmp_path):
    inicial = bd_con_partida(tmp_path / "OctoMaze.db")
    datos = tmp_path / "Application Support" / "OctopusMaze"
    bd = preparar_carpeta_datos(datos, inicial)
    assert bd == datos / "OctoMaze.db" and datos.is_dir()
    with sqlite3.connect(bd) as conexion:
        assert conexion.execute("SELECT jugador FROM partida_guardada").fetchall() == [("Memmaker650",)]


def test_no_sobrescribe_una_bd_que_ya_existe(tmp_path):
    inicial = bd_con_partida(tmp_path / "inicial.db")
    datos = tmp_path / "datos"
    datos.mkdir()
    (datos / "OctoMaze.db").write_bytes(b"la del jugador")
    preparar_carpeta_datos(datos, inicial)
    assert (datos / "OctoMaze.db").read_bytes() == b"la del jugador"


def test_nombre_de_la_bd():
    assert rutas.NOMBRE_BD == "OctoMaze.db"


def test_renombra_la_tutorial_db_que_ya_estaba(tmp_path):
    # Quien ya jugó con el nombre antiguo conserva su partida: tutorial.db pasa a OctoMaze.db sin copiar la inicial.
    datos = tmp_path / "datos"
    bd_con_partida(datos.mkdir() or datos / "tutorial.db")
    inicial = tmp_path / "inicial.db"
    inicial.write_bytes(b"la del proyecto")
    bd = preparar_carpeta_datos(datos, inicial)
    assert bd == datos / "OctoMaze.db" and not (datos / "tutorial.db").exists()
    with sqlite3.connect(bd) as conexion:
        assert conexion.execute("SELECT jugador FROM partida_guardada").fetchall() == [("Memmaker650",)]


def test_si_ya_hay_octomaze_no_toca_la_antigua(tmp_path):
    datos = tmp_path / "datos"
    datos.mkdir()
    (datos / "OctoMaze.db").write_bytes(b"nueva")
    (datos / "tutorial.db").write_bytes(b"antigua")
    preparar_carpeta_datos(datos)
    assert (datos / "OctoMaze.db").read_bytes() == b"nueva" and (datos / "tutorial.db").exists()


def test_sin_bd_inicial_solo_crea_la_carpeta(tmp_path):
    bd = preparar_carpeta_datos(tmp_path / "datos", tmp_path / "no_existe.db")
    assert (tmp_path / "datos").is_dir() and not bd.exists()


# ---- Uso en el juego ----

def test_el_juego_guarda_log_y_bd_en_la_carpeta_de_datos():
    assert Path(Laberinto.DIR_LOG) == Path(Laberinto.DIR_DATOS) / "log"
    assert Path(Laberinto.RUTA_BD_INICIAL) == Path(Laberinto.DIR_PROYECTO) / "DB" / "OctoMaze.db"
    assert Path(Laberinto.RUTA_BD_INICIAL).is_file()
    assert Path(Laberinto.DIR_DATOS) == carpeta_datos()


def test_ruta_bd_real_en_la_carpeta_de_datos(monkeypatch):
    # conftest cambia RUTA_BD por una de prueba: se comprueba el valor escrito en el código.
    codigo = Path(Laberinto.__file__).read_text(encoding="utf-8")
    assert "RUTA_BD = os.path.join(DIR_DATOS, rutas.NOMBRE_BD)" in codigo
    assert '"./DB/tutorial.db"' not in codigo


def test_al_arrancar_prepara_la_carpeta_y_abre_esa_bd():
    codigo = Path(Laberinto.__file__).read_text(encoding="utf-8")
    arranque = codigo[codigo.index('if __name__ == "__main__":'):]
    assert "rutas.preparar_carpeta_datos(DIR_DATOS, RUTA_BD_INICIAL)" in arranque
    assert arranque.index("rutas.preparar_carpeta_datos(") < arranque.index("sqlite3.connect(RUTA_BD)")
