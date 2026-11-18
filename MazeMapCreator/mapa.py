"""
Modelo del editor de niveles: un mapa en memoria y su importación/exportación al formato JSON
de la carpeta Levels/ del juego (el mismo que lee Code/levels_parser.py).

  - Capa "Background": 1 = Floor (suelo), 2 = Wall (pared).
  - Capa "Objects":    0 = nada; si no, el id (1..N) del objeto en tileNames.
  - playerSpawnX / playerSpawnY: casilla donde aparece el jugador.
  - oscuridad (opcional): 0..1, niveles oscuros donde sólo se ve con la linterna.
"""

import json
import os
import sys

DIR_EDITOR = os.path.dirname(os.path.abspath(__file__))
DIR_PROYECTO = os.path.dirname(DIR_EDITOR)
DIR_NIVELES = os.path.join(DIR_PROYECTO, "Levels")
DIR_RECURSOS = os.path.join(DIR_PROYECTO, "Resources")

# El editor usa el mismo analizador de niveles que el juego para avisar de problemas.
_DIR_CODIGO = os.path.join(DIR_PROYECTO, "Code")
if _DIR_CODIGO not in sys.path:
    sys.path.insert(0, _DIR_CODIGO)
from levels_parser import OBJETOS_NIVEL, Layer, LevelData  # noqa: E402

SUELO = "Floor"
PARED = "Wall"
ENEMIGO = "DogDown1"
INICIO = "Inicio"     # herramienta: casilla de inicio del jugador
BORRAR = "Borrar"     # herramienta: quita el objeto de la casilla

# tileNames que se escriben al exportar (los mismos ids que Level_0.json).
TILE_NAMES = [SUELO, PARED, "Bone", ENEMIGO, "Exit", "Alarm", "PileOfBones", "Key", "DoorKey", "Mushroom",
              "RedStar", "Tunnel", "Gold", "Grenade", "FirstAid", "Door"]
# Lo que se puede poner en la capa Objects: los objetos del juego y los enemigos.
OBJETOS = [n for n in TILE_NAMES if n in OBJETOS_NIVEL or n == ENEMIGO]

TAM_CASILLA = 32
ANCHO_POR_DEFECTO = ALTO_POR_DEFECTO = 32
TAM_MINIMO, TAM_MAXIMO = 3, 200
# Tamaño máximo que admite el juego (MazeLab.NUM_CASILLAS_H x NUM_CASILLAS_VERTI).
MAX_ANCHO_JUEGO, MAX_ALTO_JUEGO = 40, 27


