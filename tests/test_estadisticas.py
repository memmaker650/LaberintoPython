# Estadísticas del nivel (Code/estadisticas.py), mecánicas de combate que las alimentan,
# pantalla final (Game Over / Nivel completado) y guardado en la base de datos.
import os
import sqlite3

import pygame
import pytest

import Laberinto
import estadisticas
import player
from estadisticas import Estadisticas
from test_laberinto import Salida, app, enemigos_normales, lanzar, mover_jugador  # noqa: F401
from test_niveles import tandas, tecla, raton


# ================= Clase Estadisticas =================
def test_valores_iniciales():
    e = Estadisticas(jugador="Ana", nivel=3, inicio_ms=500)
    assert (e.jugador, e.nivel, e.inicio_ms) == ("Ana", 3, 500)
    assert (e.enemigosMuertos, e.balasDisparadas, e.impactos, e.huesos, e.monedasOro,
            e.heridas, e.vidaPerdida, e.puntos, e.tiempoSegundos, e.terminado) == (0, 0, 0, 0, 0, 0, 0, 0, 0.0, False)


def test_registrar():
    e = Estadisticas()
    for _ in range(4):
        e.registrarDisparo()
    e.registrarImpacto(enemigoMuerto=False)
    e.registrarImpacto(enemigoMuerto=True)
    e.registrarHerida(10)
    e.registrarHerida(20)
    e.registrarHuesos()
    e.registrarHuesos(10)
    e.registrarOro()
    e.registrarOro(2)
    assert (e.balasDisparadas, e.impactos, e.enemigosMuertos) == (4, 2, 1)
    assert (e.heridas, e.vidaPerdida, e.huesos, e.monedasOro) == (2, 30, 11, 3)


@pytest.mark.parametrize("balas, muertos, esperado, texto", [
    (0, 0, None, "Acierto en disparos: - (ningún disparo)"),
    (7, 2, 200 / 7, "Acierto en disparos: 28 % (2 muertes / 7 balas)"),   # ejemplo: 2/7 = 0,28
    (5, 0, 0.0, "Acierto en disparos: 0 % (0 muertes / 5 balas)"),
    (4, 2, 50.0, "Acierto en disparos: 50 % (2 muertes / 4 balas)"),
    (3, 3, 100.0, "Acierto en disparos: 100 % (3 muertes / 3 balas)"),
    (3, 2, 200 / 3, "Acierto en disparos: 66 % (2 muertes / 3 balas)"),   # truncado, no redondeado
])
def test_porcentaje_acierto(balas, muertos, esperado, texto):
    e = Estadisticas()
    e.balasDisparadas, e.enemigosMuertos = balas, muertos
    assert e.porcentajeAcierto == (None if esperado is None else pytest.approx(esperado))
    assert e.textoAcierto() == texto


def test_finalizar():
    e = Estadisticas(nivel=1, inicio_ms=2_000)
    e.finalizar(85_500, nivel=4, puntos=320)
    assert e.tiempoSegundos == 83.5
    assert (e.nivel, e.puntos, e.terminado) == (4, 320, True)
    e.finalizar(1_000)  # reloj por detrás del inicio: nunca negativo
    assert e.tiempoSegundos == 0.0 and e.nivel == 4


@pytest.mark.parametrize("segundos, texto", [(0, "00:00"), (59.9, "00:59"), (83.5, "01:23"), (3600, "60:00")])
def test_formatoTiempo(segundos, texto):
    assert Estadisticas.formatoTiempo(segundos) == texto


def test_lineas():
    e = Estadisticas()
    e.enemigosMuertos, e.balasDisparadas, e.impactos = 2, 8, 3
    e.huesos, e.monedasOro, e.heridas, e.vidaPerdida, e.tiempoSegundos = 12, 2, 4, 50, 95
    assert e.lineas() == [
        "Enemigos muertos: 2",
        "Balas usadas: 8",
        "Acierto en disparos: 25 % (2 muertes / 8 balas)",
        "Huesos recolectados: 12",
        "Monedas de oro: 2",
        "Tiempo: 01:35",
        "Heridas recibidas: 4 (-50 de vida)",
    ]


