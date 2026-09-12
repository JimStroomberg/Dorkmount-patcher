import importlib.util
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"


def module(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


release = module("release_metadata")
audit = module("audit_release")


def project(tmp_path, version):
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nversion="{version}"\n'
        'authors=[{name="Maintainer",email="noreply@example.org"}]\n'
        '[project.urls]\nRepository="https://example.org/project"\n')
    (tmp_path / "VERSION").write_text(version)
    module = tmp_path / "src/dorkmount_patcher/__init__.py"
    module.parent.mkdir(parents=True)
    module.write_text(f'__version__ = "{version}"\n')
    return tmp_path


@pytest.mark.parametrize("version,tag,deb,filename,arch,prerelease", [
    ("1.2.3a2", "v1.2.3-alpha.2", "1.2.3~alpha2-1",
     "dorkmount-patcher_1.2.3-alpha2-1_amd64.deb", "1.2.3alpha2", True),
    ("1.2.3b1", "v1.2.3-beta.1", "1.2.3~beta1-1",
     "dorkmount-patcher_1.2.3-beta1-1_amd64.deb", "1.2.3beta1", True),
    ("1.2.3b12", "v1.2.3-beta.12", "1.2.3~beta12-1",
     "dorkmount-patcher_1.2.3-beta12-1_amd64.deb", "1.2.3beta12", True),
    ("1.2.3", "v1.2.3", "1.2.3-1",
     "dorkmount-patcher_1.2.3-1_amd64.deb", "1.2.3", False),
])
def test_release_maps_versions(tmp_path, version, tag, deb, filename, arch, prerelease):
    info = release.metadata(project(tmp_path, version))
    assert (info["tag"], info["debian_version"], info["arch_version"], info["prerelease"]) == (
        tag, deb, arch, prerelease)
    assert info["debian_filename"] == filename


@pytest.mark.parametrize("version", ["1.2.3b0", "1.2.3b01", "1.2.3beta1"])
def test_release_refuses_noncanonical_beta_versions(tmp_path, version):
    with pytest.raises(ValueError, match="Release versions must be"):
        release.metadata(project(tmp_path, version))


def test_release_refuses_mismatched_versions(tmp_path):
    root = project(tmp_path, "1.2.3")
    (root / "VERSION").write_text("1.2.2")
    with pytest.raises(ValueError, match="VERSION must match"):
        release.metadata(root)


@pytest.mark.parametrize("name", [".local/session.json", "inputs/MCU0.bin",
                                 "source/private-build/firmware.dat", "../escape", "/etc/passwd",
                                 "captures/test.pcapng", "key.pem"])
def test_release_refuses_private_or_unsafe_members(name):
    with pytest.raises(ValueError):
        audit.check_member(name)


def test_release_symlink_stays_inside_package():
    audit.check_member("opt/app/_internal/libQt6Core.so.6", "PySide6/Qt/lib/libQt6Core.so.6")
    with pytest.raises(ValueError):
        audit.check_member("opt/app/link", "../../../outside")


def test_release_requires_every_expected_asset(tmp_path):
    with pytest.raises(FileNotFoundError):
        audit.assets(tmp_path)
