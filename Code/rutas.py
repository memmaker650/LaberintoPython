"""
Carpeta de datos del juego (logs y base de datos), fuera del proyecto:

  macOS:   ~/Library/Application Support/com.SkullWithGasMask/OctopusMaze
  iOS:     <contenedor de la app>/Library/Application Support/com.SkullWithGasMask/OctopusMaze
           (en iOS ~ es la carpeta privada de la app, así que la ruta relativa es la misma)
  Windows: %APPDATA%\\com.SkullWithGasMask\\OctopusMaze
  Linux:   ~/.local/share/com.SkullWithGasMask/OctopusMaze  (o $XDG_DATA_HOME)

Con la variable de entorno OCTOPUSMAZE_DATOS se puede usar otra carpeta (p. ej. para pruebas).

Dentro: log/ (un fichero por día, ver registro.py) y la base de datos OctoMaze.db.
"""

import logging
import os
import shutil
import sys
from pathlib import Path

ID_ORGANIZACION = "com.SkullWithGasMask"
NOMBRE_APP = "OctopusMaze"
VARIABLE_CARPETA = "OCTOPUSMAZE_DATOS"
NOMBRE_BD = "OctoMaze.db"
# Nombre que tenía antes la base de datos: si la carpeta aún la tiene, se renombra (no se pierden partidas).
NOMBRE_BD_ANTIGUO = "tutorial.db"


def carpeta_datos(sistema=None, inicio=None, entorno=None):
    """Carpeta de datos según el sistema (no la crea)."""
    sistema = sys.platform if sistema is None else sistema
    inicio = Path.home() if inicio is None else Path(inicio)
    entorno = os.environ if entorno is None else entorno

    if entorno.get(VARIABLE_CARPETA):
        return Path(entorno[VARIABLE_CARPETA])
    if sistema in ("darwin", "ios"):
        base = inicio / "Library" / "Application Support"
    elif sistema.startswith("win"):
        base = Path(entorno.get("APPDATA") or inicio / "AppData" / "Roaming")
    else:
        base = Path(entorno.get("XDG_DATA_HOME") or inicio / ".local" / "share")
    return base / ID_ORGANIZACION / NOMBRE_APP


def preparar_carpeta_datos(carpeta, bd_inicial=None):
    """Crea la carpeta de datos y, si aún no tiene base de datos, copia `bd_inicial` (la que viene con el
    proyecto) para conservar las partidas y estadísticas que hubiera. Devuelve la ruta de la base de datos."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    bd = carpeta / NOMBRE_BD
    antigua = carpeta / NOMBRE_BD_ANTIGUO
    if not bd.exists() and antigua.is_file():
        antigua.rename(bd)
        logging.warning("Base de datos renombrada de %s a %s", antigua, bd)
    if not bd.exists() and bd_inicial is not None and Path(bd_inicial).is_file():
        shutil.copy2(bd_inicial, bd)
        logging.warning("Base de datos copiada de %s a %s", bd_inicial, bd)
    return bd
