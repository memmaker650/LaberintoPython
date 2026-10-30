import datetime
import logging
import sqlite3
from contextlib import closing

# estadisticas.py
# Datos de la partida del jugador en un nivel: se van sumando mientras se juega, se muestran
# en la pantalla final (Game Over o Nivel completado) y sólo se guardan en la base de datos
# cuando el jugador termina el nivel.

TABLA = "estadisticas_nivel"

SQL_CREAR_TABLA = f"""
CREATE TABLE IF NOT EXISTS {TABLA} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    jugador TEXT NOT NULL,
    nivel INTEGER NOT NULL,
    enemigos_muertos INTEGER NOT NULL,
    balas_disparadas INTEGER NOT NULL,
    impactos INTEGER NOT NULL,
    porcentaje_acierto REAL,
    huesos INTEGER NOT NULL,
    monedas_oro INTEGER NOT NULL,
    tiempo_segundos REAL NOT NULL,
    heridas INTEGER NOT NULL,
    vida_perdida INTEGER NOT NULL,
    puntos INTEGER NOT NULL
)
"""

COLUMNAS = ["fecha", "jugador", "nivel", "enemigos_muertos", "balas_disparadas", "impactos",
            "porcentaje_acierto", "huesos", "monedas_oro", "tiempo_segundos", "heridas",
            "vida_perdida", "puntos"]


class Estadisticas:
    def __init__(self, jugador="Memmaker650", nivel=1, inicio_ms=0):
        self.jugador = jugador
        self.nivel = nivel
        self.inicio_ms = inicio_ms

        self.enemigosMuertos = 0
        self.balasDisparadas = 0
        self.impactos = 0          # balas del jugador que han dado a un enemigo
        self.huesos = 0
        self.monedasOro = 0
        self.heridas = 0           # golpes recibidos (choques con enemigos y balas enemigas)
        self.vidaPerdida = 0       # puntos de vida perdidos en total
        self.puntos = 0
        self.tiempoSegundos = 0.0
        self.terminado = False

    # ---------- Partida guardada ----------
    CONTADORES = ["enemigosMuertos", "balasDisparadas", "impactos", "huesos", "monedasOro",
                  "heridas", "vidaPerdida"]

    # Contadores de la partida en curso, para guardarla y poder continuarla.
    def estado(self):
        return {campo: getattr(self, campo) for campo in self.CONTADORES}

    def restaurar(self, estado):
        for campo in self.CONTADORES:
            setattr(self, campo, int(estado.get(campo, 0)))

    # ---------- Registro durante la partida ----------
    def registrarDisparo(self):
        self.balasDisparadas += 1

    def registrarImpacto(self, enemigoMuerto):
        self.impactos += 1
        if enemigoMuerto:
            self.enemigosMuertos += 1

    def registrarHerida(self, dano):
        self.heridas += 1
        self.vidaPerdida += dano

    def registrarHuesos(self, cantidad=1):
        self.huesos += cantidad

    def registrarOro(self, cantidad=1):
        self.monedasOro += cantidad

    # Acierto en disparos: enemigos muertos / balas usadas, en %.
    # Ej.: 2 muertes con 7 balas = 2/7 = 28 %. None si no se ha disparado (no se puede dividir entre 0).
    @property
    def porcentajeAcierto(self):
        if self.balasDisparadas == 0:
            return None
        return 100.0 * self.enemigosMuertos / self.balasDisparadas

    # Cierra las estadísticas al acabar el nivel (por muerte o por llegar a la salida).
    def finalizar(self, ahora_ms, nivel=None, puntos=None):
        self.tiempoSegundos = max(0.0, (ahora_ms - self.inicio_ms) / 1000.0)
        if nivel is not None:
            self.nivel = nivel
        if puntos is not None:
            self.puntos = puntos
        self.terminado = True

    @staticmethod
    def formatoTiempo(segundos):
        minutos, resto = divmod(int(segundos), 60)
        return f"{minutos:02d}:{resto:02d}"

    # Textos que se muestran en la pantalla final, uno por línea.
    def lineas(self):
        return [
            f"Enemigos muertos: {self.enemigosMuertos}",
            f"Balas usadas: {self.balasDisparadas}",
            self.textoAcierto(),
            f"Huesos recolectados: {self.huesos}",
            f"Monedas de oro: {self.monedasOro}",
            f"Tiempo: {self.formatoTiempo(self.tiempoSegundos)}",
            f"Heridas recibidas: {self.heridas} (-{self.vidaPerdida} de vida)",
        ]

    def textoAcierto(self):
        if self.porcentajeAcierto is None:
            return "Acierto en disparos: - (ningún disparo)"
        # Sin decimales y truncado, como en el ejemplo: 2/7 = 0,2857 -> 28 %.
        return (f"Acierto en disparos: {int(self.porcentajeAcierto)} % "
                f"({self.enemigosMuertos} muertes / {self.balasDisparadas} balas)")

    def comoFila(self):
        return {
            "fecha": datetime.datetime.now().isoformat(timespec="seconds"),
            "jugador": self.jugador,
            "nivel": self.nivel,
            "enemigos_muertos": self.enemigosMuertos,
            "balas_disparadas": self.balasDisparadas,
            "impactos": self.impactos,
            "porcentaje_acierto": None if self.porcentajeAcierto is None else round(self.porcentajeAcierto, 2),
            "huesos": self.huesos,
            "monedas_oro": self.monedasOro,
            "tiempo_segundos": round(self.tiempoSegundos, 2),
            "heridas": self.heridas,
            "vida_perdida": self.vidaPerdida,
            "puntos": self.puntos,
        }

    # ---------- Base de datos ----------
    @staticmethod
    def crearTabla(conexion):
        conexion.execute(SQL_CREAR_TABLA)

    # Guarda las estadísticas en la base de datos y devuelve el id de la fila creada.
    def guardar(self, ruta_bd):
        fila = self.comoFila()
        with closing(sqlite3.connect(ruta_bd)) as conexion, conexion:
            self.crearTabla(conexion)
            cursor = conexion.execute(
                f"INSERT INTO {TABLA} ({', '.join(COLUMNAS)}) VALUES ({', '.join('?' for _ in COLUMNAS)})",
                [fila[c] for c in COLUMNAS])
            identificador = cursor.lastrowid
        logging.info("Estadísticas del nivel %s guardadas en %s (id %s)", self.nivel, ruta_bd, identificador)
        return identificador

    # Lista de filas guardadas (diccionarios), de la más antigua a la más reciente.
    @staticmethod
    def cargarTodas(ruta_bd):
        with closing(sqlite3.connect(ruta_bd)) as conexion:
            Estadisticas.crearTabla(conexion)
            conexion.row_factory = sqlite3.Row
            return [dict(fila) for fila in conexion.execute(f"SELECT * FROM {TABLA} ORDER BY id")]
