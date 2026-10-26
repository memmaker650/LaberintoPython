import json
import os

import pytest

from levels_parser import Layer, LevelData, LevelParser

LEVELS_DIR = os.path.join(os.path.dirname(__file__), "..", "Levels")


def datos_nivel(**cambios):
    datos = {
        "tileNames": ["Floor", "Wall"],
        "width": 3,
        "height": 2,
        "tileWidth": 32,
        "tileHeight": 32,
        "playerSpawnX": 1,
        "playerSpawnY": 0,
        "layers": [
            {"name": "Background", "tiles": [[1, 0, 1], [1, 1, 0]]},
            {"name": "Objects", "tiles": [[0, 2, 0], [0, 0, 3]]},
        ],
    }
    datos.update(cambios)
    return datos


@pytest.fixture
def dir_niveles(tmp_path):
    (tmp_path / "Level_1.json").write_text(json.dumps(datos_nivel()), encoding="utf-8")
    (tmp_path / "Level_2.json").write_text(json.dumps(datos_nivel(width=1, layers=[
        {"name": "Background", "tiles": [[1], [1]]}])), encoding="utf-8")
    (tmp_path / "otro.json").write_text("{}", encoding="utf-8")
    return tmp_path


@pytest.fixture
def nivel(dir_niveles):
    return LevelParser(str(dir_niveles)).load_by_name("Level_1.json")


# ---------- LevelData ----------
def test_campos_basicos(nivel):
    assert nivel.width == 3 and nivel.height == 2
    assert nivel.tileNames == ["Floor", "Wall"]
    assert (nivel.playerSpawnX, nivel.playerSpawnY) == (1, 0)
    assert [l.name for l in nivel.layers] == ["Background", "Objects"]


def test_get_layer(nivel):
    assert nivel.get_layer("Objects").tiles == [[0, 2, 0], [0, 0, 3]]
    assert nivel.get_layer("NoExiste") is None


def test_tiles_iter(nivel):
    assert list(nivel.tiles_iter("Background")) == [
        (0, 0, 1), (0, 1, 0), (0, 2, 1),
        (1, 0, 1), (1, 1, 1), (1, 2, 0),
    ]
    assert list(nivel.tiles_iter("NoExiste")) == []


@pytest.mark.parametrize("x, y, esperado", [
    (1, 0, 2), (2, 1, 3), (3, 0, None), (0, 2, None), (-1, 0, None),
])
def test_get_tile(nivel, x, y, esperado):
    assert nivel.get_tile("Objects", x, y) == esperado


def test_get_tile_layer_inexistente(nivel):
    assert nivel.get_tile("NoExiste", 0, 0) is None


def test_debug_layers(nivel, capsys):
    nivel.debug_layers()
    salida = capsys.readouterr().out
    assert "Level: Level_1.json" in salida
    assert "Total layers: 2" in salida
    assert " 1  0  1" in salida


def _level(**cambios):
    base = dict(path="x", tileNames=["F"], width=2, height=1, tileWidth=32, tileHeight=32,
                playerSpawnX=0, playerSpawnY=0, layers=[Layer("B", [[1, 0]])])
    base.update(cambios)
    return LevelData(**base)


def test_validate_ok():
    _level().validate()


@pytest.mark.parametrize("cambios, mensaje", [
    (dict(width=None), "Faltan claves"),
    (dict(width=0), "width/height"),
    (dict(tileWidth=0), "tileWidth/tileHeight"),
    (dict(layers=[]), "al menos un layer"),
    (dict(layers=[Layer("", [[1, 0]])]), "name"),
    (dict(layers=[Layer("B", [[1, 0], [1, 0]])]), "filas"),
    (dict(layers=[Layer("B", [[1]])]), "columnas"),
    (dict(layers=[Layer("B", [[1, -1]])]), "Tile inválido"),
    (dict(layers=[Layer("B", [[1, "a"]])]), "Tile inválido"),
])
def test_validate_errores(cambios, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        _level(**cambios).validate()


# ---------- LevelParser ----------
def test_list_level_files(dir_niveles):
    parser = LevelParser(str(dir_niveles))
    nombres = [os.path.basename(p) for p in parser.list_level_files()]
    assert nombres == ["Level_1.json", "Level_2.json"]
    assert len(parser.list_level_files("*.json")) == 3


def test_load_usa_cache(dir_niveles):
    parser = LevelParser(str(dir_niveles))
    primero = parser.load_by_name("Level_1.json")
    segundo = parser.load(str(dir_niveles / "Level_1.json"))
    assert primero is segundo


def test_load_all(dir_niveles):
    niveles = LevelParser(str(dir_niveles)).load_all()
    assert [n.width for n in niveles] == [3, 1]


def test_load_fichero_inexistente(dir_niveles):
    with pytest.raises(FileNotFoundError):
        LevelParser(str(dir_niveles)).load_by_name("Level_99.json")


def test_load_json_invalido(tmp_path):
    (tmp_path / "Level_1.json").write_text("{ no es json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        LevelParser(str(tmp_path)).load_by_name("Level_1.json")


def test_load_nivel_invalido(tmp_path):
    (tmp_path / "Level_1.json").write_text(json.dumps(datos_nivel(height=5)), encoding="utf-8")
    with pytest.raises(ValueError):
        LevelParser(str(tmp_path)).load_by_name("Level_1.json")


def test_niveles_reales_son_validos():
    niveles = LevelParser(LEVELS_DIR).load_all()
    assert len(niveles) == 6
    for n in niveles:
        assert n.get_layer("Background") is not None
        assert n.get_layer("Objects") is not None
