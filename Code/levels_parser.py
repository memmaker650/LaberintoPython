from __future__ import annotations

import json
import os
from dataclasses import dataclass
from glob import glob
from typing import Any, Dict, List, Optional, Iterable

# Objetos de la capa Objects (nombre en tileNames) y su código en el laberinto del juego
# (MazeLab.mazeDataExtra). Los "Dog..." no son objetos: marcan dónde empiezan los enemigos.
OBJETOS_NIVEL = {
    "Bone": 2,          # hueso
    "PileOfBones": 3,   # pila de huesos
    "Exit": 4,          # bandera de fin de nivel
    "Key": 6,           # llave dorada (fin de nivel)
    "DoorKey": 7,       # llave de las puertas
    "Mushroom": 8,      # champiñón
    "RedStar": 9,       # estrella roja
    "Tunnel": 10,       # túnel
    "Gold": 11,         # monedas de oro
    "Grenade": 13,      # granada
    "FirstAid": 15,     # botiquín
    "Alarm": 16,        # luz de alarma
    "Door": 33,         # puerta
}
# Jefe enemigo: casilla donde empieza (uno por nivel; si no hay, el juego elige una al azar).
JEFE = "Boss"
# Tiles del fondo. En la capa Objects marcan las casillas sin objeto (y deben coincidir con el fondo).
BASES = ("Floor", "Wall")
# Una puerta puede ocupar 1, 2 o 3 casillas seguidas (para pasillos de 2 o 3 casillas de ancho).
MAX_CASILLAS_PUERTA = 3


# Tramos de puertas seguidas: [[(x, y), ...], ...]. Las casillas de puerta contiguas en una fila
# forman un tramo horizontal (de izquierda a derecha); si no, las contiguas en una columna forman
# uno vertical (de arriba abajo); una puerta suelta es un tramo de 1. Los tramos no se limitan aquí.
def tramosPuertas(casillas) -> List[List[tuple]]:
    pendientes = set(casillas)
    tramos = []
    for x, y in sorted(pendientes, key=lambda p: (p[1], p[0])):
        if (x, y) not in pendientes:
            continue
        paso = (1, 0) if (x + 1, y) in pendientes else (0, 1)
        tramo = [(x, y)]
        while (tramo[-1][0] + paso[0], tramo[-1][1] + paso[1]) in pendientes:
            tramo.append((tramo[-1][0] + paso[0], tramo[-1][1] + paso[1]))
        pendientes -= set(tramo)
        tramos.append(tramo)
    return tramos


# Puertas del nivel: cada una es la lista de sus casillas (1 a MAX_CASILLAS_PUERTA). Un tramo más
# largo se parte en puertas de 3 (el análisis del nivel avisa).
def agruparPuertas(casillas) -> List[List[tuple]]:
    return [tramo[i:i + MAX_CASILLAS_PUERTA] for tramo in tramosPuertas(casillas)
            for i in range(0, len(tramo), MAX_CASILLAS_PUERTA)]


@dataclass
class Layer:
    name: str
    tiles: List[List[int]]  # filas -> columnas