class Mapa:
    def __init__(self, ancho=ANCHO_POR_DEFECTO, alto=ALTO_POR_DEFECTO):
        self.comprobarTamano(ancho, alto)
        self.ancho, self.alto = ancho, alto
        # Mapa nuevo: suelo rodeado de pared.
        self.fondo = [[PARED if x in (0, ancho - 1) or y in (0, alto - 1) else SUELO for x in range(ancho)]
                      for y in range(alto)]
        self.objetos = {}          # (x, y) -> nombre del objeto
        self.inicio = (1, 1)       # (x, y) o None
        self.oscuridad = 0.0

    @staticmethod
    def comprobarTamano(ancho, alto):
        for valor in (ancho, alto):
            if not isinstance(valor, int) or not TAM_MINIMO <= valor <= TAM_MAXIMO:
                raise ValueError(f"El tamaño debe estar entre {TAM_MINIMO} y {TAM_MAXIMO} casillas")

    def dentro(self, x, y):
        return 0 <= x < self.ancho and 0 <= y < self.alto

    # ---------- Edición ----------
    # Aplica una herramienta en la casilla (x, y). Devuelve True si el mapa ha cambiado.
    # Poner un objeto o el inicio sobre una pared la convierte en suelo (el juego ignora lo que
    # está sobre pared); poner pared quita el objeto de la casilla.
    def pintar(self, x, y, herramienta):
        if not self.dentro(x, y):
            return False
        antes = self.estado()
        if herramienta == PARED:
            self.fondo[y][x] = PARED
            self.objetos.pop((x, y), None)
        elif herramienta == SUELO:
            self.fondo[y][x] = SUELO
        elif herramienta == BORRAR:
            self.objetos.pop((x, y), None)
        elif herramienta == INICIO:
            self.fondo[y][x] = SUELO
            self.inicio = (x, y)
        elif herramienta in OBJETOS:
            self.fondo[y][x] = SUELO
            self.objetos[(x, y)] = herramienta
        else:
            raise ValueError(f"Herramienta desconocida: {herramienta}")
        return self.estado() != antes

    # Botón derecho: quita el objeto; si no hay ninguno, pone pared.
    def borrar(self, x, y):
        if (x, y) in self.objetos:
            return self.pintar(x, y, BORRAR)
        return self.pintar(x, y, PARED)

    # Cambia el tamaño conservando lo que cabe (esquina superior izquierda). Las casillas nuevas
    # son pared; los objetos y el inicio que quedan fuera se pierden.
    def redimensionar(self, ancho, alto):
        self.comprobarTamano(ancho, alto)
        self.fondo = [[self.fondo[y][x] if x < self.ancho and y < self.alto else PARED for x in range(ancho)]
                      for y in range(alto)]
        self.ancho, self.alto = ancho, alto
        self.objetos = {p: n for p, n in self.objetos.items() if self.dentro(*p)}
        if self.inicio is not None and not self.dentro(*self.inicio):
            self.inicio = None

    # Copia de todo el mapa (para deshacer).
    def estado(self):
        return (self.ancho, self.alto, [fila[:] for fila in self.fondo], dict(self.objetos), self.inicio,
                self.oscuridad)

    def restaurar(self, estado):
        self.ancho, self.alto, fondo, objetos, self.inicio, self.oscuridad = estado
        self.fondo = [fila[:] for fila in fondo]
        self.objetos = dict(objetos)

    # ---------- JSON ----------
    @classmethod
    def desdeJson(cls, datos):
        """Crea un mapa a partir del JSON de un nivel. Devuelve (mapa, avisos)."""
        avisos = []
        nombres = list(datos.get("tileNames", []))

        def nombre(tile_id):
            return nombres[tile_id - 1] if isinstance(tile_id, int) and 1 <= tile_id <= len(nombres) else None

        capas = {c.get("name"): c.get("tiles", []) for c in datos.get("layers", [])}
        if "Background" not in capas:
            raise ValueError("El nivel no tiene la capa 'Background'")
        fondo = capas["Background"]
        objetos = capas.get("Objects", [])

        # Las dimensiones salen de las casillas; si no cuadran con width/height se avisa.
        alto = len(fondo)
        ancho = max((len(fila) for fila in fondo), default=0)
        cabecera = (datos.get("width"), datos.get("height"))
        if cabecera != (ancho, alto):
            avisos.append(f"La cabecera dice {cabecera[0]}x{cabecera[1]} pero las casillas son "
                          f"{ancho}x{alto}: se usa {ancho}x{alto}")
        if any(len(fila) != ancho for fila in fondo):
            avisos.append("Hay filas más cortas que otras: se completan con pared")

        mapa = cls(max(ancho, TAM_MINIMO), max(alto, TAM_MINIMO))
        mapa.objetos = {}
        raros = 0
        for y in range(mapa.alto):
            for x in range(mapa.ancho):
                tile = fondo[y][x] if y < len(fondo) and x < len(fondo[y]) else None
                if nombre(tile) == SUELO:
                    mapa.fondo[y][x] = SUELO
                else:
                    mapa.fondo[y][x] = PARED
                    if tile not in (None, 0) and nombre(tile) != PARED:
                        raros += 1
        if raros:
            avisos.append(f"{raros} casillas del fondo no eran Floor ni Wall: se dejan como pared")

        desconocidos = set()
        for y, fila in enumerate(objetos):
            for x, tile in enumerate(fila):
                if not tile or not mapa.dentro(x, y):
                    continue
                n = nombre(tile)
                if n in OBJETOS:
                    mapa.objetos[(x, y)] = n
                elif n is not None and n.startswith("Dog"):
                    mapa.objetos[(x, y)] = ENEMIGO
                else:
                    desconocidos.add(n or f"id {tile}")
        if desconocidos:
            avisos.append(f"Objetos que no conoce el juego (no se importan): {', '.join(sorted(desconocidos))}")

        inicio = (datos.get("playerSpawnX"), datos.get("playerSpawnY"))
        mapa.inicio = inicio if all(isinstance(v, int) for v in inicio) and mapa.dentro(*inicio) else None
        if mapa.inicio is None:
            avisos.append(f"El inicio del jugador {inicio} está fuera del mapa")
        mapa.oscuridad = float(datos.get("oscuridad", 0.0))
        return mapa, avisos

    @classmethod
    def importar(cls, ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return cls.desdeJson(json.load(f))

    def aJson(self):
        ids = {n: i + 1 for i, n in enumerate(TILE_NAMES)}
        datos = {
            "tileNames": list(TILE_NAMES),
            "width": self.ancho,
            "height": self.alto,
            "tileWidth": TAM_CASILLA,
            "tileHeight": TAM_CASILLA,
            "playerSpawnX": self.inicio[0] if self.inicio else 0,
            "playerSpawnY": self.inicio[1] if self.inicio else 0,
        }
        if self.oscuridad:
            datos["oscuridad"] = self.oscuridad
        datos["layers"] = [
            {"name": "Background", "tiles": [[ids[c] for c in fila] for fila in self.fondo]},
            {"name": "Objects", "tiles": [[ids[self.objetos[(x, y)]] if (x, y) in self.objetos else 0
                                           for x in range(self.ancho)] for y in range(self.alto)]},
        ]
        return datos

    # JSON con el mismo aspecto que los niveles de Levels/: una fila del mapa por línea.
    def textoJson(self):
        datos = self.aJson()
        lineas = ["{", f'  "tileNames": {json.dumps(datos["tileNames"])},']
        for clave in ("width", "height", "tileWidth", "tileHeight", "playerSpawnX", "playerSpawnY", "oscuridad"):
            if clave in datos:
                lineas.append(f'  "{clave}": {json.dumps(datos[clave])},')
        lineas.append('  "layers": [')
        for i, capa in enumerate(datos["layers"]):
            lineas += ["    {", f'      "name": {json.dumps(capa["name"])},', '      "tiles": [']
            filas = [f"        {json.dumps(fila)}" for fila in capa["tiles"]]
            lineas.append(",\n".join(filas))
            lineas += ["      ]", "    }" + ("," if i < len(datos["layers"]) - 1 else "")]
        lineas += ["  ]", "}", ""]
        return "\n".join(lineas)

    def exportar(self, ruta):
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(self.textoJson())

    # ---------- Comprobaciones ----------
    def problemas(self):
        """Problemas que tendría el nivel en el juego (los mismos que avisa el juego, más el tamaño)."""
        datos = self.aJson()
        nivel = LevelData(path="", tileNames=datos["tileNames"], width=self.ancho, height=self.alto,
                          tileWidth=TAM_CASILLA, tileHeight=TAM_CASILLA, playerSpawnX=datos["playerSpawnX"],
                          playerSpawnY=datos["playerSpawnY"],
                          layers=[Layer(c["name"], c["tiles"]) for c in datos["layers"]], oscuridad=self.oscuridad)
        problemas = []
        if self.ancho > MAX_ANCHO_JUEGO or self.alto > MAX_ALTO_JUEGO:
            problemas.append(f"El juego admite como máximo {MAX_ANCHO_JUEGO}x{MAX_ALTO_JUEGO} casillas; "
                             f"este mapa mide {self.ancho}x{self.alto}")
        if self.inicio is None:
            problemas.append("Falta la casilla de inicio del jugador")
        else:
            problemas += nivel.analizar()
        return problemas
