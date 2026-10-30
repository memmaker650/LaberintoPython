import datetime
import json
import logging
import sqlite3
from contextlib import closing

# partida.py
# Partida guardada en la base de datos para poder continuarla desde el menú principal.
# Se guarda una sola partida por jugador (cada guardado sustituye al anterior). El estado
# completo (nivel, jugador, enemigos, objetos cogidos, estadísticas...) va en JSON en la
# columna 'estado'; el resto de columnas son un resumen para consultarla fácilmente.

TABLA = "partida_guardada"

SQL_CREAR_TABLA = f"""
CREATE TABLE IF NOT EXISTS {TABLA} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    jugador TEXT NOT NULL UNIQUE,
    nivel INTEGER NOT NULL,
    puntos INTEGER NOT NULL,
    vida INTEGER NOT NULL,
    tiempo_segundos REAL NOT NULL,
    motivo TEXT NOT NULL,
    estado TEXT NOT NULL
)
"""


class PartidaGuardada:
    @staticmethod
    def crearTabla(conexion):
        conexion.execute(SQL_CREAR_TABLA)

    # Guarda (o sustituye) la partida del jugador. 'estado' es un diccionario serializable a JSON.
    # 'motivo' indica por qué se ha guardado (salir, cerrar, segundo plano...). Devuelve el id.
    @staticmethod
    def guardar(ruta_bd, jugador, estado, motivo="salir"):
        fila = (
            datetime.datetime.now().isoformat(timespec="seconds"),
            jugador,
            int(estado.get("nivel", 0)),
            int(estado.get("puntos", 0)),
            int(estado.get("vida", 0)),
            round(estado.get("tiempo_ms", 0) / 1000.0, 2),
            motivo,
            json.dumps(estado, ensure_ascii=False),
        )
        with closing(sqlite3.connect(ruta_bd)) as conexion, conexion:
            PartidaGuardada.crearTabla(conexion)
            conexion.execute(f"DELETE FROM {TABLA} WHERE jugador = ?", (jugador,))
            cursor = conexion.execute(
                f"INSERT INTO {TABLA} (fecha, jugador, nivel, puntos, vida, tiempo_segundos, motivo, estado) "
                f"VALUES (?, ?, ?, ?, ?, ?, ?, ?)", fila)
            identificador = cursor.lastrowid
        logging.info("Partida de %s guardada (%s) en %s", jugador, motivo, ruta_bd)
        return identificador

    # Estado guardado del jugador (diccionario) o None si no tiene ninguna partida.
    @staticmethod
    def cargar(ruta_bd, jugador):
        with closing(sqlite3.connect(ruta_bd)) as conexion:
            PartidaGuardada.crearTabla(conexion)
            fila = conexion.execute(f"SELECT estado FROM {TABLA} WHERE jugador = ?", (jugador,)).fetchone()
        return json.loads(fila[0]) if fila else None

    @staticmethod
    def existe(ruta_bd, jugador):
        return PartidaGuardada.cargar(ruta_bd, jugador) is not None

    @staticmethod
    def borrar(ruta_bd, jugador):
        with closing(sqlite3.connect(ruta_bd)) as conexion, conexion:
            PartidaGuardada.crearTabla(conexion)
            conexion.execute(f"DELETE FROM {TABLA} WHERE jugador = ?", (jugador,))
        logging.info("Partida guardada de %s borrada", jugador)

    # Resumen de la partida guardada (fecha, nivel, puntos, vida, tiempo, motivo) o None.
    @staticmethod
    def resumen(ruta_bd, jugador):
        with closing(sqlite3.connect(ruta_bd)) as conexion:
            PartidaGuardada.crearTabla(conexion)
            conexion.row_factory = sqlite3.Row
            fila = conexion.execute(
                f"SELECT fecha, nivel, puntos, vida, tiempo_segundos, motivo FROM {TABLA} WHERE jugador = ?",
                (jugador,)).fetchone()
        return dict(fila) if fila else None
