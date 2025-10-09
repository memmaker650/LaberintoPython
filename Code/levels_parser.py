from __future__ import annotations

import json
import os
from dataclasses import dataclass
from glob import glob
from typing import Any, Dict, List, Optional, Iterable


@dataclass
class Layer:
    name: str
    tiles: List[List[int]]  # filas -> columnas


@dataclass
class LevelData:
    path: str
    tileNames: List[str]
    width: int
    height: int
    tileWidth: int
    tileHeight: int
    playerSpawnX: int
    playerSpawnY: int
    layers: List[Layer]

    def get_layer(self, name: str) -> Optional[Layer]:
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None

    def tiles_iter(self, layer_name: str) -> Iterable[tuple[int, int, int]]:
        layer = self.get_layer(layer_name)
        if not layer:
            return
        for y, row in enumerate(layer.tiles):
            for x, tile_id in enumerate(row):
                yield (y, x, tile_id)

    def get_tile(self, layer_name: str, x: int, y: int) -> Optional[int]:
        layer = self.get_layer(layer_name)
        if not layer:
            return None
        if 0 <= y < len(layer.tiles) and 0 <= x < len(layer.tiles[y]):
            return layer.tiles[y][x]
        return None

    def validate(self) -> None:
        required = [
            "tileNames", "width", "height", "tileWidth", "tileHeight",
            "playerSpawnX", "playerSpawnY", "layers"
        ]
        missing = [k for k in required if getattr(self, k, None) is None]
        if missing:
            raise ValueError(f"Faltan claves requeridas: {missing}")

        if self.width <= 0 or self.height <= 0:
            raise ValueError("width/height deben ser > 0")
        if self.tileWidth <= 0 or self.tileHeight <= 0:
            raise ValueError("tileWidth/tileHeight deben ser > 0")

        if not self.layers:
            raise ValueError("Debe existir al menos un layer")

        for layer in self.layers:
            if not isinstance(layer.name, str) or not layer.name:
                raise ValueError("Cada layer debe tener 'name' no vacío")
            if not isinstance(layer.tiles, list) or len(layer.tiles) != self.height:
                raise ValueError(
                    f"Layer '{layer.name}' debe tener {self.height} filas; tiene {len(layer.tiles)}"
                )
            for y, row in enumerate(layer.tiles):
                if not isinstance(row, list) or len(row) != self.width:
                    raise ValueError(
                        f"Layer '{layer.name}' fila {y} debe tener {self.width} columnas; tiene {len(row)}"
                    )
                for x, v in enumerate(row):
                    if not isinstance(v, int) or v < 0:
                        raise ValueError(
                            f"Tile inválido en layer '{layer.name}' ({y},{x}): {v}"
                        )


class LevelParser:
    def __init__(self, levels_dir: str) -> None:
        self.levels_dir = os.path.abspath(levels_dir)
        self._cache: Dict[str, LevelData] = {}

    def list_level_files(self, pattern: str = "Level_*.json") -> List[str]:
        return sorted(glob(os.path.join(self.levels_dir, pattern)))

    def load_all(self) -> List[LevelData]:
        files = self.list_level_files()
        return [self.load(path) for path in files]

    def load(self, path: str) -> LevelData:
        abs_path = os.path.abspath(path)
        if abs_path in self._cache:
            return self._cache[abs_path]

        with open(abs_path, "r", encoding="utf-8") as f:
            raw: Dict[str, Any] = json.load(f)

        level = self._from_raw(abs_path, raw)
        level.validate()
        self._cache[abs_path] = level
        return level

    def load_by_name(self, filename: str) -> LevelData:
        return self.load(os.path.join(self.levels_dir, filename))

    def _from_raw(self, path: str, raw: Dict[str, Any]) -> LevelData:
        tile_names = list(raw.get("tileNames", []))
        width = int(raw.get("width", 0))
        height = int(raw.get("height", 0))
        tile_w = int(raw.get("tileWidth", 0))
        tile_h = int(raw.get("tileHeight", 0))
        spawn_x = int(raw.get("playerSpawnX", 0))
        spawn_y = int(raw.get("playerSpawnY", 0))

        layers_raw = raw.get("layers", [])
        layers: List[Layer] = []
        for lr in layers_raw:
            name = str(lr.get("name", ""))
            tiles = lr.get("tiles", [])
            tiles_norm: List[List[int]] = [list(row) for row in tiles]
            layers.append(Layer(name=name, tiles=tiles_norm))

        return LevelData(
            path=path,
            tileNames=tile_names,
            width=width,
            height=height,
            tileWidth=tile_w,
            tileHeight=tile_h,
            playerSpawnX=spawn_x,
            playerSpawnY=spawn_y,
            layers=layers,
        )