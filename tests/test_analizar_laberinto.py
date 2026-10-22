import analizar_laberinto as al


def test_tamano_del_array():
    assert len(al.maze) == al.NUM_CASILLAS * al.NUM_CASILLAS


def test_analizar_laberinto_salida(capsys):
    al.analizar_laberinto()
    salida = capsys.readouterr().out
    assert "=== ANÁLISIS DEL LABERINTO ===" in salida
    assert f"Tamaño total del array: {len(al.maze)} elementos" in salida
    # Sólo hay un valor > 1 (un 2) en el array.
    assert "=== PAREDES ENCONTRADAS (1) ===" in salida
    # Una línea visual por cada fila.
    filas = [l for l in salida.splitlines() if l[:2].strip().isdigit() and l[2:3] == ":"]
    assert len(filas) == al.NUM_CASILLAS
