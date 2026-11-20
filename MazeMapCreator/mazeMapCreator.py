"""
MazeMapCreator: editor gráfico de niveles para el juego (pygame-ce o pygame).

    python3 MazeMapCreator/mazeMapCreator.py [nivel.json]

  - Izquierda: elementos (suelo, pared, inicio del jugador, enemigo, puerta, oro...). Clic para elegir.
  - Centro: el mapa. Botón izquierdo pinta (se puede arrastrar); botón derecho quita el objeto
    de la casilla o, si no hay, pone pared.
  - Zoom con "-" / "+" (o Ctrl/Cmd + rueda, teclas - + y 0 para ajustar a la ventana). Si el mapa no
    cabe, se mueve con la rueda (Mayúsculas + rueda en horizontal), las flechas o arrastrando con el
    botón central: así se edita todo el nivel.
  - "Cámara" (tecla C): muestra lo que el juego ve a la vez (27x27 casillas). Clic o arrastrar en el
    mapa con Mayúsculas la centra en esa casilla y las flechas la mueven. Sólo se dibuja su borde: se
    sigue viendo y pintando todo el nivel.
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
ZOOM_MAXIMO = 48                 # píxeles por casilla con el zoom al máximo
PASO_RUEDA = 40                  # píxeles que se desplaza el mapa por cada paso de la rueda
GROSOR_BARRA = 6                 # barras de desplazamiento (sólo indican qué parte se ve)

FONDO = (38, 32, 44)
PANEL = (52, 44, 60)
BOTON = (90, 84, 100)
BOTON_ENCIMA = (255, 140, 0)
BOTON_ELEGIDO = (216, 75, 32)
TEXTO = (240, 240, 240)
TEXTO_SUAVE = (170, 165, 180)
COLOR_SUELO = (205, 195, 165)
COLOR_PARED = (150, 96, 70)            # ladrillo (no oscuro: no debe parecer una zona desactivada)
COLOR_JUNTA = (95, 60, 45)             # juntas entre los ladrillos
COLOR_REJILLA = (30, 26, 34)
COLOR_OK = (110, 210, 90)
COLOR_AVISO = (255, 170, 60)
COLOR_CAMPO = (25, 22, 30)
COLOR_CAMARA = (80, 200, 255)
COLOR_PUERTA_ANCHA = (255, 200, 60)

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
BOTONES_BARRA = [("nuevo", "Nuevo"), ("importar", "Importar"), ("exportar", "Exportar"), ("deshacer", "Deshacer"),
                 ("camara", "Cámara")]
BOTONES_ZOOM = [("zoomMenos", "-"), ("zoomMas", "+")]
FLECHAS = {pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1)}


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
        self.superficieMapa = None       # parte visible del mapa ya pintada (se rehace al cambiar)
        self.claveMapa = None            # (tamaño de casilla, posición, tamaño) de superficieMapa
        self.zoom = None                 # píxeles por casilla; None = ajustado a la ventana
        self.vista = [0, 0]              # desplazamiento (píxeles) del mapa cuando no cabe
        self.arrastrandoVista = False    # botón central pulsado
        self.verCamara = False           # muestra el borde de la cámara del juego (Mayúsculas+clic la mueve)
        self.camara = None               # esquina superior izquierda de la cámara, en casillas
        self.moviendoCamara = False
        self.problemas = self.mapa.problemas()
        self.botones = {}                # nombre -> Rect (los calcula dibujar)
        if ruta:
            self.importar(ruta)

    # ---------- Disposición ----------
    def zonaMapa(self):
        ancho, alto = self.pantalla.get_size()
        return pygame.Rect(ANCHO_PANEL + MARGEN, ALTO_BARRA + MARGEN,
                           max(10, ancho - ANCHO_PANEL - 2 * MARGEN), max(10, alto - ALTO_BARRA - ALTO_ESTADO - 2 * MARGEN))

    # Tamaño de casilla con el que el mapa entero cabe en la zona central.
    def tamanoAjustado(self):
        zona = self.zonaMapa()
        return max(2, min(zona.width // self.mapa.ancho, zona.height // self.mapa.alto))

    def tamanoCasilla(self):
        return self.zoom if self.zoom is not None else self.tamanoAjustado()

    def limitarVista(self):
        zona, c = self.zonaMapa(), self.tamanoCasilla()
        for i, (total, visible) in enumerate(((c * self.mapa.ancho, zona.width), (c * self.mapa.alto, zona.height))):
            self.vista[i] = max(0, min(self.vista[i], total - visible))

    # El mapa entero en la pantalla: centrado si cabe; si no, desplazado según self.vista (y sólo se
    # ve la parte que cae en zonaMapa()).
    def rectMapa(self):
        zona, c = self.zonaMapa(), self.tamanoCasilla()
        rect = pygame.Rect(0, 0, c * self.mapa.ancho, c * self.mapa.alto)
        rect.center = zona.center
        self.limitarVista()
        if rect.width > zona.width:
            rect.x = zona.x - self.vista[0]
        if rect.height > zona.height:
            rect.y = zona.y - self.vista[1]
        return rect

    def rectVisible(self):
        return self.rectMapa().clip(self.zonaMapa())

    def casillaEn(self, pos):
        rect = self.rectMapa()
        if not rect.clip(self.zonaMapa()).collidepoint(pos):
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
        for nombre, _ in BOTONES_ZOOM:
            b[nombre] = pygame.Rect(x, 14, 40, 36)
            x += 48
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
        if self.verCamara:
            self.limitarCamara()         # el mapa ha podido cambiar de tamaño o de suelo
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

    # ---------- Zoom, desplazamiento y cámara ----------
    def desplazar(self, dx, dy):
        self.vista[0] += round(dx)
        self.vista[1] += round(dy)
        self.limitarVista()

    # sentido > 0 acerca, < 0 aleja (como mucho hasta que el mapa entero cabe) y 0 ajusta a la ventana.
    # La casilla bajo 'ancla' (el ratón) se queda en el mismo sitio.
    def cambiarZoom(self, sentido, ancla=None):
        c, ajustado = self.tamanoCasilla(), self.tamanoAjustado()
        if sentido > 0:
            nuevo = min(max(ZOOM_MAXIMO, ajustado), max(c + 1, round(c * 1.25)))
        elif sentido < 0:
            nuevo = max(ajustado, min(c - 1, round(c / 1.25)))
        else:
            nuevo = ajustado
        if nuevo == c and (sentido or self.zoom is None):
            return False
        zona, rect = self.zonaMapa(), self.rectMapa()
        ancla = ancla if ancla is not None and rect.clip(zona).collidepoint(ancla) else rect.clip(zona).center
        fx, fy = (ancla[0] - rect.x) / c, (ancla[1] - rect.y) / c      # punto del mapa, en casillas
        self.zoom = None if nuevo <= ajustado else nuevo
        c = self.tamanoCasilla()
        self.vista = [round(zona.x + fx * c - ancla[0]), round(zona.y + fy * c - ancla[1])]
        self.limitarVista()
        self.superficieMapa = None
        self.avisar(f"Zoom: casillas de {c} px" + (" (todo el mapa)." if self.zoom is None else
                                                   ". Rueda, flechas o botón central para moverse."))
        return True

    # Desplaza la vista para que la casilla (x, y) quede en el centro de la zona del mapa.
    def centrarVistaEn(self, x, y):
        zona, c = self.zonaMapa(), self.tamanoCasilla()
        self.vista = [round((x + 0.5) * c - zona.width / 2), round((y + 0.5) * c - zona.height / 2)]
        self.limitarVista()

    def limitarCamara(self):
        if self.camara is not None:
            maxX, maxY = self.mapa.limitesCamara()
            self.camara = (max(0, min(self.camara[0], maxX)), max(0, min(self.camara[1], maxY)))

    def rectCamara(self):
        # La cámara en la pantalla (puede salirse del mapa: la rejilla del juego mide al menos 40x27).
        rect, c = self.rectMapa(), self.tamanoCasilla()
        return pygame.Rect(rect.x + self.camara[0] * c, rect.y + self.camara[1] * c,
                           modelo.CAMARA_ANCHO * c, modelo.CAMARA_ALTO * c)

    def avisarCamara(self):
        x, y = self.camara
        self.avisar(f"Cámara: columnas {x}-{x + modelo.CAMARA_ANCHO - 1}, filas {y}-{y + modelo.CAMARA_ALTO - 1}. "
                    f"Mayúsculas + clic (o arrastrar) la centra, flechas la mueven; C la oculta.", COLOR_CAMARA)

    def centrarCamara(self, casilla):
        self.camara = self.mapa.camaraCentradaEn(*casilla)
        self.avisarCamara()

    def moverCamara(self, dx, dy):
        self.camara = (self.camara[0] + dx, self.camara[1] + dy)
        self.limitarCamara()
        # Si se sale de lo que se ve, la vista la sigue.
        x, y = self.camara[0] + modelo.CAMARA_ANCHO // 2, self.camara[1] + modelo.CAMARA_ALTO // 2
        rect, c = self.rectMapa(), self.tamanoCasilla()
        if not self.zonaMapa().collidepoint(rect.x + x * c, rect.y + y * c):
            self.centrarVistaEn(x, y)
        self.avisarCamara()

    def alternarCamara(self):
        self.verCamara = not self.verCamara
        self.terminarTrazo()
        self.moviendoCamara = False
        if not self.verCamara:
            self.avisar("Cámara oculta.")
            return
        if self.camara is None:          # la primera vez, donde empieza el jugador (como en el juego)
            self.camara = self.mapa.camaraCentradaEn(*(self.mapa.inicio or (0, 0)))
        self.limitarCamara()
        self.avisarCamara()

    def verMapaNuevo(self):
        # Al abrir otro mapa: zoom ajustado, vista arriba a la izquierda y cámara en el inicio.
        self.zoom, self.vista, self.camara = None, [0, 0], None
        if self.verCamara:
            self.verCamara = False
            self.alternarCamara()

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
        self.verMapaNuevo()
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
        self.verMapaNuevo()
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
            elif ev.key == pygame.K_c:
                self.alternarCamara()
            elif ev.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                self.cambiarZoom(1, pygame.mouse.get_pos())
            elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.cambiarZoom(-1, pygame.mouse.get_pos())
            elif ev.key in (pygame.K_0, pygame.K_KP0):
                self.cambiarZoom(0)
            elif ev.key in FLECHAS:
                dx, dy = FLECHAS[ev.key]
                if self.verCamara:
                    paso = 5 if ev.mod & pygame.KMOD_SHIFT else 1
                    self.moverCamara(dx * paso, dy * paso)
                else:
                    paso = 3 * self.tamanoCasilla()
                    self.desplazar(dx * paso, dy * paso)
        elif ev.type == pygame.MOUSEWHEEL:
            mods = pygame.key.get_mods()
            if mods & (pygame.KMOD_CTRL | pygame.KMOD_META):
                if ev.y:
                    self.cambiarZoom(1 if ev.y > 0 else -1, pygame.mouse.get_pos())
            elif mods & pygame.KMOD_SHIFT:
                self.desplazar(-ev.y * PASO_RUEDA, 0)
            else:
                self.desplazar(ev.x * PASO_RUEDA, -ev.y * PASO_RUEDA)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 2:
            self.arrastrandoVista = self.zonaMapa().collidepoint(ev.pos)
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 2:
            self.arrastrandoVista = False
        elif ev.type == pygame.MOUSEMOTION and self.arrastrandoVista:
            self.desplazar(-ev.rel[0], -ev.rel[1])
        elif ev.type == pygame.MOUSEMOTION and self.moviendoCamara:
            casilla = self.casillaEn(ev.pos)
            if casilla is not None:
                self.centrarCamara(casilla)
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and self.moviendoCamara:
            self.moviendoCamara = False
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
                     "aplicar": self.aplicarTamano, "camara": self.alternarCamara,
                     "zoomMenos": lambda: self.cambiarZoom(-1), "zoomMas": lambda: self.cambiarZoom(1)}[nombre]()
                    return
        casilla = self.casillaEn(pos)
        # Con la cámara visible, Mayúsculas + clic la mueve; sin Mayúsculas se pinta como siempre.
        if casilla is not None and self.verCamara and boton == 1 and pygame.key.get_mods() & pygame.KMOD_SHIFT:
            self.moviendoCamara = True
            self.centrarCamara(casilla)
        elif casilla is not None:
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
        if herramienta == SUELO:
            sup.fill(COLOR_SUELO)
        elif herramienta == PARED:
            self.dibujarLadrillos(sup, tamano)
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

    # Pinta sólo la parte visible del mapa (con zoom, el mapa entero podría ser enorme).
    # Pared: ladrillos con sus juntas (si la casilla es muy pequeña, sólo el color).
    @staticmethod
    def dibujarLadrillos(sup, tamano):
        sup.fill(COLOR_PARED)
        if tamano < 8:
            return
        alto = max(3, tamano // 3)
        for fila, y in enumerate(range(0, tamano, alto)):
            pygame.draw.line(sup, COLOR_JUNTA, (0, y), (tamano - 1, y))
            desfase = 0 if fila % 2 == 0 else tamano // 2
            for x in (desfase, desfase + tamano // 2):
                if 0 < x < tamano:
                    pygame.draw.line(sup, COLOR_JUNTA, (x, y), (x, min(tamano - 1, y + alto - 1)))

    def pintarMapa(self, rect, visible):
        c = self.tamanoCasilla()
        sup = pygame.Surface(visible.size)
        sup.fill(COLOR_REJILLA)
        ox, oy = visible.x - rect.x, visible.y - rect.y        # esquina visible, en píxeles del mapa
        x0, y0 = ox // c, oy // c
        x1 = min(self.mapa.ancho, -(-(ox + visible.width) // c))
        y1 = min(self.mapa.alto, -(-(oy + visible.height) // c))
        hueco = 1 if c >= 6 else 0
        suelo, pared = self.icono(SUELO, c - hueco), self.icono(PARED, c - hueco)
        for y in range(y0, y1):
            fila = self.mapa.fondo[y]
            for x in range(x0, x1):
                sup.blit(suelo if fila[x] == SUELO else pared, (x * c - ox, y * c - oy))
        margen = 1 if c >= 8 else 0
        # Las puertas de 2 o 3 casillas se dibujan como una sola (más abajo).
        puertasAnchas = [g for g in self.mapa.puertas() if len(g) > 1]
        enPuertaAncha = {p for g in puertasAnchas for p in g}
        casillas = [(p, n) for p, n in self.mapa.objetos.items() if p not in enPuertaAncha]
        if self.mapa.inicio is not None:
            casillas.append((self.mapa.inicio, INICIO))
        for (x, y), nombre in casillas:
            if x0 <= x < x1 and y0 <= y < y1:
                sup.blit(self.icono(nombre, c - 2 * margen), (x * c + margen - ox, y * c + margen - oy))
        for grupo in puertasAnchas:
            if any(x0 <= x < x1 and y0 <= y < y1 for x, y in grupo):
                self.dibujarPuertaAncha(sup, grupo, c, ox, oy)
        return sup

    # Una puerta de 2 o 3 casillas: un marco alrededor de todas y una sola hoja que las cruza por la
    # mitad, con la bisagra en la primera (como en el juego).
    @staticmethod
    def dibujarPuertaAncha(sup, grupo, c, ox, oy):
        (x, y), horizontal = grupo[0], grupo[1][1] == grupo[0][1]
        largo = len(grupo) * c
        marco = pygame.Rect(x * c - ox, y * c - oy, largo if horizontal else c, c if horizontal else largo)
        grosor = max(2, c // 5)
        if horizontal:
            hoja = pygame.Rect(marco.x + 1, marco.centery - grosor // 2, marco.width - 2, grosor)
            bisagra = (marco.x + 2, marco.centery)
        else:
            hoja = pygame.Rect(marco.centerx - grosor // 2, marco.y + 1, grosor, marco.height - 2)
            bisagra = (marco.centerx, marco.y + 2)
        pygame.draw.rect(sup, (140, 90, 40), hoja)
        pygame.draw.circle(sup, (60, 40, 20), bisagra, max(2, c // 6))
        pygame.draw.rect(sup, COLOR_PUERTA_ANCHA, marco, max(2, c // 10))

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
        for nombre, texto in BOTONES_BARRA + BOTONES_ZOOM:
            self.boton(self.botones[nombre], texto, elegido=nombre == "camara" and self.verCamara)
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
        nombre = (os.path.basename(self.ruta) if self.ruta else "sin guardar") + (" *" if self.cambios else "")
        self.textoEn(nombre, (MARGEN, alto - 28), TEXTO_SUAVE, self.fuentePequena, ancho=ANCHO_PANEL - 2 * MARGEN)

        # Centro: el mapa con su cuadrícula.
        rectMapa, zona, c = self.rectMapa(), self.zonaMapa(), self.tamanoCasilla()
        visible = rectMapa.clip(zona)
        # Se rehace al cambiar el mapa, el zoom, la vista o el tamaño de la ventana.
        clave = (c, rectMapa.topleft, visible.size)
        if self.superficieMapa is None or self.claveMapa != clave:
            self.superficieMapa, self.claveMapa = self.pintarMapa(rectMapa, visible), clave
        self.pantalla.blit(self.superficieMapa, visible)
        self.dibujarBarras(rectMapa, zona)
        if self.verCamara and self.camara is not None:
            self.dibujarCamara(zona)
        casilla = self.casillaEn(pygame.mouse.get_pos()) if not self.dialogo else None
        if casilla is not None:
            self.pantalla.set_clip(zona)
            pygame.draw.rect(self.pantalla, COLOR_CAMARA if self.verCamara else BOTON_ENCIMA,
                             (rectMapa.x + casilla[0] * c, rectMapa.y + casilla[1] * c, c, c), 2)
            self.pantalla.set_clip(None)

        # Barra de estado: casilla, último mensaje y problemas para el juego.
        y = alto - ALTO_ESTADO
        pygame.draw.rect(self.pantalla, PANEL, (ANCHO_PANEL, y, ancho - ANCHO_PANEL, ALTO_ESTADO))
        posicion = f"Casilla ({casilla[0]}, {casilla[1]})" if casilla else f"{self.mapa.ancho}x{self.mapa.alto}"
        puerta = self.mapa.puertaEn(*casilla) if casilla else None
        if puerta:
            posicion += f" · puerta de {len(puerta)}"
        self.textoEn(posicion, (ANCHO_PANEL + MARGEN, y + 8), TEXTO_SUAVE, self.fuentePequena)
        x = max(ANCHO_PANEL + 130, ANCHO_PANEL + MARGEN + self.fuentePequena.size(posicion)[0] + 16)
        self.textoEn(self.mensaje, (x, y + 8), self.colorMensaje, self.fuentePequena,
                     ancho=max(0, ancho - x - MARGEN))
        if self.problemas:
            texto, color = f"{len(self.problemas)} problema(s) para el juego: {self.problemas[0]}", COLOR_AVISO
        else:
            texto, color = "Nivel correcto para el juego.", COLOR_OK
        self.textoEn(texto, (ANCHO_PANEL + MARGEN, y + 32), color, self.fuentePequena, ancho=ancho - ANCHO_PANEL - 20)

        if self.dialogo:
            self.dibujarDialogo()

    # Barras finas en el borde de la zona del mapa que indican qué parte se ve cuando no cabe.
    def dibujarBarras(self, rect, zona):
        if rect.width > zona.width:
            largo = max(20, zona.width * zona.width // rect.width)
            x = zona.x + (zona.x - rect.x) * (zona.width - largo) // (rect.width - zona.width)
            pygame.draw.rect(self.pantalla, BOTON, (x, zona.bottom + 2, largo, GROSOR_BARRA), border_radius=3)
        if rect.height > zona.height:
            largo = max(20, zona.height * zona.height // rect.height)
            y = zona.y + (zona.y - rect.y) * (zona.height - largo) // (rect.height - zona.height)
            pygame.draw.rect(self.pantalla, BOTON, (zona.right + 2, y, GROSOR_BARRA, largo), border_radius=3)

    # Recuadra la cámara del juego (sólo el borde: el resto del nivel se sigue viendo igual).
    def dibujarCamara(self, zona):
        camara = self.rectCamara()
        self.pantalla.set_clip(zona)
        pygame.draw.rect(self.pantalla, COLOR_CAMARA, camara, 3)
        etiqueta = self.fuentePequena.render(f"Cámara {modelo.CAMARA_ANCHO}x{modelo.CAMARA_ALTO}", True, COLOR_CAMARA)
        fondo = etiqueta.get_rect(topleft=(camara.x + 6, camara.y + 6)).inflate(8, 4)
        pygame.draw.rect(self.pantalla, COLOR_CAMPO, fondo)
        self.pantalla.blit(etiqueta, (camara.x + 6, camara.y + 6))
        self.pantalla.set_clip(None)

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
