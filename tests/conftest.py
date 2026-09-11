import copy

import pytest

from dorkmount_patcher import firmware


@pytest.fixture
def synthetic(monkeypatch):
    stock = {name: bytes(range(80)) for name in firmware.COMPONENTS}
    output = {**stock, "dock": stock["dock"][:10] + b"OUR CODE" + stock["dock"][18:]}
    spec = {
        "components": {name: {"size": len(raw), "stock_filename": name + ".bin",
                               "stock_sha256": firmware.digest(raw),
                               "patched_sha256": firmware.digest(output[name])}
                       for name, raw in stock.items()},
        "patches": [{"component": "dock", "offset": 10, "length": 8,
                     "replacement_hex": b"OUR CODE".hex(),
                     "original_sha256": firmware.digest(stock["dock"][10:18]),
                     "replacement_sha256": firmware.digest(b"OUR CODE")}],
    }
    monkeypatch.setattr(firmware, "target", lambda: copy.deepcopy(spec))
    return stock, output, spec