@dataclass
class LevelData:
    path: str
    tileNames: List[str]
    width: int
    height: int
    tileWidth: int
    tileHeight: int
    playerSpawnX: int
    playerSpawnY: int
    layers: List[Layer]
    oscuridad: float = 0.0  # 0 = nivel iluminado; 0.9 = 90% de oscuridad (sólo se ve con la linterna)

    def get_layer(self, name: str) -> Optional[Layer]:
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None

    def tiles_iter(self, layer_name: str) -> Iterable[tuple[int, int, int]]:
        layer = self.get_layer(layer_name)
        if not layer:
            return
        for y, row in enumerate(layer.tiles):
            for x, tile_id in enumerate(row):
                yield (y, x, tile_id)

    def get_tile(self, layer_name: str, x: int, y: int) -> Optional[int]:
        layer = self.get_layer(layer_name)
        if not layer:
            return None
        if 0 <= y < len(layer.tiles) and 0 <= x < len(layer.tiles[y]):
            return layer.tiles[y][x]
        return None

    def validate(self) -> None:
        required = [
            "tileNames", "width", "height", "tileWidth", "tileHeight",
            "playerSpawnX", "playerSpawnY", "layers"
        ]
        missing = [k for k in required if getattr(self, k, None) is None]
        if missing:
            raise ValueError(f"Faltan claves requeridas: {missing}")

        if self.width <= 0 or self.height <= 0:
            raise ValueError("width/height deben ser > 0")
        if self.tileWidth <= 0 or self.tileHeight <= 0:
            raise ValueError("tileWidth/tileHeight deben ser > 0")

        if not self.layers:
            raise ValueError("Debe existir al menos un layer")

        if not 0 <= self.oscuridad <= 1:
            raise ValueError(f"oscuridad debe estar entre 0 y 1; es {self.oscuridad}")

        for layer in self.layers:
            if not isinstance(layer.name, str) or not layer.name:
                raise ValueError("Cada layer debe tener 'name' no vacío")
            if not isinstance(layer.tiles, list) or len(layer.tiles) != self.height:
                raise ValueError(
                    f"Layer '{layer.name}' debe tener {self.height} filas; tiene {len(layer.tiles)}"
                )
            for y, row in enumerate(layer.tiles):
                if not isinstance(row, list) or len(row) != self.width:
                    raise ValueError(
                        f"Layer '{layer.name}' fila {y} debe tener {self.width} columnas; tiene {len(row)}"
                    )
                for x, v in enumerate(row):
                    if not isinstance(v, int) or v < 0:
                        raise ValueError(
                            f"Tile inválido en layer '{layer.name}' ({y},{x}): {v}"
                        )
        
    # ----------------------------------------------------------------
    # Análisis de coherencia del nivel.
    # Los ids de tile empiezan en 1 y apuntan a tileNames (0 = vacío):
    # 1 Floor, 2 Wall, 3 Bone, 4 DogDown1, 5 Exit... Los objetos que se
    # pueden poner en la capa Objects están en OBJETOS_NIVEL.
    # La capa Objects repite también el fondo: Wall en las paredes y, en el suelo, Floor o
    # el objeto de la casilla. Así no se pueden poner objetos en paredes y se comprueba dos
    # veces que el fondo es el que se quería (ver analizar).
    # ----------------------------------------------------------------
    def tile_name(self, tile_id: int) -> Optional[str]:
        if 1 <= tile_id <= len(self.tileNames):
            return self.tileNames[tile_id - 1]
        return None

    def es_suelo(self, x: int, y: int) -> bool:
        return self.tile_name(self.get_tile("Background", x, y) or 0) == "Floor"

    def casillas_suelo(self) -> set:
        return {(x, y) for y, x, _ in self.tiles_iter("Background") if self.es_suelo(x, y)}

    def alcanzables_desde(self, x: int, y: int) -> set:
        # Casillas de suelo a las que se llega andando (4 direcciones) desde (x, y).
        suelo = self.casillas_suelo()
        if (x, y) not in suelo:
            return set()
        visitadas = {(x, y)}
        pendientes = [(x, y)]
        while pendientes:
            cx, cy = pendientes.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                vecina = (cx + dx, cy + dy)
                if vecina in suelo and vecina not in visitadas:
                    visitadas.add(vecina)
                    pendientes.append(vecina)
        return visitadas

    def zonas_suelo(self) -> List[int]:
        # Tamaño de cada zona de suelo conectada, de mayor a menor.
        restantes = self.casillas_suelo()
        zonas = []
        while restantes:
            zona = self.alcanzables_desde(*next(iter(restantes)))
            zonas.append(len(zona))
            restantes -= zona
        return sorted(zonas, reverse=True)

    def objetos(self) -> Dict[str, List[tuple]]:
        # {nombre: [(x, y), ...]} de la capa Objects. Floor y Wall no son objetos (repiten el fondo).
        resultado: Dict[str, List[tuple]] = {}
        for y, x, tile_id in self.tiles_iter("Objects"):
            if tile_id and self.tile_name(tile_id) not in BASES:
                nombre = self.tile_name(tile_id) or f"id {tile_id}"
                resultado.setdefault(nombre, []).append((x, y))
        return resultado

    def puertas(self) -> List[List[tuple]]:
        # Una entrada por puerta (2 o 3 puertas seguidas son una sola), con sus casillas.
        return agruparPuertas(self.objetos().get("Door", []))

    def analizar(self) -> List[str]:
        # Devuelve la lista de problemas encontrados (vacía si el nivel tiene sentido).
        problemas: List[str] = []
        for capa in ("Background", "Objects"):
            if self.get_layer(capa) is None:
                problemas.append(f"Falta la capa '{capa}'")
        if problemas:
            return problemas

        ids_fondo = {t for _, _, t in self.tiles_iter("Background")}
        raros = sorted(t for t in ids_fondo if self.tile_name(t) not in ("Floor", "Wall"))
        if raros:
            problemas.append(f"El fondo usa ids que no son Floor ni Wall: {raros}")

        suelo = self.casillas_suelo()
        if not suelo:
            problemas.append("El nivel no tiene ninguna casilla de suelo")
            return problemas

        sx, sy = self.playerSpawnX, self.playerSpawnY
        if not (0 <= sx < self.width and 0 <= sy < self.height):
            problemas.append(f"La salida del jugador ({sx}, {sy}) está fuera del mapa")
            alcanzables = set()
        elif not self.es_suelo(sx, sy):
            problemas.append(f"El jugador aparece sobre una pared en ({sx}, {sy})")
            alcanzables = set()
        else:
            alcanzables = self.alcanzables_desde(sx, sy)
            if len(alcanzables) < len(suelo):
                problemas.append(
                    f"{len(suelo) - len(alcanzables)} de {len(suelo)} casillas de suelo "
                    f"no se pueden alcanzar desde el inicio del jugador")

        zonas = self.zonas_suelo()
        if len(zonas) > 1:
            problemas.append(f"El suelo está dividido en {len(zonas)} zonas separadas: {zonas}")

        borde = [(x, y) for (x, y) in suelo
                 if x in (0, self.width - 1) or y in (0, self.height - 1)]
        if borde:
            problemas.append(f"El borde no está cerrado: {len(borde)} casillas de suelo en el borde del mapa")

        problemas += self.comprobarObjectsConFondo()

        objetos = self.objetos()
        for nombre, posiciones in sorted(objetos.items()):
            if nombre.startswith("id "):
                problemas.append(f"La capa Objects usa un {nombre} que no existe en tileNames")
            elif nombre not in OBJETOS_NIVEL and nombre != JEFE and not nombre.startswith("Dog"):
                problemas.append(f"La capa Objects usa '{nombre}', que no es un objeto conocido "
                                 f"({', '.join(sorted(OBJETOS_NIVEL))}, {JEFE} o Dog...)")
            en_pared = [p for p in posiciones if p not in suelo]
            if en_pared:
                problemas.append(f"{len(en_pared)} de {len(posiciones)} '{nombre}' están sobre una pared")
            inalcanzables = [p for p in posiciones if p in suelo and p not in alcanzables]
            if inalcanzables and alcanzables:
                problemas.append(f"{len(inalcanzables)} '{nombre}' no se pueden alcanzar")

        largos = [t for t in tramosPuertas(objetos.get("Door", [])) if len(t) > MAX_CASILLAS_PUERTA]
        if largos:
            x, y = largos[0][0]
            problemas.append(f"{len(largos)} puerta(s) de más de {MAX_CASILLAS_PUERTA} casillas seguidas "
                             f"(la primera, de {len(largos[0])} en ({x}, {y})); se parten en puertas de "
                             f"{MAX_CASILLAS_PUERTA}")

        jefes = objetos.get(JEFE, [])
        if len(jefes) > 1:
            problemas.append(f"El nivel tiene {len(jefes)} jefes ('{JEFE}'); sólo se usa el primero")

        salidas = objetos.get("Exit", [])
        if not salidas:
            problemas.append("El nivel no tiene salida ('Exit')")
        elif len(salidas) > 1:
            problemas.append(f"El nivel tiene {len(salidas)} salidas")
        return problemas

    def comprobarObjectsConFondo(self) -> List[str]:
        # Doble chequeo: en cada casilla, Objects debe decir Wall si el fondo es pared, y Floor
        # (o un objeto) si es suelo. Un objeto sobre pared lo avisa analizar() aparte.
        vacias, distintas = [], []
        for y, x, tile_id in self.tiles_iter("Objects"):
            nombre = self.tile_name(tile_id) if tile_id else None
            if not tile_id:
                vacias.append((x, y))
            elif nombre in BASES and nombre != ("Floor" if self.es_suelo(x, y) else "Wall"):
                distintas.append((x, y, nombre))
        problemas = []
        if vacias:
            problemas.append(f"La capa Objects tiene {len(vacias)} casilla(s) vacías (0); deben llevar "
                             f"Floor, Wall o un objeto. La primera, {vacias[0]}")
        if distintas:
            x, y, nombre = distintas[0]
            fondo = self.tile_name(self.get_tile("Background", x, y) or 0)
            problemas.append(f"La capa Objects no coincide con el fondo en {len(distintas)} casilla(s). "
                             f"La primera, ({x}, {y}): Objects dice {nombre} y el fondo {fondo}")
        return problemas

    def mismo_mapa(self, otro: "LevelData") -> bool:
        return (self.width, self.height, [l.tiles for l in self.layers]) == \
               (otro.width, otro.height, [l.tiles for l in otro.layers])

    def debug_layers(self) -> None:
        print(f"Level: {os.path.basename(self.path)}")
        print(f"Total layers: {len(self.layers)}")
        for idx, layer in enumerate(self.layers, start=1):
            print(f"\nLayer #{idx}: {layer.name}")
            for fila in layer.tiles:
                print(" ".join(f"{v:2d}" for v in fila))