def test_comoFila():
    e = Estadisticas(jugador="Ana", nivel=2)
    e.balasDisparadas, e.enemigosMuertos = 7, 2
    fila = e.comoFila()
    assert list(fila) == estadisticas.COLUMNAS
    assert fila["porcentaje_acierto"] == 28.57
    e.balasDisparadas = 0
    assert e.comoFila()["porcentaje_acierto"] is None
    assert fila["jugador"] == "Ana" and fila["nivel"] == 2


# ================= Base de datos =================
def test_guardar_y_cargar(tmp_path):
    ruta = str(tmp_path / "bd.db")
    e = Estadisticas(jugador="Ana", nivel=2)
    e.enemigosMuertos, e.balasDisparadas, e.impactos, e.huesos, e.monedasOro = 3, 10, 4, 7, 1
    e.heridas, e.vidaPerdida, e.puntos = 2, 30, 450
    e.finalizar(61_000)
    assert e.guardar(ruta) == 1
    assert e.guardar(ruta) == 2
    filas = Estadisticas.cargarTodas(ruta)
    assert [f["id"] for f in filas] == [1, 2]
    f = filas[0]
    assert (f["jugador"], f["nivel"], f["enemigos_muertos"], f["balas_disparadas"], f["impactos"]) == ("Ana", 2, 3, 10, 4)
    assert (f["porcentaje_acierto"], f["huesos"], f["monedas_oro"]) == (30.0, 7, 1)
    assert (f["tiempo_segundos"], f["heridas"], f["vida_perdida"], f["puntos"]) == (61.0, 2, 30, 450)
    assert f["fecha"][:4].isdigit() and "T" in f["fecha"]


def test_guardar_sin_disparos(tmp_path):
    ruta = str(tmp_path / "bd.db")
    Estadisticas().guardar(ruta)
    assert Estadisticas.cargarTodas(ruta)[0]["porcentaje_acierto"] is None


def test_cargarTodas_bd_vacia(tmp_path):
    assert Estadisticas.cargarTodas(str(tmp_path / "vacia.db")) == []


def test_guardar_no_toca_las_tablas_existentes(tmp_path):
    # La BD del juego ya tiene una tabla 'estadisticas' antigua: se usa una tabla nueva.
    ruta = str(tmp_path / "juego.db")
    con = sqlite3.connect(ruta)
    con.execute("CREATE TABLE estadisticas (id interger PRIMARY KEY, jugador text NOT NULL, nivelmax integer NOT NULL)")
    con.commit()
    con.close()
    Estadisticas().guardar(ruta)
    con = sqlite3.connect(ruta)
    tablas = {n for n, in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"estadisticas", "estadisticas_nivel"} <= tablas
    assert con.execute("SELECT count(*) FROM estadisticas").fetchone() == (0,)
    con.close()


def test_guardar_cierra_la_conexion(tmp_path):
    ruta = str(tmp_path / "bd.db")
    Estadisticas().guardar(ruta)
    os.remove(ruta)  # en Windows fallaría si la conexión siguiera abierta
    assert not os.path.exists(ruta)


def test_bd_real_no_se_toca_en_los_tests(bd_de_prueba):
    assert Laberinto.RUTA_BD == bd_de_prueba
    assert "DB" not in os.path.dirname(bd_de_prueba).split(os.sep)[-1:]


# ================= Combate en el juego =================
@pytest.fixture
def juego(app):
    app.on_init()
    app.on_render()
    app.on_loop()
    return app


def test_partida_nueva_tiene_estadisticas(app):
    assert isinstance(app.estadisticas, Estadisticas)
    assert app.resultadoPartida is None
    assert app.JefeEnemigo.vida == Laberinto.VIDA_JEFE


def test_el_tiempo_empieza_al_jugar(app):
    app.tiempo_inicio = app.estadisticas.inicio_ms = -50_000
    app.on_init()
    ahora = pygame.time.get_ticks()
    assert ahora - app.tiempo_inicio < 1_000
    assert app.estadisticas.inicio_ms == app.tiempo_inicio


