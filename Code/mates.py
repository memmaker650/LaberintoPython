import logging
import os
import sys


# mates.py
# Modulo de operaciones matemáticas para el juego.
def dentroBoton(raton, centroX, centroY, largo, ancho):
    dentro = False

   # print("Dentro de mates")

    if centroX <= raton[0] <= centroX + largo:
        if centroY <= raton[1] <= centroY + ancho:
            return True

    return dentro