class LevelParser:
    def __init__(self, levels_dir: str) -> None:
        self.levels_dir = os.path.abspath(levels_dir)
        self._cache: Dict[str, LevelData] = {}

    def list_level_files(self, pattern: str = "Level_*.json") -> List[str]:
        return sorted(glob(os.path.join(self.levels_dir, pattern)))

    def load_all(self) -> List[LevelData]:
        files = self.list_level_files()
        return [self.load(path) for path in files]

    def load(self, path: str) -> LevelData:
        abs_path = os.path.abspath(path)
        if abs_path in self._cache:
            return self._cache[abs_path]

        with open(abs_path, "r", encoding="utf-8") as f:
            raw: Dict[str, Any] = json.load(f)

        level = self._from_raw(abs_path, raw)
        level.validate()
        self._cache[abs_path] = level
        return level

    def load_by_name(self, filename: str) -> LevelData:
        return self.load(os.path.join(self.levels_dir, filename))

    def _from_raw(self, path: str, raw: Dict[str, Any]) -> LevelData:
        tile_names = list(raw.get("tileNames", []))
        width = int(raw.get("width", 0))
        height = int(raw.get("height", 0))
        tile_w = int(raw.get("tileWidth", 0))
        tile_h = int(raw.get("tileHeight", 0))
        spawn_x = int(raw.get("playerSpawnX", 0))
        spawn_y = int(raw.get("playerSpawnY", 0))
        oscuridad = float(raw.get("oscuridad", 0.0))

        layers_raw = raw.get("layers", [])
        layers: List[Layer] = []
        for lr in layers_raw:
            name = str(lr.get("name", ""))
            tiles = lr.get("tiles", [])
            tiles_norm: List[List[int]] = [list(row) for row in tiles]
            layers.append(Layer(name=name, tiles=tiles_norm))

        return LevelData(
            path=path,
            tileNames=tile_names,
            width=width,
            height=height,
            tileWidth=tile_w,
            tileHeight=tile_h,
            playerSpawnX=spawn_x,
            playerSpawnY=spawn_y,
            layers=layers,
            oscuridad=oscuridad,
        )

