import pytest

import mates


@pytest.mark.parametrize("raton, esperado", [
    ((100, 100), True),    # esquina superior izquierda (borde incluido)
    ((330, 140), True),    # esquina inferior derecha (borde incluido)
    ((200, 120), True),    # dentro
    ((99, 120), False),    # a la izquierda
    ((331, 120), False),   # a la derecha
    ((200, 99), False),    # encima
    ((200, 141), False),   # debajo
])
def test_dentroBoton(raton, esperado):
    assert mates.dentroBoton(raton, 100, 100, 230, 40) is esperado
