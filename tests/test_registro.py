# Log diario (Code/registro.py): squidcastle_YYYYMMDD.log, cambio de fichero al pasar la medianoche y
# limpieza al arrancar dejando sólo los 10 ficheros más recientes. Adaptado de BikeCompFollowUp.
import logging
import time
from datetime import date, datetime
from pathlib import Path

import pytest

import Laberinto
import registro
from registro import ManejadorLogDiario, configurar_log, limpiar_logs_antiguos, nombre_log


@pytest.fixture(autouse=True)
def raiz_limpia():
    # Deja el logger raíz como estaba: los tests no deben tocar el log real del juego.
    raiz = logging.getLogger()
    handlers, nivel = list(raiz.handlers), raiz.level
    yield
    for h in raiz.handlers:
        if h not in handlers:
            raiz.removeHandler(h)
            h.close()
    raiz.setLevel(nivel)


def registro_en(fecha_hora, mensaje="hola"):
    r = logging.LogRecord("prueba", logging.WARNING, __file__, 1, mensaje, None, None)
    r.created = time.mktime(fecha_hora.timetuple())
    r.msecs = 0
    return r


@pytest.mark.parametrize("dia, nombre", [
    (date(2026, 11, 9), "squidcastle_20261109.log"), (date(2026, 1, 5), "squidcastle_20260105.log"),
    (date(2027, 12, 31), "squidcastle_20271231.log"),
])
def test_nombre_del_fichero(dia, nombre):
    assert nombre_log(dia) == nombre


def test_configurar_escribe_en_el_fichero_de_hoy(tmp_path):
    manejador = configurar_log(tmp_path / "log")
    logging.getLogger("Laberinto").warning("Inicio LaberintoPy!!!")
    manejador.flush()
    hoy = tmp_path / "log" / nombre_log(date.today())
    assert manejador.baseFilename == str(hoy)
    contenido = hoy.read_text(encoding="utf-8")
    assert "WARNING" in contenido and "Inicio LaberintoPy!!!" in contenido
    assert [f.name for f in (tmp_path / "log").iterdir()] == [hoy.name]


def test_formato_de_las_lineas(tmp_path):
    manejador = configurar_log(tmp_path)
    logging.getLogger("x").warning("cuidado %s", "ñandú")
    manejador.flush()
    linea = (tmp_path / nombre_log(date.today())).read_text(encoding="utf-8").strip()
    fecha, hora, nivel, modulo, guion, funcion, *mensaje = linea.split(" ")
    datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M:%S.%f")
    assert (nivel, modulo, guion, funcion) == ("WARNING", "test_registro", "-", "test_formato_de_las_lineas:")
    assert " ".join(mensaje) == "cuidado ñandú"


def test_al_pasar_la_medianoche_cambia_de_fichero(tmp_path):
    manejador = ManejadorLogDiario(tmp_path)
    manejador.setFormatter(logging.Formatter("%(message)s"))
    manejador.dia = date(2026, 11, 9)
    manejador.baseFilename = str(manejador.ruta(manejador.dia))
    manejador.handle(registro_en(datetime(2026, 11, 9, 23, 59, 59), "antes"))
    manejador.handle(registro_en(datetime(2026, 11, 10, 0, 0, 1), "después"))
    manejador.handle(registro_en(datetime(2026, 11, 10, 8, 0, 0), "mañana"))
    manejador.close()
    assert (tmp_path / "squidcastle_20261109.log").read_text(encoding="utf-8") == "antes\n"
    assert (tmp_path / "squidcastle_20261110.log").read_text(encoding="utf-8") == "después\nmañana\n"
    assert manejador.dia == date(2026, 11, 10)


def test_mismo_dia_se_anade_al_mismo_fichero(tmp_path):
    for texto in ("primera partida", "segunda partida"):     # dos arranques del juego el mismo día
        manejador = configurar_log(tmp_path)
        logging.getLogger("x").warning(texto)
        manejador.flush()
    lineas = (tmp_path / nombre_log(date.today())).read_text(encoding="utf-8").splitlines()
    assert [l.split(": ", 1)[1] for l in lineas] == ["primera partida", "segunda partida"]


def test_configurar_dos_veces_no_duplica_mensajes(tmp_path):
    configurar_log(tmp_path)
    manejador = configurar_log(tmp_path)
    assert [h for h in logging.getLogger().handlers if isinstance(h, ManejadorLogDiario)] == [manejador]
    logging.getLogger("x").warning("una vez")
    manejador.flush()
    assert (tmp_path / nombre_log(date.today())).read_text(encoding="utf-8").count("una vez") == 1


def test_crea_la_carpeta_y_no_crea_fichero_hasta_el_primer_mensaje(tmp_path):
    carpeta = tmp_path / "no" / "existe"
    configurar_log(carpeta)
    assert carpeta.is_dir() and list(carpeta.iterdir()) == []


def test_nivel_warning_por_defecto(tmp_path):
    # Como hasta ahora: el juego sólo guarda avisos y errores (info y debug irían a cada fotograma).
    manejador = configurar_log(tmp_path)
    assert logging.getLogger().level == logging.WARNING
    logging.getLogger("x").info("no se guarda")
    manejador.flush()
    assert not (tmp_path / nombre_log(date.today())).exists()