def informe_niveles(levels_dir: str) -> str:
    # Texto con el análisis de todos los niveles de la carpeta, incluidos los repetidos.
    niveles = LevelParser(levels_dir).load_all()
    lineas: List[str] = []
    for i, nivel in enumerate(niveles):
        nombre = os.path.basename(nivel.path)
        objetos = nivel.objetos()
        resumen = ", ".join(f"{len(v)} {k}" for k, v in sorted(objetos.items()))
        if nivel.oscuridad:
            resumen += f", oscuro ({round(nivel.oscuridad * 100)}%)"
        lineas.append(f"{nombre}: {nivel.width}x{nivel.height}, inicio ({nivel.playerSpawnX}, "
                      f"{nivel.playerSpawnY}), {len(nivel.casillas_suelo())} casillas de suelo, {resumen}")
        iguales = [os.path.basename(o.path) for o in niveles[:i] if o.mismo_mapa(nivel)]
        if iguales:
            lineas.append(f"  - Es idéntico a {', '.join(iguales)}")
        problemas = nivel.analizar()
        lineas.extend(f"  - {p}" for p in problemas)
        if not problemas and not iguales:
            lineas.append("  - OK")
    return "\n".join(lineas)


if __name__ == "__main__":
    print(informe_niveles(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Levels")))
