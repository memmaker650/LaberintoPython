"""
MazeMapCreator: editor gráfico de niveles para el juego (pygame-ce o pygame).

    python3 MazeMapCreator/mazMapCreator.py [nivel.json]

  - Izquierda: elementos (suelo, pared, inicio del jugador, enemigo, puerta, oro...). Clic para elegir.
  - Centro: el mapa. Botón izquierdo pinta (se puede arrastrar); botón derecho quita el objeto
    de la casilla o, si no hay, pone pared.
  - Arriba a la derecha: tamaño del mapa en casillas (X, Y) y "Aplicar".
  - Importar / Exportar: niveles JSON de la carpeta Levels/ (también se puede arrastrar un .json
    a la ventana para abrirlo). Al importar mandan las casillas: si width/height u otras dimensiones
    del fichero no cuadran con ellas, se pregunta si se quiere corregir el fichero (sólo eso).
  - Atajos: Ctrl/Cmd+Z deshacer, Ctrl/Cmd+O importar, Ctrl/Cmd+S exportar, ESC cerrar diálogo.
"""

import json
import os
import sys

import pygame

import mapa as modelo
from mapa import BORRAR, ENEMIGO, INICIO, PARED, SUELO, Mapa

TAMANO_VENTANA = (1200, 820)
ANCHO_PANEL = 210
ALTO_BARRA = 64
ALTO_ESTADO = 58
MARGEN = 10
ALTO_ELEMENTO = 38
MAX_DESHACER = 100

FONDO = (38, 32, 44)
PANEL = (52, 44, 60)
BOTON = (90, 84, 100)
BOTON_ENCIMA = (255, 140, 0)
BOTON_ELEGIDO = (216, 75, 32)
TEXTO = (240, 240, 240)
TEXTO_SUAVE = (170, 165, 180)
COLOR_SUELO = (205, 195, 165)
COLOR_PARED = (75, 62, 52)
COLOR_REJILLA = (30, 26, 34)
COLOR_OK = (110, 210, 90)
COLOR_AVISO = (255, 170, 60)
COLOR_CAMPO = (25, 22, 30)

# Paleta: (herramienta, etiqueta, imagen en Resources/ o None si se dibuja).
ELEMENTOS = [
    (SUELO, "Suelo", "Floor.png"),
    (PARED, "Pared", "Wall.png"),
    (INICIO, "Inicio jugador", "player.png"),
    (ENEMIGO, "Enemigo", "DogDown1.png"),
    ("Door", "Puerta", None),
    ("Alarm", "Alarma", None),
    ("Exit", "Salida", "banderaPirataRoja2.png"),
    ("Key", "Llave", "llave.png"),
    ("DoorKey", "Llave puerta", "llave_puerta.png"),
    ("Gold", "Oro", "Oro.png"),
    ("Bone", "Hueso", "Bone.png"),
    ("PileOfBones", "Pila de huesos", "PileOfBones.png"),
    ("Mushroom", "Champiñón", "powerMushroom.png"),
    ("RedStar", "Estrella roja", "redstar.png"),
    ("Tunnel", "Túnel", "CompuertaTunnel.png"),
    ("Grenade", "Granada", "granada-de-mano.png"),
    ("FirstAid", "Botiquín", "medical-box.png"),
    (BORRAR, "Borrar objeto", None),
]
BOTONES_BARRA = [("nuevo", "Nuevo"), ("importar", "Importar"), ("exportar", "Exportar"), ("deshacer", "Deshacer")]


class CampoNumero:
    def __init__(self, etiqueta, valor):
        self.etiqueta = etiqueta
        self.texto = str(valor)
        self.activo = False
        self.rect = pygame.Rect(0, 0, 0, 0)

    def valor(self):
        return int(self.texto) if self.texto.isdigit() else None