# ---- Al arrancar se conservan sólo los 10 ficheros más recientes ----

def crear(carpeta, *nombres):
    for nombre in nombres:
        (carpeta / nombre).write_text("x", encoding="utf-8")


def dias_jugados(*fechas):
    return [nombre_log(f) for f in fechas]


def test_por_defecto_conserva_10_ficheros():
    assert registro.MAX_FICHEROS_LOG == 10


def test_conserva_los_10_mas_recientes_aunque_sean_antiguos(tmp_path):
    # 12 días de juego repartidos en dos años: se borran los 2 más antiguos, no los de hace más de 10 días.
    fechas = [date(2025, 3, 1), date(2025, 7, 15), date(2025, 12, 31), date(2026, 1, 2), date(2026, 2, 20),
              date(2026, 4, 4), date(2026, 6, 1), date(2026, 8, 8), date(2026, 9, 9), date(2026, 10, 1),
              date(2026, 10, 30), date(2026, 11, 9)]
    crear(tmp_path, *dias_jugados(*fechas))
    assert limpiar_logs_antiguos(tmp_path) == ["squidcastle_20250301.log", "squidcastle_20250715.log"]
    assert sorted(f.name for f in tmp_path.iterdir()) == sorted(dias_jugados(*fechas[2:]))


def test_con_10_o_menos_no_borra_nada(tmp_path):
    crear(tmp_path, *dias_jugados(*[date(2020, 1, d) for d in range(1, 11)]))
    assert limpiar_logs_antiguos(tmp_path) == []
    assert len(list(tmp_path.iterdir())) == 10


def test_ordena_por_la_fecha_del_nombre(tmp_path):
    # La fecha del nombre manda, no el orden en que se crearon los ficheros.
    crear(tmp_path, "squidcastle_20261109.log", "squidcastle_20190101.log", "squidcastle_20230515.log")
    assert limpiar_logs_antiguos(tmp_path, maximo=1) == ["squidcastle_20190101.log", "squidcastle_20230515.log"]
    assert [f.name for f in tmp_path.iterdir()] == ["squidcastle_20261109.log"]


def test_no_toca_otros_ficheros(tmp_path):
    crear(tmp_path, "squidcastle.log",               # el log único de antes
                    ".DS_Store", "squidcastle_2026.log", "squidcastle_20261340.log", "otro_20200101.log",
                    "squidcastle_20200101.log.bak", "squidcastle_20200101.txt")
    assert limpiar_logs_antiguos(tmp_path, maximo=0) == []
    assert len(list(tmp_path.iterdir())) == 7


def test_otro_maximo(tmp_path):
    crear(tmp_path, "squidcastle_20261119.log", "squidcastle_20261117.log", "squidcastle_20261001.log")
    assert limpiar_logs_antiguos(tmp_path, maximo=2) == ["squidcastle_20261001.log"]


def test_carpeta_vacia_o_inexistente(tmp_path):
    assert limpiar_logs_antiguos(tmp_path) == []
    assert limpiar_logs_antiguos(tmp_path / "no_existe") == []


def test_el_borrado_queda_en_el_log_de_hoy(tmp_path):
    manejador = configurar_log(tmp_path)
    crear(tmp_path, *dias_jugados(*[date(2020, 1, d) for d in range(1, 12)]))   # 11 antiguos
    limpiar_logs_antiguos(tmp_path)      # con el de hoy no creado aún: se borra sólo el 1 más antiguo
    manejador.flush()
    assert "Borrados 1 logs antiguos (se conservan los 10 últimos): squidcastle_20200101.log" in (
        tmp_path / nombre_log(date.today())).read_text(encoding="utf-8")


def test_si_no_se_puede_borrar_sigue_con_los_demas(tmp_path, monkeypatch):
    crear(tmp_path, "squidcastle_20200101.log", "squidcastle_20200102.log", "squidcastle_20261109.log")
    original = type(tmp_path).unlink

    def unlink(self, *a, **k):
        if self.name == "squidcastle_20200101.log":
            raise PermissionError("bloqueado")
        return original(self, *a, **k)
    monkeypatch.setattr(type(tmp_path), "unlink", unlink)
    assert limpiar_logs_antiguos(tmp_path, maximo=1) == ["squidcastle_20200102.log"]
    assert (tmp_path / "squidcastle_20200101.log").exists()


# ---- Uso en el juego ----

def test_el_juego_usa_el_log_diario():
    codigo = Path(Laberinto.__file__).read_text(encoding="utf-8")
    assert "registro.configurar_log(DIR_LOG)" in codigo
    assert "basicConfig" not in codigo and "squidcastle.log" not in codigo


def test_el_juego_limpia_los_logs_al_arrancar():
    codigo = Path(Laberinto.__file__).read_text(encoding="utf-8")
    arranque = codigo[codigo.index('if __name__ == "__main__":'):]
    assert arranque.index("registro.configurar_log(") < arranque.index("registro.limpiar_logs_antiguos(")


def test_carpeta_de_log_en_el_proyecto():
    assert Path(Laberinto.DIR_LOG) == Path(Laberinto.DIR_PROYECTO) / "log"