def test_herirJugador(juego):
    vida = juego.HeadBarraDeVida.vida
    assert juego.herirJugador(10) is True
    assert juego.HeadBarraDeVida.vida == vida - 10
    assert (juego.estadisticas.heridas, juego.estadisticas.vidaPerdida) == (1, 10)


def test_herirJugador_invulnerable_un_momento(juego):
    juego.herirJugador(10)
    assert juego.herirJugador(10) is False      # justo después: no cuenta
    assert juego.estadisticas.heridas == 1
    juego.ultimaHerida_ms -= Laberinto.TIEMPO_INVULNERABLE_MS
    assert juego.herirJugador(10) is True
    assert juego.estadisticas.heridas == 2


def test_herirJugador_hasta_morir(juego):
    juego.HeadBarraDeVida.vida = 15
    juego.herirJugador(20)
    assert juego.HeadBarraDeVida.vida == 0       # nunca negativa
    assert juego.resultadoPartida == "muerto"


def test_tocar_enemigo_hiere(juego):
    e = enemigos_normales(juego)[0]
    vida = juego.HeadBarraDeVida.vida
    mover_jugador(juego, e.x, e.y)
    juego.on_loop()
    assert juego.HeadBarraDeVida.vida == vida - Laberinto.DANO_ENEMIGO
    juego.on_loop()                               # sigue tocándolo: invulnerable
    assert juego.estadisticas.heridas == 1


def test_tocar_jefe_hiere_mas(juego):
    vida = juego.HeadBarraDeVida.vida
    mover_jugador(juego, juego.JefeEnemigo.x, juego.JefeEnemigo.y)
    juego.on_loop()
    assert juego.HeadBarraDeVida.vida == vida - Laberinto.DANO_JEFE


def test_bala_enemiga_hiere(juego):
    mover_jugador(juego, 40, Laberinto.BIAS + 40)
    juego.on_loop()
    bala = player.Disparos(juego.player.rect.x + 4, juego.player.rect.y + 2, False, 2)
    player.Enemigo.balas.add(bala)
    vida = juego.HeadBarraDeVida.vida
    juego.on_loop()
    assert juego.HeadBarraDeVida.vida == vida - Laberinto.DANO_BALA_ENEMIGA
    assert not player.Enemigo.balas.has(bala)


def disparar_a(app, enemigo):
    bala = player.Disparos(0, 300, True, 1)
    bala.rect.center = enemigo.rect.center
    app.player.balas.add(bala)
    app.player.flagDisparo = False  # que no se mueva antes de comprobar el impacto
    app.on_loop()
    return bala


def test_dos_balas_matan_a_un_enemigo(juego):
    e = enemigos_normales(juego)[0]
    puntos = juego.HeadPuntuacion.puntos
    bala = disparar_a(juego, e)
    assert not juego.player.balas.has(bala)       # la bala desaparece al acertar
    assert e.vida == 50 and e.alive()
    disparar_a(juego, e)
    assert e.vida == 0 and not e.alive() and e not in juego.EnemigosGroup
    assert (juego.estadisticas.impactos, juego.estadisticas.enemigosMuertos) == (2, 1)
    assert juego.HeadPuntuacion.puntos == puntos + Laberinto.PUNTOS_ENEMIGO


def test_enemigo_muerto_no_se_pinta_ni_hiere(juego):
    e = enemigos_normales(juego)[0]
    disparar_a(juego, e)
    disparar_a(juego, e)
    juego.on_render()
    mover_jugador(juego, e.x, e.y)
    vida = juego.HeadBarraDeVida.vida
    juego.on_loop()
    assert juego.HeadBarraDeVida.vida == vida


