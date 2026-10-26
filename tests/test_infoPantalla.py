import pytest

import infoPantalla


# ---------- barraDeVida ----------
def test_barraDeVida_valor_inicial():
    assert infoPantalla.barraDeVida().vida == 60


def test_barraDeVida_crear_superficie():
    barra = infoPantalla.barraDeVida()
    barra.vida = 50
    barra.crearBarraDeVida()
    sup = barra.spriteBarraDeVida
    assert sup.get_size() == (200, 50)
    # Parte rellena (vida*2 = 100 px) en rojo, resto en gris.
    assert sup.get_at((50, 25))[:3] == (255, 0, 0)
    assert sup.get_at((150, 25))[:3] == (100, 100, 100)
    # Borde blanco.
    assert sup.get_at((0, 0))[:3] == (255, 255, 255)


def test_barraDeVida_conversionTexto():
    barra = infoPantalla.barraDeVida()
    barra.vida = 85
    barra.conversionTexto()
    assert barra.textoVida == "85"


# ---------- panelPuntuacion ----------
def test_panelPuntuacion_inicial():
    panel = infoPantalla.panelPuntuacion()
    assert panel.puntos == 0
    assert panel.textoPuntos == "000000"


def test_panelPuntuacion_conversionTexto_rellena_ceros():
    panel = infoPantalla.panelPuntuacion()
    panel.puntos = 150
    panel.conversionTexto()
    assert panel.textoPuntos == "000150"


def test_panelPuntuacion_incrementarPuntos():
    panel = infoPantalla.panelPuntuacion()
    panel.incrementarPuntos(10)
    assert panel.puntos == 10


def test_panelPuntuacion_restarPuntos():
    panel = infoPantalla.panelPuntuacion()
    panel.puntos = 30
    panel.restarPuntos(10)
    assert panel.puntos == 20


def test_panelPuntuacion_reiniciarPuntos():
    panel = infoPantalla.panelPuntuacion()
    panel.puntos = 30
    panel.reiniciarPuntos(0)
    assert panel.puntos == 0


# ---------- infoNivel / infoHuesos / infoItems ----------
def test_infoNivel():
    nivel = infoPantalla.infoNivel()
    assert (nivel.NumeroNivel, nivel.textoNivel) == (1, "1")
    nivel.definirNumeroNivel(4)
    nivel.conversionTexto()
    assert nivel.textoNivel == "4"


def test_infoHuesos():
    huesos = infoPantalla.infoHuesos()
    assert (huesos.NumeroHuesos, huesos.textoHuesos) == (0, "0")
    huesos.definirNumeroNivel(12)
    huesos.conversionTexto()
    assert huesos.textoHuesos == "12"


def test_infoItems_definirNumeroNivel():
    items = infoPantalla.infoItems()
    items.definirNumeroNivel(3)
    assert items.NumeroNivel == 3


# ---------- relojPantalla ----------
def test_reloj_inicial():
    reloj = infoPantalla.relojPantalla()
    assert reloj.tiempoInteger == 90
    assert reloj.textoReloj == "90"
    assert reloj.flagTerminado is False


def test_reloj_cuentaTiempo_y_cambioSegundo():
    reloj = infoPantalla.relojPantalla()
    reloj.cuentaTiempo(0.5)
    assert reloj.tiempoActual == 89.5
    reloj.cambioSegundo()
    assert reloj.tiempoInteger == 89
    reloj.conversionTexto()
    assert reloj.textoReloj == "89"


def test_reloj_cambioSegundo_sin_cambio():
    reloj = infoPantalla.relojPantalla()
    reloj.cambioSegundo()
    assert reloj.tiempoInteger == 90


# ---------- infoArmasMunicion ----------
def test_armas_inicial():
    armas = infoPantalla.infoArmasMunicion()
    assert armas.armaSeleccionada == 4
    assert armas.Armas == [False, False, False, False, True, False]
    assert armas.municion == [1, 0, 0, 0, 0, 0]


def test_armas_update_marca_arma_y_municion():
    armas = infoPantalla.infoArmasMunicion()
    armas.armaSeleccionada = 2
    armas.municionArmaSeleccionada = 7
    armas.update()
    assert armas.Armas == [False, True, False, False, False, False]
    assert armas.municion[1] == 7


@pytest.mark.parametrize("arma, nombre", [
    (1, "Cuchillo"), (2, "Pistola"), (3, "Metralleta"),
    (4, "Granada"), (5, "Laser"), (6, "Bomba Humo"),
])
def test_armas_conversionTexto(arma, nombre):
    armas = infoPantalla.infoArmasMunicion()
    armas.armaSeleccionada = arma
    armas.municion[arma - 1] = arma * 10
    armas.conversionTexto()
    assert armas.textoArma == nombre
    assert armas.textoMunicion == str(arma * 10)


def test_armas_definirMunicion():
    armas = infoPantalla.infoArmasMunicion()
    armas.definirMunicion(2, 15)
    assert armas.municion[2] == 15


def test_armas_incrementarMunicion():
    armas = infoPantalla.infoArmasMunicion()
    armas.municion[0] = 5
    armas.incrementarMunicion(0, 10)
    assert armas.municion[0] == 15


def test_armas_gastarMunicion():
    armas = infoPantalla.infoArmasMunicion()
    armas.municion[0] = 5
    armas.gastarMunicion(0)
    assert armas.municion[0] == 4