class Editor:
    def __init__(self, pantalla, ruta=None):
        self.pantalla = pantalla
        self.mapa = Mapa()
        self.ruta = None                 # fichero importado/exportado
        self.cambios = False             # hay cambios sin exportar
        self.deshacer = []
        self.herramienta = PARED
        self.trazo = None                # (botón, estado antes del trazo, última casilla)
        self.dialogo = None              # None, "importar", "exportar", "sobrescribir", "salir", "corregir"
        self.datosFichero = None         # JSON importado con errores de dimensiones (para corregirlo)
        self.erroresFichero = []
        self.textoFichero = ""
        self.desplazamientoLista = 0
        self.salir = False
        self.mensaje = "Elige un elemento a la izquierda y pinta en el mapa."
        self.colorMensaje = TEXTO_SUAVE
        self.campos = [CampoNumero("X", self.mapa.ancho), CampoNumero("Y", self.mapa.alto)]
        self.fuente = pygame.font.SysFont("Arial", 17)
        self.fuentePequena = pygame.font.SysFont("Arial", 14)
        self.fuenteTitulo = pygame.font.SysFont("Arial", 22, bold=True)
        self.iconos = {}
        self.cacheCasillas = {}
        self.superficieMapa = None       # mapa ya pintado (se rehace al cambiar)
        self.problemas = self.mapa.problemas()
        self.botones = {}                # nombre -> Rect (los calcula dibujar)
        if ruta:
            self.importar(ruta)

    # ---------- Disposición ----------
    def zonaMapa(self):
        ancho, alto = self.pantalla.get_size()
        return pygame.Rect(ANCHO_PANEL + MARGEN, ALTO_BARRA + MARGEN,
                           max(10, ancho - ANCHO_PANEL - 2 * MARGEN), max(10, alto - ALTO_BARRA - ALTO_ESTADO - 2 * MARGEN))

    def tamanoCasilla(self):
        zona = self.zonaMapa()
        return max(2, min(zona.width // self.mapa.ancho, zona.height // self.mapa.alto))

    def rectMapa(self):
        zona, c = self.zonaMapa(), self.tamanoCasilla()
        rect = pygame.Rect(0, 0, c * self.mapa.ancho, c * self.mapa.alto)
        rect.center = zona.center
        return rect

    def casillaEn(self, pos):
        rect = self.rectMapa()
        if not rect.collidepoint(pos):
            return None
        c = self.tamanoCasilla()
        return (pos[0] - rect.x) // c, (pos[1] - rect.y) // c

    def rectElemento(self, i):
        return pygame.Rect(MARGEN, ALTO_BARRA + MARGEN + i * ALTO_ELEMENTO, ANCHO_PANEL - 2 * MARGEN, ALTO_ELEMENTO - 4)

    def calcularBotones(self):
        ancho = self.pantalla.get_width()
        b = {}
        x = ANCHO_PANEL + MARGEN
        for nombre, _ in BOTONES_BARRA:
            b[nombre] = pygame.Rect(x, 14, 96, 36)
            x += 104
        # Arriba a la derecha: X [  ]  Y [  ]  [Aplicar]
        b["aplicar"] = pygame.Rect(ancho - MARGEN - 90, 14, 90, 36)
        self.campos[1].rect = pygame.Rect(b["aplicar"].x - 10 - 64, 14, 64, 36)
        self.campos[0].rect = pygame.Rect(self.campos[1].rect.x - 30 - 64, 14, 64, 36)
        self.botones = b

    # ---------- Acciones ----------
    def guardarDeshacer(self, estado=None):
        self.deshacer.append(estado if estado is not None else self.mapa.estado())
        del self.deshacer[:-MAX_DESHACER]

    def mapaCambiado(self):
        self.cambios = True
        self.superficieMapa = None
        self.problemas = self.mapa.problemas()
        for campo, valor in zip(self.campos, (self.mapa.ancho, self.mapa.alto)):
            if not campo.activo:
                campo.texto = str(valor)

    def avisar(self, texto, color=TEXTO_SUAVE):
        self.mensaje, self.colorMensaje = texto, color

    def hacerDeshacer(self):
        if not self.deshacer:
            self.avisar("No hay nada que deshacer.")
            return
        self.mapa.restaurar(self.deshacer.pop())
        self.mapaCambiado()
        self.avisar("Deshecho.")

    def aplicarTamano(self):
        ancho, alto = (campo.valor() for campo in self.campos)
        for campo in self.campos:
            campo.activo = False
        if ancho is None or alto is None:
            self.avisar("Escribe un número de casillas en X y en Y.", COLOR_AVISO)
            return False
        if (ancho, alto) == (self.mapa.ancho, self.mapa.alto):
            return False
        antes = self.mapa.estado()
        try:
            self.mapa.redimensionar(ancho, alto)
        except ValueError as error:
            self.avisar(str(error), COLOR_AVISO)
            self.mapaCambiado()   # vuelve a mostrar el tamaño actual
            return False
        self.guardarDeshacer(antes)
        self.mapaCambiado()
        self.avisar(f"Mapa de {ancho}x{alto} casillas.")
        return True

    def nuevo(self):
        ancho, alto = (campo.valor() for campo in self.campos)
        try:
            nuevo = Mapa(ancho or modelo.ANCHO_POR_DEFECTO, alto or modelo.ALTO_POR_DEFECTO)
        except ValueError as error:
            self.avisar(str(error), COLOR_AVISO)
            return
        self.guardarDeshacer()
        self.mapa = nuevo
        self.ruta = None
        self.mapaCambiado()
        self.avisar(f"Mapa nuevo de {nuevo.ancho}x{nuevo.alto} (Deshacer lo recupera).")

    def importar(self, ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
            nuevo, avisos = Mapa.desdeJson(datos)
            errores = modelo.erroresDimensiones(datos)
        except (OSError, ValueError, TypeError, AttributeError) as error:
            self.avisar(f"No se puede importar {os.path.basename(ruta)}: {error}", COLOR_AVISO)
            return False
        self.guardarDeshacer()
        self.mapa = nuevo
        self.ruta = os.path.abspath(ruta)
        self.mapaCambiado()
        self.cambios = bool(avisos)      # si se ha corregido algo, el fichero ya no es igual
        texto = f"Importado {os.path.basename(ruta)} ({nuevo.ancho}x{nuevo.alto})."
        self.avisar(texto + (" " + " · ".join(avisos) if avisos else ""), COLOR_AVISO if avisos else COLOR_OK)
        # Dimensiones mal definidas en el fichero: se pregunta si se corrigen en el propio fichero.
        self.datosFichero, self.erroresFichero = (datos, errores) if errores else (None, [])
        if errores:
            self.dialogo = "corregir"
        return True

    # Botón "Corregir" del aviso de dimensiones: reescribe el fichero importado cambiando sólo lo
    # que está mal (width/height y filas incompletas); el resto del fichero queda igual.
    def corregirFichero(self):
        self.dialogo = None
        corregido = modelo.corregirDimensiones(self.datosFichero)
        try:
            with open(self.ruta, "w", encoding="utf-8") as f:
                f.write(modelo.textoNivel(corregido))
        except OSError as error:
            self.avisar(f"No se puede corregir {os.path.basename(self.ruta)}: {error}", COLOR_AVISO)
            return False
        _, avisos = Mapa.desdeJson(corregido)
        self.cambios = bool(avisos)
        self.avisar(f"Corregido {os.path.basename(self.ruta)}: ahora mide {corregido['width']}x{corregido['height']} "
                    f"({len(self.erroresFichero)} error(es) de dimensiones).", COLOR_OK)
        self.datosFichero, self.erroresFichero = None, []
        return True

    def noCorregirFichero(self):
        self.dialogo = None
        self.datosFichero, self.erroresFichero = None, []
        self.cambios = True              # lo que se ve ya no es igual que el fichero
        self.avisar(f"{os.path.basename(self.ruta)} no se ha corregido; al exportarlo se escribirán las "
                    f"dimensiones de las casillas.", COLOR_AVISO)

    def exportar(self, ruta):
        try:
            self.mapa.exportar(ruta)
        except OSError as error:
            self.avisar(f"No se puede exportar: {error}", COLOR_AVISO)
            return False
        self.ruta = os.path.abspath(ruta)
        self.cambios = False
        if self.problemas:
            self.avisar(f"Exportado {os.path.basename(ruta)}, pero el juego verá {len(self.problemas)} "
                        f"problema(s): {self.problemas[0]}", COLOR_AVISO)
        else:
            self.avisar(f"Exportado {os.path.basename(ruta)}.", COLOR_OK)
        return True

    def ficherosNiveles(self):
        if not os.path.isdir(modelo.DIR_NIVELES):
            return []
        return sorted(f for f in os.listdir(modelo.DIR_NIVELES) if f.lower().endswith(".json"))

    def nombreSugerido(self):
        if self.ruta:
            return os.path.basename(self.ruta)
        existentes = set(self.ficherosNiveles())
        n = 0
        while f"Level_{n}.json" in existentes:
            n += 1
        return f"Level_{n}.json"

    def abrirDialogo(self, tipo):
        self.dialogo = tipo
        self.trazo = None
        if tipo == "exportar":
            self.textoFichero = self.nombreSugerido()
        if tipo == "importar":
            self.desplazamientoLista = 0

    def rutaExportar(self):
        nombre = self.textoFichero.strip()
        if not nombre:
            return None
        if not nombre.lower().endswith(".json"):
            nombre += ".json"
        return os.path.join(modelo.DIR_NIVELES, os.path.basename(nombre))

    def confirmarExportar(self):
        ruta = self.rutaExportar()
        if ruta is None:
            self.avisar("Escribe un nombre de fichero.", COLOR_AVISO)
            return
        if os.path.exists(ruta) and os.path.abspath(ruta) != self.ruta:
            self.dialogo = "sobrescribir"
            return
        self.dialogo = None
        self.exportar(ruta)

    def pedirSalir(self):
        if self.cambios:
            self.dialogo = "salir"
        else:
            self.salir = True

    # ---------- Pintar con el ratón ----------
    def pintarEn(self, casilla, boton):
        x, y = casilla
        if boton == 3:
            return self.mapa.borrar(x, y)
        return self.mapa.pintar(x, y, self.herramienta)

    def seguirTrazo(self, casilla):
        # Pinta todas las casillas entre la anterior y la actual (para que no queden huecos al
        # mover rápido el ratón).
        boton, antes, ultima = self.trazo
        cambiado = False
        pasos = max(abs(casilla[0] - ultima[0]), abs(casilla[1] - ultima[1]), 1)
        for i in range(1, pasos + 1):
            punto = (ultima[0] + round((casilla[0] - ultima[0]) * i / pasos),
                     ultima[1] + round((casilla[1] - ultima[1]) * i / pasos))
            cambiado |= self.pintarEn(punto, boton)
        self.trazo = (boton, antes, casilla)
        if cambiado:
            self.mapaCambiado()

    def terminarTrazo(self):
        if self.trazo is not None and self.mapa.estado() != self.trazo[1]:
            self.guardarDeshacer(self.trazo[1])
        self.trazo = None

    # ---------- Eventos ----------
    def manejar(self, ev):
        if ev.type == pygame.QUIT:
            self.pedirSalir()
            return
        if ev.type == getattr(pygame, "DROPFILE", None):
            self.dialogo = None
            self.importar(ev.file)
            return
        if self.dialogo:
            self.manejarDialogo(ev)
            return
        self.calcularBotones()

        if ev.type == pygame.KEYDOWN:
            atajo = ev.mod & (pygame.KMOD_CTRL | pygame.KMOD_META)
            campo = next((c for c in self.campos if c.activo), None)
            if atajo and ev.key == pygame.K_z:
                self.hacerDeshacer()
            elif atajo and ev.key == pygame.K_o:
                self.abrirDialogo("importar")
            elif atajo and ev.key == pygame.K_s:
                self.abrirDialogo("exportar")
            elif campo is not None:
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.aplicarTamano()
                elif ev.key == pygame.K_BACKSPACE:
                    campo.texto = campo.texto[:-1]
                elif ev.key == pygame.K_TAB:
                    i = self.campos.index(campo)
                    campo.activo = False
                    self.campos[(i + 1) % 2].activo = True
                elif ev.key == pygame.K_ESCAPE:
                    campo.activo = False
                    campo.texto = str((self.mapa.ancho, self.mapa.alto)[self.campos.index(campo)])
            elif ev.key == pygame.K_ESCAPE:
                self.pedirSalir()
        elif ev.type == pygame.TEXTINPUT:
            campo = next((c for c in self.campos if c.activo), None)
            if campo is not None:
                campo.texto = (campo.texto + "".join(ch for ch in ev.text if ch.isdigit()))[:3]
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (1, 3):
            self.clic(ev.pos, ev.button)
        elif ev.type == pygame.MOUSEMOTION and self.trazo is not None:
            casilla = self.casillaEn(ev.pos)
            if casilla is not None:
                self.seguirTrazo(casilla)
        elif ev.type == pygame.MOUSEBUTTONUP and self.trazo is not None and ev.button == self.trazo[0]:
            self.terminarTrazo()

    def clic(self, pos, boton):
        for campo in self.campos:
            campo.activo = campo.rect.collidepoint(pos) and boton == 1
        if any(c.activo for c in self.campos):
            return
        if boton == 1:
            for i, (herramienta, etiqueta, _) in enumerate(ELEMENTOS):
                if self.rectElemento(i).collidepoint(pos):
                    self.herramienta = herramienta
                    self.avisar(f"Elemento: {etiqueta}.")
                    return
            for nombre, rect in self.botones.items():
                if rect.collidepoint(pos):
                    {"nuevo": self.nuevo, "importar": lambda: self.abrirDialogo("importar"),
                     "exportar": lambda: self.abrirDialogo("exportar"), "deshacer": self.hacerDeshacer,
                     "aplicar": self.aplicarTamano}[nombre]()
                    return
        casilla = self.casillaEn(pos)
        if casilla is not None:
            self.trazo = (boton, self.mapa.estado(), casilla)
            if self.pintarEn(casilla, boton):
                self.mapaCambiado()

    # ---------- Diálogos ----------
    def rectDialogo(self):
        alto = {"importar": 420, "corregir": 330}.get(self.dialogo, 200)
        rect = pygame.Rect(0, 0, 560 if self.dialogo == "corregir" else 520, alto)
        rect.center = self.pantalla.get_rect().center
        return rect

    def botonesDialogo(self):
        rect = self.rectDialogo()
        si = pygame.Rect(rect.right - 250, rect.bottom - 56, 110, 38)
        no = pygame.Rect(rect.right - 130, rect.bottom - 56, 110, 38)
        return si, no

    def filasLista(self):
        rect = self.rectDialogo()
        visibles = (rect.height - 130) // 30
        ficheros = self.ficherosNiveles()[self.desplazamientoLista:self.desplazamientoLista + visibles]
        return [(f, pygame.Rect(rect.x + 20, rect.y + 60 + i * 30, rect.width - 40, 28)) for i, f in enumerate(ficheros)]

    def manejarDialogo(self, ev):
        si, no = self.botonesDialogo()
        if self.dialogo == "corregir":
            if (ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER)) or \
                    (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and si.collidepoint(ev.pos)):
                self.corregirFichero()
            elif (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE) or \
                    (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and no.collidepoint(ev.pos)):
                self.noCorregirFichero()
            return
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self.dialogo = "exportar" if self.dialogo == "sobrescribir" else None
            return
        if self.dialogo == "importar":
            if ev.type == pygame.MOUSEWHEEL:
                maximo = max(0, len(self.ficherosNiveles()) - len(self.filasLista()))
                self.desplazamientoLista = min(maximo, max(0, self.desplazamientoLista - ev.y))
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for fichero, rect in self.filasLista():
                    if rect.collidepoint(ev.pos):
                        self.dialogo = None
                        self.importar(os.path.join(modelo.DIR_NIVELES, fichero))
                        return
                if no.collidepoint(ev.pos):
                    self.dialogo = None
        elif self.dialogo == "exportar":
            if ev.type == pygame.TEXTINPUT:
                self.textoFichero = (self.textoFichero + ev.text)[:60]
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_BACKSPACE:
                self.textoFichero = self.textoFichero[:-1]
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.confirmarExportar()
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if si.collidepoint(ev.pos):
                    self.confirmarExportar()
                elif no.collidepoint(ev.pos):
                    self.dialogo = None
        elif self.dialogo in ("sobrescribir", "salir"):
            acepta = (ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER)) or \
                     (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and si.collidepoint(ev.pos))
            cancela = ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and no.collidepoint(ev.pos)
            if acepta and self.dialogo == "sobrescribir":
                self.dialogo = None
                self.exportar(self.rutaExportar())
            elif acepta:
                self.salir = True
            elif cancela:
                self.dialogo = "exportar" if self.dialogo == "sobrescribir" else None

    # ---------- Dibujo ----------
    def icono(self, herramienta, tamano):
        clave = (herramienta, tamano)
        if clave in self.cacheCasillas:
            return self.cacheCasillas[clave]
        sup = pygame.Surface((tamano, tamano), pygame.SRCALPHA)
        fichero = next((f for h, _, f in ELEMENTOS if h == herramienta), None)
        imagen = None
        if fichero:
            if fichero not in self.iconos:
                try:
                    self.iconos[fichero] = pygame.image.load(os.path.join(modelo.DIR_RECURSOS, fichero))
                except (pygame.error, FileNotFoundError):
                    self.iconos[fichero] = None
            imagen = self.iconos[fichero]
        if herramienta in (SUELO, PARED):
            sup.fill(COLOR_SUELO if herramienta == SUELO else COLOR_PARED)
        elif imagen is not None:
            sup.blit(pygame.transform.smoothscale(imagen.convert_alpha() if pygame.display.get_surface() else imagen,
                                                  (tamano, tamano)), (0, 0))
        elif herramienta == "Door":
            ancho = max(2, tamano // 5)
            pygame.draw.rect(sup, (140, 90, 40), (tamano // 2 - ancho // 2, 1, ancho, tamano - 2))
            pygame.draw.circle(sup, (60, 40, 20), (tamano // 2, max(2, tamano // 6)), max(2, tamano // 6))
        elif herramienta == "Alarm":
            pygame.draw.circle(sup, (230, 20, 20), (tamano // 2, tamano // 2), max(2, tamano * 2 // 5))
            pygame.draw.circle(sup, (255, 150, 150), (tamano // 2 - tamano // 8, tamano // 2 - tamano // 8),
                               max(1, tamano // 8))
        elif herramienta == BORRAR:
            g = max(1, tamano // 8)
            pygame.draw.line(sup, (230, 60, 60), (3, 3), (tamano - 4, tamano - 4), g)
            pygame.draw.line(sup, (230, 60, 60), (tamano - 4, 3), (3, tamano - 4), g)
        else:
            sup.fill((200, 0, 200))
        self.cacheCasillas[clave] = sup
        return sup

    def pintarMapa(self):
        c = self.tamanoCasilla()
        sup = pygame.Surface((c * self.mapa.ancho, c * self.mapa.alto))
        sup.fill(COLOR_REJILLA)
        hueco = 1 if c >= 6 else 0
        for y, fila in enumerate(self.mapa.fondo):
            for x, tipo in enumerate(fila):
                sup.fill(COLOR_SUELO if tipo == SUELO else COLOR_PARED, (x * c, y * c, c - hueco, c - hueco))
        margen = 1 if c >= 8 else 0
        for (x, y), nombre in self.mapa.objetos.items():
            sup.blit(self.icono(nombre, c - 2 * margen), (x * c + margen, y * c + margen))
        if self.mapa.inicio is not None:
            x, y = self.mapa.inicio
            sup.blit(self.icono(INICIO, c - 2 * margen), (x * c + margen, y * c + margen))
        return sup

    def boton(self, rect, texto, elegido=False, color=None):
        encima = rect.collidepoint(pygame.mouse.get_pos())
        fondo = color or (BOTON_ELEGIDO if elegido else BOTON_ENCIMA if encima else BOTON)
        pygame.draw.rect(self.pantalla, fondo, rect, border_radius=5)
        etiqueta = self.fuente.render(texto, True, TEXTO)
        self.pantalla.blit(etiqueta, etiqueta.get_rect(center=rect.center))

    def textoEn(self, texto, pos, color=TEXTO, fuente=None, ancho=None):
        fuente = fuente or self.fuente
        if ancho is not None:
            while texto and fuente.size(texto)[0] > ancho:
                texto = texto[:-2] + "…" if len(texto) > 2 else ""
        self.pantalla.blit(fuente.render(texto, True, color), pos)

    def dibujar(self):
        self.calcularBotones()
        ancho, alto = self.pantalla.get_size()
        self.pantalla.fill(FONDO)

        # Barra superior: botones, nombre del fichero y tamaño (arriba a la derecha).
        pygame.draw.rect(self.pantalla, PANEL, (0, 0, ancho, ALTO_BARRA))
        self.textoEn("MazeMapCreator", (MARGEN, 20), BOTON_ENCIMA, self.fuenteTitulo)
        for nombre, texto in BOTONES_BARRA:
            self.boton(self.botones[nombre], texto)
        nombre = (os.path.basename(self.ruta) if self.ruta else "sin guardar") + (" *" if self.cambios else "")
        x = self.botones["deshacer"].right + 16
        self.textoEn(nombre, (x, 24), TEXTO_SUAVE, ancho=max(0, self.campos[0].rect.x - 40 - x))
        for campo in self.campos:
            self.textoEn(campo.etiqueta, (campo.rect.x - 20, 22))
            pygame.draw.rect(self.pantalla, COLOR_CAMPO, campo.rect, border_radius=4)
            pygame.draw.rect(self.pantalla, BOTON_ENCIMA if campo.activo else BOTON, campo.rect, 2, border_radius=4)
            texto = campo.texto + ("|" if campo.activo else "")
            self.textoEn(texto, (campo.rect.x + 10, campo.rect.y + 8))
        self.boton(self.botones["aplicar"], "Aplicar")

        # Columna izquierda: elementos.
        pygame.draw.rect(self.pantalla, PANEL, (0, ALTO_BARRA, ANCHO_PANEL, alto - ALTO_BARRA))
        for i, (herramienta, etiqueta, _) in enumerate(ELEMENTOS):
            rect = self.rectElemento(i)
            elegido = herramienta == self.herramienta
            encima = rect.collidepoint(pygame.mouse.get_pos())
            if elegido or encima:
                pygame.draw.rect(self.pantalla, BOTON_ELEGIDO if elegido else BOTON, rect, border_radius=5)
            self.pantalla.blit(self.icono(herramienta, 26), (rect.x + 6, rect.y + 4))
            self.textoEn(etiqueta, (rect.x + 42, rect.y + 8))

        # Centro: el mapa con su cuadrícula.
        rectMapa = self.rectMapa()
        # Se rehace al cambiar el mapa o el tamaño de la ventana (cambia el tamaño de casilla).
        if self.superficieMapa is None or self.superficieMapa.get_size() != rectMapa.size:
            self.superficieMapa = self.pintarMapa()
        self.pantalla.blit(self.superficieMapa, rectMapa)
        casilla = self.casillaEn(pygame.mouse.get_pos()) if not self.dialogo else None
        if casilla is not None:
            c = self.tamanoCasilla()
            pygame.draw.rect(self.pantalla, BOTON_ENCIMA, (rectMapa.x + casilla[0] * c, rectMapa.y + casilla[1] * c, c, c), 2)

        # Barra de estado: casilla, último mensaje y problemas para el juego.
        y = alto - ALTO_ESTADO
        pygame.draw.rect(self.pantalla, PANEL, (ANCHO_PANEL, y, ancho - ANCHO_PANEL, ALTO_ESTADO))
        posicion = f"Casilla ({casilla[0]}, {casilla[1]})" if casilla else f"{self.mapa.ancho}x{self.mapa.alto}"
        self.textoEn(posicion, (ANCHO_PANEL + MARGEN, y + 8), TEXTO_SUAVE, self.fuentePequena)
        self.textoEn(self.mensaje, (ANCHO_PANEL + 130, y + 8), self.colorMensaje, self.fuentePequena,
                     ancho=ancho - ANCHO_PANEL - 140)
        if self.problemas:
            texto, color = f"{len(self.problemas)} problema(s) para el juego: {self.problemas[0]}", COLOR_AVISO
        else:
            texto, color = "Nivel correcto para el juego.", COLOR_OK
        self.textoEn(texto, (ANCHO_PANEL + MARGEN, y + 32), color, self.fuentePequena, ancho=ancho - ANCHO_PANEL - 20)

        if self.dialogo:
            self.dibujarDialogo()

    def dibujarDialogo(self):
        velo = pygame.Surface(self.pantalla.get_size(), pygame.SRCALPHA)
        velo.fill((0, 0, 0, 150))
        self.pantalla.blit(velo, (0, 0))
        rect = self.rectDialogo()
        pygame.draw.rect(self.pantalla, PANEL, rect, border_radius=8)
        pygame.draw.rect(self.pantalla, BOTON_ENCIMA, rect, 2, border_radius=8)
        si, no = self.botonesDialogo()
        if self.dialogo == "importar":
            self.textoEn("Importar nivel de Levels/", (rect.x + 20, rect.y + 18), TEXTO, self.fuenteTitulo)
            for fichero, fila in self.filasLista():
                if fila.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(self.pantalla, BOTON_ENCIMA, fila, border_radius=4)
                self.textoEn(fichero, (fila.x + 10, fila.y + 4))
            if not self.ficherosNiveles():
                self.textoEn("No hay ficheros .json en Levels/", (rect.x + 20, rect.y + 64), TEXTO_SUAVE)
            self.textoEn("También puedes arrastrar un .json a la ventana.", (rect.x + 20, rect.bottom - 46),
                         TEXTO_SUAVE, self.fuentePequena)
            self.boton(no, "Cancelar")
        elif self.dialogo == "corregir":
            self.textoEn("Errores en las dimensiones", (rect.x + 20, rect.y + 18), COLOR_AVISO, self.fuenteTitulo)
            self.textoEn(f"{os.path.basename(self.ruta)}: mandan las casillas.", (rect.x + 20, rect.y + 56),
                         TEXTO_SUAVE, ancho=rect.width - 40)
            y = rect.y + 90
            lineas = [linea for error in self.erroresFichero[:5]
                      for linea in self.partirTexto("• " + error, self.fuente, rect.width - 40)]
            if len(self.erroresFichero) > 5:
                lineas.append(f"… y {len(self.erroresFichero) - 5} más")
            for linea in lineas[:6]:
                self.textoEn(linea, (rect.x + 20, y))
                y += 24
            self.textoEn("¿Corregirlo en el fichero? Sólo se cambia lo que está mal.",
                         (rect.x + 20, rect.bottom - 90), TEXTO, self.fuentePequena)
            self.boton(si, "Corregir")
            self.boton(no, "No")
        elif self.dialogo == "exportar":
            self.textoEn("Exportar a Levels/", (rect.x + 20, rect.y + 18), TEXTO, self.fuenteTitulo)
            campo = pygame.Rect(rect.x + 20, rect.y + 70, rect.width - 40, 38)
            pygame.draw.rect(self.pantalla, COLOR_CAMPO, campo, border_radius=4)
            pygame.draw.rect(self.pantalla, BOTON_ENCIMA, campo, 2, border_radius=4)
            self.textoEn(self.textoFichero + "|", (campo.x + 10, campo.y + 9))
            self.boton(si, "Exportar")
            self.boton(no, "Cancelar")
        else:
            if self.dialogo == "sobrescribir":
                titulo, detalle, texto = "¿Sobrescribir?", f"Ya existe {os.path.basename(self.rutaExportar())}.", "Sí"
            else:
                titulo, detalle, texto = "¿Salir?", "Hay cambios sin exportar.", "Salir"
            self.textoEn(titulo, (rect.x + 20, rect.y + 18), TEXTO, self.fuenteTitulo)
            self.textoEn(detalle, (rect.x + 20, rect.y + 70), TEXTO_SUAVE)
            self.boton(si, texto)
            self.boton(no, "Cancelar")

    @staticmethod
    def partirTexto(texto, fuente, ancho):
        # Parte el texto en líneas que quepan en 'ancho' (las siguientes, con sangría).
        lineas, actual = [], ""
        for palabra in texto.split():
            prueba = f"{actual} {palabra}" if actual else palabra
            if actual and fuente.size(prueba)[0] > ancho:
                lineas.append(actual)
                actual = "   " + palabra
            else:
                actual = prueba
        return lineas + [actual] if actual else lineas

    def actualizarTitulo(self):
        nombre = os.path.basename(self.ruta) if self.ruta else "sin guardar"
        pygame.display.set_caption(f"MazeMapCreator - {nombre}{' *' if self.cambios else ''}")

    def bucle(self):
        reloj = pygame.time.Clock()
        while not self.salir:
            for ev in pygame.event.get():
                self.manejar(ev)
            self.dibujar()
            self.actualizarTitulo()
            pygame.display.flip()
            reloj.tick(30)


def main(argumentos):
    pygame.init()
    pantalla = pygame.display.set_mode(TAMANO_VENTANA, pygame.RESIZABLE)
    editor = Editor(pantalla, argumentos[0] if argumentos else None)
    editor.bucle()
    pygame.quit()


if __name__ == "__main__":
    main(sys.argv[1:])
