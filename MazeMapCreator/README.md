# MazeMapCreator

Editor gráfico de niveles para el juego, hecho con pygame-ce (también funciona con pygame).

```bash
pip install -r MazeMapCreator/requirements.txt
python3 MazeMapCreator/maze_map_creator.py                      # mapa nuevo de 32x32
python3 MazeMapCreator/maze_map_creator.py Levels/Level_0.json  # abre un nivel
```

- **Izquierda:** elementos (suelo, pared, inicio del jugador, enemigo, puerta, alarma, salida, llaves, oro...).
  Clic para elegir uno.
- **Centro:** el mapa con su cuadrícula.
  - Botón izquierdo: pinta (se puede arrastrar).
  - Botón derecho: quita el objeto de la casilla o, si no hay ninguno, pone pared.
  - Poner un objeto o el inicio sobre una pared la convierte en suelo.
- **Arriba a la derecha:** tamaño en casillas (X, Y) y **Aplicar**. Al cambiar el tamaño se conserva lo que cabe;
  las casillas nuevas son pared.
- **Nuevo:** mapa vacío con el tamaño de X e Y.
- **Importar / Exportar:** niveles JSON de la carpeta `Levels/`. También se puede arrastrar un `.json` a la ventana.
  Al exportar se escriben siempre los `tileNames` de `Level_0.json` y se conserva la `oscuridad` del nivel.
- **Barra inferior:** avisa de los problemas que vería el juego (sin salida, suelo inalcanzable, borde abierto,
  más grande que 40x27...), con el mismo análisis que `Code/levels_parser.py`.
- **Atajos:** Ctrl/Cmd+Z deshacer, Ctrl/Cmd+O importar, Ctrl/Cmd+S exportar, ESC cierra un diálogo o sale.

Ficheros: `mapa.py` (el nivel y su JSON) y `maze_map_creator.py` (la ventana). Tests: `tests/test_maze_map_creator.py`.
