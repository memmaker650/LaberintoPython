# MazeMapCreator

Editor gráfico de niveles para el juego, hecho con pygame-ce (también funciona con pygame).

```bash
pip install -r MazeMapCreator/requirements.txt
python3 MazeMapCreator/mazeMapCreator.py                      # mapa nuevo de 32x32
python3 MazeMapCreator/mazeMapCreator.py Levels/Level_0.json  # abre un nivel
```

- **Izquierda:** elementos (suelo, pared, inicio del jugador, enemigo, puerta, alarma, salida, llaves, oro...).
  Clic para elegir uno.
- **Centro:** el mapa con su cuadrícula.
  - Botón izquierdo: pinta (se puede arrastrar).
  - Botón derecho: quita el objeto de la casilla o, si no hay ninguno, pone pared.
  - Poner un objeto o el inicio sobre una pared la convierte en suelo.
- **Zoom (`-` / `+`):** también con Ctrl/Cmd + rueda y las teclas `-`, `+` y `0` (ver el mapa entero). Si el mapa
  no cabe en la ventana se mueve con la rueda (Mayúsculas + rueda en horizontal), las flechas o arrastrando con el
  botón central, así que se puede editar el nivel entero. Las barras finas del borde indican qué parte se ve.
- **Cámara (tecla C):** recuadra lo que el juego ve a la vez (27x27 casillas); sólo se dibuja el borde, así que se
  sigue viendo y pintando todo el nivel. En el juego la cámara sigue al jugador; aquí se coloca donde quieras:
  Mayúsculas + clic (o arrastrar) la centra en esa casilla y las flechas la mueven (Mayúsculas: de 5 en 5). No se sale
  del mundo, igual que en el juego (rejilla de al menos 40x27). C o el botón la ocultan.
- **Arriba a la derecha:** tamaño en casillas (X, Y) y **Aplicar**. Al cambiar el tamaño se conserva lo que cabe;
  las casillas nuevas son suelo y el borde nuevo, pared (el nivel sigue cerrado).
- **Nuevo:** mapa vacío con el tamaño de X e Y.
- **Importar / Exportar:** niveles JSON de la carpeta `Levels/`. También se puede arrastrar un `.json` a la ventana.
  Al exportar se escriben siempre los `tileNames` de `Level_0.json` y se conserva la `oscuridad` del nivel.
  La capa `Objects` se exporta repitiendo el fondo (`Floor`/`Wall`) donde no hay objeto. Al importar se
  avisa si no coincide con el fondo o si es un nivel antiguo con ceros.
- **Barra inferior:** avisa de los problemas que vería el juego (sin salida, suelo inalcanzable, borde abierto,
  más grande que 64x64...), con el mismo análisis que `Code/levels_parser.py`.
- **Atajos:** Ctrl/Cmd+Z deshacer, Ctrl/Cmd+O importar, Ctrl/Cmd+S exportar, C cámara, `-` `+` `0` zoom,
  ESC cierra un diálogo o sale.

Ficheros: `mapa.py` (el nivel y su JSON) y `mazeMapCreator.py` (la ventana). Tests: `tests/test_maze_map_creator.py`.
