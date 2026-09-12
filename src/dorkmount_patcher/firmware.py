"""Exact-image patching. No compiler, device access or manufacturer bytes bundled."""

import hashlib
import json
import os
import tempfile
import urllib.request
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from types import MappingProxyType

from .https import verified_context

BASE_URL = "https://dfu-release.bequiet.com/fw/dark_mount/"
COMPONENTS = ("main", "dock", "numpad")
DEFAULT_EXTENSION = "dmr3"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def target(extension=DEFAULT_EXTENSION):
    if extension not in ("dmr2", "dmr3"):
        raise ValueError("Unsupported firmware extension.")
    return json.loads(files(__package__).joinpath(f"data/{extension}.json").read_text())


def checked_images(images, mode="stock"):
    if mode not in ("stock", "dmr2", "dmr3") or set(images) != set(COMPONENTS):
        raise ValueError("A complete supported firmware set is required.")
    metadata = target(DEFAULT_EXTENSION if mode == "stock" else mode)["components"]
    for name in COMPONENTS:
        raw, expected = images[name], metadata[name]
        key = "stock_sha256" if mode == "stock" else "patched_sha256"
        if not isinstance(raw, bytes) or len(raw) != expected["size"] or digest(raw) != expected[key]:
            raise ValueError(f"The {name} file is not the exact supported {mode} firmware.")


@dataclass(frozen=True)
class Package:
    """Immutable image bytes, rechecked at the update boundary."""

    stock: object
    images: object
    mode: str

    def __post_init__(self):
        object.__setattr__(self, "stock", MappingProxyType(dict(self.stock)))
        object.__setattr__(self, "images", MappingProxyType(dict(self.images)))
        self.verify()

    def verify(self):
        checked_images(self.stock)
        checked_images(self.images, self.mode)


def prepare(originals, restore=False, extension=DEFAULT_EXTENSION):
    checked_images(originals)
    if restore:
        return Package(originals, originals, "stock")
    spec = target(extension)
    candidates = {name: bytearray(originals[name]) for name in COMPONENTS}
    occupied = {name: [] for name in COMPONENTS}
    # Validate every region before applying even the first patch.
    for region in spec["patches"]:
        name, start, size = region["component"], region["offset"], region["length"]
        end = start + size
        data = bytes.fromhex(region["replacement_hex"])
        if start < 0 or size <= 0 or end > len(candidates[name]) or len(data) != size:
            raise ValueError("Invalid patch extent.")
        if any(start < b and end > a for a, b in occupied[name]):
            raise ValueError("Overlapping patches.")
        if digest(originals[name][start:end]) != region["original_sha256"]:
            raise ValueError("Original patch bytes differ.")
        if digest(data) != region["replacement_sha256"]:
            raise ValueError("Bundled extension bytes differ.")
        occupied[name].append((start, end))
    for region in spec["patches"]:
        start = region["offset"]
        candidates[region["component"]][start:start + region["length"]] = bytes.fromhex(
            region["replacement_hex"]
        )
    return Package(originals, {name: bytes(raw) for name, raw in candidates.items()}, extension)


def private_directory(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def atomic_write(path, data):
    path = Path(path)
    private_directory(path.parent)
    fd, temporary = tempfile.mkstemp(prefix=".writing-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class OfficialOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.startswith(BASE_URL):
            raise ValueError("The firmware download redirected outside the official source.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def obtain_originals(directory, progress=lambda text: None, opener=None):
    """Download fixed filenames only; never auto-select a newer firmware release."""
    directory = private_directory(directory)
    images = {}
    for name, item in target()["components"].items():
        path = directory / item["stock_filename"]
        progress(f"Preparing {dict(main='keyboard', dock='screen', numpad='number pad')[name]}…")
        raw = path.read_bytes() if path.is_file() else None
        if raw is None or len(raw) != item["size"] or digest(raw) != item["stock_sha256"]:
            if opener is None:
                opener = urllib.request.build_opener(
                    OfficialOnly(), urllib.request.HTTPSHandler(context=verified_context()))
            request = urllib.request.Request(BASE_URL + item["stock_filename"], headers={
                "User-Agent": "Dorkmount-patcher/0.2 (local firmware preparation)"
            })
            with opener.open(request, timeout=30) as response:
                raw = response.read(item["size"] + 1)
            if len(raw) != item["size"] or digest(raw) != item["stock_sha256"]:
                raise ValueError("The downloaded firmware did not pass verification. Nothing installed.")
            atomic_write(path, raw)
        images[name] = raw
    checked_images(images)
    return images


def export(package, directory):
    package.verify()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    for name in COMPONENTS:
        atomic_write(directory / f"{name}-stock.bin", package.stock[name])
        atomic_write(directory / f"{name}-{package.mode}.bin", package.images[name])
    record = {"mode": package.mode, "target": f"darkmount-1.29.0-{package.mode}", "images": {
        name: {"size": len(package.images[name]), "sha256": digest(package.images[name])}
        for name in COMPONENTS
    }}
    atomic_write(directory / "manifest.json", (json.dumps(record, indent=2) + "\n").encode())
    return record
