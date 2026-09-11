import copy
import json
from dataclasses import FrozenInstanceError
from importlib.resources import files
from pathlib import Path

import pytest

from dorkmount_patcher import firmware

ROOT = Path(__file__).resolve().parents[1]


def test_patch_exact_ranges_immutable_and_numpad_unchanged(synthetic):
    stock, output, _ = synthetic
    package = firmware.prepare(stock)
    assert dict(package.images) == output
    assert package.images["numpad"] == stock["numpad"]
    with pytest.raises(TypeError):
        package.images["dock"] = b"changed"
    with pytest.raises(FrozenInstanceError):
        package.mode = "stock"
    stock["main"] = b"changed"
    package.verify()


@pytest.mark.parametrize("name", firmware.COMPONENTS)
def test_unknown_input_rejected(synthetic, name):
    stock, _, _ = synthetic
    stock[name] = b"x" * len(stock[name])
    with pytest.raises(ValueError, match="exact supported"):
        firmware.prepare(stock)


@pytest.mark.parametrize("field,value", [
    ("offset", -1), ("offset", 100), ("length", 0),
    ("replacement_hex", "00"), ("original_sha256", "00"), ("replacement_sha256", "00")])
def test_bad_patch_metadata_rejected(synthetic, field, value):
    stock, _, spec = synthetic
    spec["patches"][0][field] = value
    with pytest.raises(ValueError):
        firmware.prepare(stock)


def test_overlap_refused(synthetic):
    stock, _, spec = synthetic
    spec["patches"].append(copy.deepcopy(spec["patches"][0]))
    with pytest.raises(ValueError, match="Overlapping"):
        firmware.prepare(stock)


def test_stock_restore_exact_and_output_directory_not_overwritten(synthetic, tmp_path):
    stock, _, _ = synthetic
    package = firmware.prepare(stock, restore=True)
    out = tmp_path / "new"
    firmware.export(package, out)
    assert all((out / f"{name}-stock.bin").read_bytes() == raw for name, raw in stock.items())
    with pytest.raises(FileExistsError):
        firmware.export(package, out)


def test_payload_metadata_matches_original_target_and_source():
    spec = firmware.target()
    original = json.loads((ROOT / "firmware/targets/1.29.0-dmr2.json").read_text())
    assert spec["components"] == original["components"]
    for region, source in zip(spec["patches"], original["patches"], strict=True):
        assert {key: region[key] for key in source} == source
        raw = bytes.fromhex(region["replacement_hex"])
        assert len(raw) == region["length"]
        assert firmware.digest(raw) == region["replacement_sha256"]
    for filename, sha in spec["source_sha256"].items():
        assert firmware.digest((ROOT / filename).read_bytes()) == sha


def test_download_failure_exports_no_unverified_firmware(synthetic, tmp_path):
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, count):
            return b"wrong firmware"
    class Opener:
        def open(self, *args, **kwargs):
            return Response()
    with pytest.raises(ValueError, match="verification"):
        firmware.obtain_originals(tmp_path, opener=Opener())
    assert list(tmp_path.iterdir()) == []


def test_valid_cache_used_without_network(synthetic, tmp_path):
    stock, _, _ = synthetic
    for name, raw in stock.items():
        (tmp_path / (name + ".bin")).write_bytes(raw)
    class NoNetwork:
        def open(self, *args, **kwargs):
            raise AssertionError("Unexpected download")
    assert firmware.obtain_originals(tmp_path, opener=NoNetwork()) == stock


def test_bundled_offline_developer_guide_matches_canonical_document():
    assert files("dorkmount_patcher").joinpath("data/developers.md").read_text() == (
        ROOT / "docs/DEVELOPERS.md"
    ).read_text()
