"""
Fichero de log del juego: uno por día, con el nombre squidcastle_YYYYMMDD.log, en la carpeta log/.

Cada mensaje va al fichero del día en que se registra. Si el juego sigue abierto al pasar la medianoche, el
siguiente mensaje ya se escribe en el fichero del nuevo día (no hace falta reiniciarlo).

Al arrancar se conservan sólo los MAX_FICHEROS_LOG ficheros más recientes (por la fecha de su nombre), aunque
no sean de los últimos días: si se juega de vez en cuando, siguen ahí los logs de las últimas partidas.

Adaptado de registro.py de BikeCompFollowUp (allí se conservan los logs de los últimos 10 días).
"""

import logging
import os
import re
from datetime import date, datetime
from pathlib import Path

PREFIJO_LOG = "squidcastle"
FORMATO_LOG = "%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s"
FORMATO_FECHA_LOG = "%Y-%m-%d %H:%M:%S"
MAX_FICHEROS_LOG = 10       # al arrancar se borran los más antiguos y quedan los 10 últimos


def nombre_log(dia, prefijo=PREFIJO_LOG):
    """date(2026, 11, 9) -> 'squidcastle_20261109.log'"""
    return f"{prefijo}_{dia:%Y%m%d}.log"


class ManejadorLogDiario(logging.FileHandler):
    """FileHandler que escribe cada mensaje en <carpeta>/<prefijo>_YYYYMMDD.log según el día del mensaje."""

    def __init__(self, carpeta, prefijo=PREFIJO_LOG, encoding="utf-8"):
        self.carpeta = Path(carpeta)
        self.prefijo = prefijo
        self.dia = date.today()
        self.carpeta.mkdir(parents=True, exist_ok=True)
        # delay=True: el fichero se crea con el primer mensaje, no al configurar el log
        super().__init__(self.ruta(self.dia), encoding=encoding, delay=True)

    def ruta(self, dia):
        return self.carpeta / nombre_log(dia, self.prefijo)

    def emit(self, record):
        dia = date.fromtimestamp(record.created)
        if dia != self.dia:            # ha cambiado el día: se cierra el fichero anterior y se pasa al nuevo
            if self.stream is not None:
                self.stream.close()
                self.stream = None
            self.dia = dia
            self.baseFilename = os.path.abspath(self.ruta(dia))
        super().emit(record)


def configurar_log(carpeta, nivel=logging.WARNING):
    """Envía el log de todo el juego a ficheros diarios en `carpeta`. Si ya estaba configurado, lo sustituye
    (no se duplican los mensajes). Devuelve el manejador; su `baseFilename` es el fichero de hoy."""
    raiz = logging.getLogger()
    for anterior in [h for h in raiz.handlers if isinstance(h, ManejadorLogDiario)]:
        raiz.removeHandler(anterior)
        anterior.close()
    manejador = ManejadorLogDiario(carpeta)
    manejador.setFormatter(logging.Formatter(FORMATO_LOG, datefmt=FORMATO_FECHA_LOG))
    raiz.addHandler(manejador)
    raiz.setLevel(nivel)
    return manejador


def limpiar_logs_antiguos(carpeta, maximo=MAX_FICHEROS_LOG, prefijo=PREFIJO_LOG):
    """Deja en `carpeta` sólo los `maximo` ficheros <prefijo>_YYYYMMDD.log más recientes (según la fecha de
    su nombre) y borra el resto, sin importar cuántos días hayan pasado. No toca ningún otro fichero.
    Devuelve los nombres borrados, del más antiguo al más reciente."""
    patron = re.compile(rf"^{re.escape(prefijo)}_(\d{{8}})\.log$")
    logs = []
    for fichero in Path(carpeta).glob(f"{prefijo}_*.log"):
        encontrado = patron.match(fichero.name)
        if not encontrado:
            continue
        try:
            dia = datetime.strptime(encontrado.group(1), "%Y%m%d").date()
        except ValueError:         # p. ej. squidcastle_20261340.log: no es una fecha, no se toca
            continue
        logs.append((dia, fichero))
    logs.sort()
    sobrantes = logs[:-maximo] if maximo > 0 else logs
    borrados = []
    for _, fichero in sobrantes:
        try:
            fichero.unlink()
            borrados.append(fichero.name)
        except OSError as error:
            logging.warning("No se pudo borrar el log antiguo %s: %s", fichero.name, error)
    if borrados:
        logging.warning("Borrados %d logs antiguos (se conservan los %d últimos): %s",
                        len(borrados), maximo, ", ".join(borrados))
    return borrados