def test_jefe_necesita_mas_balas_y_al_morir_desaparece(juego):
    jefe = juego.JefeEnemigo
    for _ in range(Laberinto.VIDA_JEFE // Laberinto.DANO_BALA_JUGADOR - 1):
        disparar_a(juego, jefe)
    assert jefe.alive()
    puntos = juego.HeadPuntuacion.puntos
    disparar_a(juego, jefe)
    assert not jefe.alive()
    assert juego.HeadPuntuacion.puntos == puntos + Laberinto.PUNTOS_JEFE
    assert juego.estadisticas.enemigosMuertos == 1
    for _ in range(3):                              # el juego sigue sin el jefe
        juego.on_loop()
        juego.on_render()


def test_disparo_sin_municion_no_cuenta(app):
    app.player.municion = 0
    pygame.event.clear()
    for tipo, k in ((pygame.KEYDOWN, pygame.K_SPACE), (pygame.KEYDOWN, pygame.K_ESCAPE)):
        pygame.event.post(pygame.event.Event(tipo, key=k))
    with pytest.raises(SystemExit):
        app.on_execute()
    assert app.estadisticas.balasDisparadas == 0


def test_espacio_cuenta_las_balas(app):
    app.player.municion = 5
    pygame.event.clear()
    for _ in range(3):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    with pytest.raises(SystemExit):
        app.on_execute()
    assert app.estadisticas.balasDisparadas == 3


def coger(app, grupo):
    sprite = next(iter(grupo))
    mover_jugador(app, sprite.rect.x + 5, sprite.rect.y + 5)
    app.on_loop()


def test_huesos_y_oro_en_las_estadisticas(juego):
    coger(juego, juego.maze.MazeHueso)
    coger(juego, juego.maze.MazePilaHuesos)
    coger(juego, juego.maze.MazeOro)
    assert juego.estadisticas.huesos == 11
    assert juego.estadisticas.monedasOro == 1


def test_bandera_completa_el_nivel(juego):
    coger(juego, juego.maze.MazeBandera)
    assert juego.resultadoPartida == "completado"


def test_bandera_no_cambia_una_muerte(juego):
    juego.resultadoPartida = "muerto"
    coger(juego, juego.maze.MazeBandera)
    assert juego.resultadoPartida == "muerto"


# ================= Fin de partida =================
@pytest.fixture
def fin(monkeypatch, juego):
    # Sustituye la pantalla final y el menú para poder comprobar qué se muestra.
    mostrado = {}

    def pantalla(titulo, color, lineas, pie=""):
        mostrado.update(titulo=titulo, color=color, lineas=lineas, pie=pie)
    monkeypatch.setattr(juego, "pantallaFinal", pantalla)
    monkeypatch.setattr(juego, "menu", lambda: mostrado.setdefault("menu", True))
    return mostrado


def test_game_over_no_guarda(juego, fin, bd_de_prueba):
    juego.estadisticas.registrarDisparo()
    juego.terminarPartida(completado=False)
    assert fin["titulo"] == "GAME OVER" and fin["color"] == Laberinto.ROJO
    assert fin["lineas"][1] == "Balas usadas: 1"
    assert "sólo se guardan si terminas el nivel" in fin["pie"]
    assert Estadisticas.cargarTodas(bd_de_prueba) == []
    assert fin["menu"] is True


def test_nivel_completado_guarda(juego, fin, bd_de_prueba):
    juego.HeadNivel.definirNumeroNivel(3)
    juego.HeadPuntuacion.puntos = 250
    juego.estadisticas.registrarHuesos(4)
    juego.terminarPartida(completado=True)
    assert fin["titulo"] == "¡NIVEL COMPLETADO!" and fin["color"] == Laberinto.VERDE
    assert fin["pie"] == "Estadísticas guardadas en la base de datos."
    filas = Estadisticas.cargarTodas(bd_de_prueba)
    assert len(filas) == 1
    assert (filas[0]["nivel"], filas[0]["puntos"], filas[0]["huesos"]) == (3, 250, 4)
    assert filas[0]["jugador"] == "Memmaker650"


def test_nivel_completado_con_error_de_bd(monkeypatch, juego, fin, tmp_path):
    monkeypatch.setattr(Laberinto, "RUTA_BD", str(tmp_path))  # una carpeta: sqlite no la puede abrir
    juego.terminarPartida(completado=True)
    assert fin["pie"] == "No se han podido guardar las estadísticas."
    assert fin["menu"] is True


def test_fin_de_partida_reinicia(juego, fin):
    juego.HeadBarraDeVida.vida = 0
    juego.HeadPuntuacion.puntos = 99
    viejo_jugador, viejas = juego.player, juego.estadisticas
    juego.terminarPartida(completado=False)
    assert juego.HeadBarraDeVida.vida == 60
    assert juego.HeadPuntuacion.puntos == 0
    assert juego.player is not viejo_jugador
    assert juego.estadisticas is not viejas and juego.estadisticas.heridas == 0
    assert juego.resultadoPartida is None
    assert juego.tocaMenu is False


def test_on_execute_muerte_lleva_a_terminarPartida(monkeypatch, app):
    resultados = []

    def terminar(completado):
        resultados.append(completado)
        raise Salida("fin")
    monkeypatch.setattr(app, "terminarPartida", terminar)
    app.HeadBarraDeVida.vida = 5
    monkeypatch.setattr(app, "on_loop", lambda: app.herirJugador(10))
    pygame.event.clear()
    with pytest.raises(Salida):
        app.on_execute()
    assert resultados == [False]


def test_on_execute_salida_lleva_a_terminarPartida(monkeypatch, app):
    resultados = []
    monkeypatch.setattr(app, "terminarPartida", lambda c: resultados.append(c) or (_ for _ in ()).throw(Salida()))
    monkeypatch.setattr(app, "on_loop", lambda: setattr(app, "resultadoPartida", "completado"))
    pygame.event.clear()
    with pytest.raises(Salida):
        app.on_execute()
    assert resultados == [True]


# ================= Pantalla final =================
@pytest.mark.parametrize("evento", [tecla(pygame.K_RETURN), tecla(pygame.K_KP_ENTER), tecla(pygame.K_ESCAPE),
                                    raton((10, 10))])
def test_pantallaFinal_se_cierra(monkeypatch, app, evento):
    tandas(monkeypatch, [], [evento])
    assert app.pantallaFinal("GAME OVER", Laberinto.ROJO, ["a"]) is None


def test_pantallaFinal_ignora_otras_teclas(monkeypatch, app):
    tandas(monkeypatch, [tecla(pygame.K_LEFT), tecla(pygame.K_SPACE)], [tecla(pygame.K_RETURN)])
    app.pantallaFinal("GAME OVER", Laberinto.ROJO, ["a"])


def test_pantallaFinal_descarta_teclas_anteriores(app):
    # Un INTRO pulsado durante el juego no debe cerrar la pantalla antes de verla.
    pygame.event.post(tecla(pygame.K_RETURN))
    with pytest.raises(RuntimeError, match="nunca llegan"):
        app.pantallaFinal("GAME OVER", Laberinto.ROJO, ["a"])


def test_pantallaFinal_quit(monkeypatch, app):
    tandas(monkeypatch, [pygame.event.Event(pygame.QUIT)])
    with pytest.raises(SystemExit):
        app.pantallaFinal("GAME OVER", Laberinto.ROJO, ["a"])


def test_pantallaFinal_pinta_titulo_y_estadisticas(monkeypatch, app):
    monkeypatch.setattr(pygame.display, "update", lambda: (_ for _ in ()).throw(Salida("frame")))
    with pytest.raises(Salida):
        app.pantallaFinal("GAME OVER", Laberinto.ROJO, app.estadisticas.lineas(), "pie")
    rojos = [x for x in range(0, 864, 2) if app.pantalla.get_at((x, 190))[:3] == Laberinto.ROJO]
    assert rojos and min(rojos) > 100 and max(rojos) < 764      # título centrado
    for i in range(len(app.estadisticas.lineas())):
        y = 380 + i * 52
        assert any(app.pantalla.get_at((x, y))[:3] == (255, 255, 255) for x in range(200, 664))
