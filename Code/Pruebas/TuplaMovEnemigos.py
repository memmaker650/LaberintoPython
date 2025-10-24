import time

eventos = []

# Simulamos bucle de juego
for i in range(5):
    # Registramos un valor cada iteración
    eventos.append((i * 10, time.time()))
    print(f"Añadido evento {i * 10}")
    time.sleep(1)

    # Eliminamos los que tengan más de 3 segundos
    ahora = time.time()
    eventos = [(v, t) for (v, t) in eventos if ahora - t < 3]

    print("Eventos activos:")
    for v, t in eventos:
        print(f"  Valor={v}, hace {ahora - t:.1f}s")
    print()
