"""
Modelo del editor de niveles: un mapa en memoria y su importación/exportación al formato JSON
de la carpeta Levels/ del juego (el mismo que lee Code/levels_parser.py).

  - Capa "Background": 1 = Floor (suelo), 2 = Wall (pared).
  - Capa "Objects":    el id (1..N) en tileNames del objeto de la casilla; si no hay objeto, repite
                       el fondo (Floor o Wall). Así ningún objeto queda en una pared y sirve de doble
                       chequeo del fondo. Se importan también niveles antiguos con 0 en las casillas vacías.
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
from levels_parser import MAX_CASILLAS_PUERTA, OBJETOS_NIVEL, Layer, LevelData, agruparPuertas  # noqa: E402,F401

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
# Tamaño máximo que admite el juego (MazeLab.MAX_CASILLAS_H x MAX_CASILLAS_VERTI; con scroll
# horizontal y vertical).
MAX_ANCHO_JUEGO, MAX_ALTO_JUEGO = 64, 64
# Lo que se ve a la vez en el juego (la cámara): 27x27 casillas (MazeLab.NUM_CASILLAS_CAMARA y
# FILAS_CAMARA), dentro de una rejilla de al menos 40x27 (REJILLA_MINIMA_H/VERTI).
CAMARA_ANCHO, CAMARA_ALTO = 27, 27
REJILLA_MINIMA_H, REJILLA_MINIMA_VERTI = 40, 27


# ---------- Dimensiones del fichero ----------
# Las casillas mandan: el ancho y el alto reales son los de las capas (la fila más larga y la capa
# con más filas), aunque width/height digan otra cosa.
def dimensionesReales(datos):
    capas = [c.get("tiles", []) for c in datos.get("layers", []) if isinstance(c.get("tiles"), list)]
    alto = max((len(t) for t in capas), default=0)
    ancho = max((len(fila) for t in capas for fila in t if isinstance(fila, list)), default=0)
    return ancho, alto


def erroresDimensiones(datos):
    """Errores en la definición de las dimensiones del nivel (lista vacía si todo cuadra)."""
    ancho, alto = dimensionesReales(datos)
    errores = []
    if datos.get("width") != ancho:
        errores.append(f"width es {datos.get('width')} pero las casillas tienen {ancho} columnas")
    if datos.get("height") != alto:
        errores.append(f"height es {datos.get('height')} pero las casillas tienen {alto} filas")
    for capa in datos.get("layers", []):
        tiles = capa.get("tiles", [])
        nombre = capa.get("name", "?")
        if len(tiles) < alto:
            errores.append(f"La capa {nombre} tiene {len(tiles)} filas de {alto}")
        cortas = [y for y, fila in enumerate(tiles) if len(fila) < ancho]
        if cortas:
            errores.append(f"La capa {nombre} tiene {len(cortas)} fila(s) con menos de {ancho} columnas "
                           f"(la primera, la {cortas[0]})")
    return errores


def corregirDimensiones(datos):
    """Copia del JSON con sólo las dimensiones corregidas: width/height según las casillas y las casillas
    que faltan completadas: pared en Background, el mismo fondo en Objects (que lo repite) y 0 en
    cualquier otra capa. Todo lo demás queda igual."""
    ancho, alto = dimensionesReales(datos)
    nombres = list(datos.get("tileNames", []))
    pared = nombres.index(PARED) + 1 if PARED in nombres else 0
    corregido = {}
    for clave, valor in datos.items():
        if clave == "layers":
            valor = [dict(capa) for capa in valor]
        corregido[clave] = valor
    corregido["width"], corregido["height"] = ancho, alto

    def completar(capa, relleno):
        tiles = [list(fila) for fila in capa.get("tiles", [])]
        tiles += [[] for _ in range(alto - len(tiles))]
        capa["tiles"] = [fila + [relleno(x, y) for x in range(len(fila), ancho)] for y, fila in enumerate(tiles)]

    capas = corregido.get("layers", [])
    fondo = next((c for c in capas if c.get("name") == "Background"), None)
    if fondo is not None:
        completar(fondo, lambda x, y: pared)
    for capa in capas:
        if capa is fondo:
            continue
        if capa.get("name") == "Objects" and fondo is not None:
            completar(capa, lambda x, y: fondo["tiles"][y][x])
        else:
            completar(capa, lambda x, y: 0)
    return corregido


# JSON con el mismo aspecto que los niveles de Levels/: una fila del mapa por línea.
def textoNivel(datos):
    lineas = ["{"]
    claves = [k for k in datos if k != "layers"]
    for clave in claves:
        lineas.append(f'  {json.dumps(clave)}: {json.dumps(datos[clave], ensure_ascii=False)},')
    lineas.append('  "layers": [')
    capas = datos.get("layers", [])
    for i, capa in enumerate(capas):
        lineas.append("    {")
        for clave, valor in capa.items():
            if clave != "tiles":
                lineas.append(f'      {json.dumps(clave)}: {json.dumps(valor, ensure_ascii=False)},')
        lineas.append('      "tiles": [')
        lineas.append(",\n".join(f"        {json.dumps(fila)}" for fila in capa.get("tiles", [])))
        lineas += ["      ]", "    }" + ("," if i < len(capas) - 1 else "")]
    lineas += ["  ]", "}", ""]
    return "\n".join(lineas)


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
    # son suelo con el borde nuevo de pared; los objetos y el inicio que quedan fuera se pierden.
    def redimensionar(self, ancho, alto):
        self.comprobarTamano(ancho, alto)
        # Las casillas nuevas son suelo, salvo las del borde nuevo, que son pared (el nivel queda cerrado).
        def nueva(x, y):
            return PARED if x in (0, ancho - 1) or y in (0, alto - 1) else SUELO
        self.fondo = [[self.fondo[y][x] if x < self.ancho and y < self.alto else nueva(x, y) for x in range(ancho)]
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

        # Las dimensiones salen de las casillas (prevalecen sobre width/height). Los errores de
        # dimensiones los da erroresDimensiones(); aquí sólo se avisa del tamaño usado.
        ancho, alto = dimensionesReales(datos)
        if erroresDimensiones(datos):
            avisos.append(f"Las dimensiones del fichero no cuadran con sus casillas: se usa {ancho}x{alto}")

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
        vacias = distintas = 0
        for y, fila in enumerate(objetos):
            for x, tile in enumerate(fila):
                if not mapa.dentro(x, y):
                    continue
                if not tile:
                    vacias += 1
                    continue
                n = nombre(tile)
                if n in (SUELO, PARED):
                    distintas += n != mapa.fondo[y][x]   # doble chequeo: debe repetir el fondo
                elif n in OBJETOS:
                    mapa.objetos[(x, y)] = n
                elif n is not None and n.startswith("Dog"):
                    mapa.objetos[(x, y)] = ENEMIGO
                else:
                    desconocidos.add(n or f"id {tile}")
        if desconocidos:
            avisos.append(f"Objetos que no conoce el juego (no se importan): {', '.join(sorted(desconocidos))}")
        if distintas:
            avisos.append(f"La capa Objects no coincide con el fondo en {distintas} casilla(s): se usa el fondo")
        if vacias:
            avisos.append(f"La capa Objects tiene {vacias} casilla(s) vacías (formato antiguo): al exportar "
                          f"se rellenan con Floor y Wall")

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
            # Objects: el objeto de la casilla o, si no hay, el mismo fondo (Floor / Wall).
            {"name": "Objects", "tiles": [[ids[self.objetos.get((x, y), self.fondo[y][x])]
                                           for x in range(self.ancho)] for y in range(self.alto)]},
        ]
        return datos

    def textoJson(self):
        return textoNivel(self.aJson())

    def exportar(self, ruta):
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(self.textoJson())

    # ---------- Cámara del juego ----------
    # Posición más a la derecha y más abajo que puede tener la esquina superior izquierda de la
    # cámara, en casillas, igual que MazeLab.moverCamara: la rejilla del juego mide al menos 40x27 y,
    # si todo el suelo cabe en las 27 primeras columnas, la cámara no se mueve en horizontal.
    def limitesCamara(self):
        columnas = [x for fila in self.fondo for x, tipo in enumerate(fila) if tipo == SUELO]
        fija = bool(columnas) and max(columnas) < CAMARA_ANCHO
        maxX = 0 if fija else max(REJILLA_MINIMA_H, self.ancho) - CAMARA_ANCHO
        return maxX, max(REJILLA_MINIMA_VERTI, self.alto) - CAMARA_ALTO

    # Esquina superior izquierda de la cámara centrada en la casilla (x, y), sin salirse del mundo.
    def camaraCentradaEn(self, x, y):
        maxX, maxY = self.limitesCamara()
        return (max(0, min(x - CAMARA_ANCHO // 2, maxX)), max(0, min(y - CAMARA_ALTO // 2, maxY)))

    # ---------- Comprobaciones ----------
    # Puertas como las crea el juego: 2 o 3 casillas de puerta seguidas son una sola puerta.
    def puertas(self):
        return agruparPuertas(p for p, nombre in self.objetos.items() if nombre == "Door")

    # La puerta (lista de casillas) a la que pertenece la casilla (x, y), o None.
    def puertaEn(self, x, y):
        if self.objetos.get((x, y)) != "Door":
            return None
        return next(grupo for grupo in self.puertas() if (x, y) in grupo)

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
