#!/usr/bin/env python3
"""Same clean Linux package build locally and in GitHub Actions. Requires Docker."""

import argparse
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

from release_metadata import ROOT, metadata


def run(*args, **kwargs):
    subprocess.run(list(map(str, args)), check=True, **kwargs)


def image_for(platform):
    return json.loads((ROOT / "packaging/platforms.json").read_text())[f"{platform}_test_image"]


def build(output):
    if output.exists():
        raise FileExistsError("Use a new output directory so old files cannot enter a release.")
    output.mkdir(parents=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
    if os.environ.get("GITHUB_ACTIONS") == "true" and dirty:
        raise ValueError("CI release builds require a clean checkout.")
    epoch = subprocess.check_output(["git", "show", "-s", "--format=%ct", "HEAD"], cwd=ROOT, text=True).strip()
    image = "dorkmount-patcher-packaging:local"
    run("docker", "build", "--platform", "linux/amd64", "--build-arg", f"SOURCE_COMMIT={commit}",
        "--build-arg", f"SOURCE_DATE_EPOCH={epoch}", "--build-arg", f"SOURCE_DIRTY={str(dirty).lower()}",
        "-t", image, "-f", ROOT / "packaging/Dockerfile", ROOT)
    archive = output / "build-output.tar"
    with archive.open("wb") as stream:
        run("docker", "run", "--rm", "--platform", "linux/amd64", image,
            "tar", "-cf", "-", "-C", "/packages", ".", stdout=stream)
    # Archive comes only from our just-built disposable image. Refuse unsafe members.
    with tarfile.open(archive) as stream:
        stream.extractall(output, filter="data")
    archive.unlink()
    run("docker", "run", "--rm", "--platform", "linux/amd64", "--env", f"SOURCE_DATE_EPOCH={epoch}",
        "--volume", f"{output / 'cachyos-input'}:/input:ro", "--volume", f"{output}:/output",
        "--volume", f"{ROOT / 'packaging'}:/scripts:ro", image_for("cachyos"),
        "bash", "/scripts/build-cachyos.sh")
    with (output / f"Dorkmount-patcher-{metadata()['version']}-linux-x86_64.tar.gz").open("wb") as stream:
        run("docker", "run", "--rm", "--platform", "linux/amd64", image,
            "tar", "-czf", "-", "-C", "/bundle", ".", stdout=stream)


def test(output, platform):
    results = output / "checks" / platform
    results.mkdir(parents=True, exist_ok=True)
    scripts = results / "scripts"
    scripts.mkdir(exist_ok=True)
    for script in (ROOT / "packaging").glob("test-*.sh"):
        shutil.copyfile(script, scripts / script.name)
    if platform == "ubuntu":
        # The minimal Ubuntu image has no CA package yet. Bootstrap HTTPS APT
        # using public trust roots from the pinned official build base; package
        # signatures remain verified by Ubuntu's own archive keyring.
        base = (ROOT / "packaging/Dockerfile").read_text().splitlines()[0].split()[1]
        with (results / "bootstrap-ca.crt").open("wb") as stream:
            run("docker", "run", "--rm", "--platform", "linux/amd64", base,
                "cat", "/etc/ssl/certs/ca-certificates.crt", stdout=stream)
    # CachyOS pacman isolates package hooks with a network namespace. Permit
    # namespace creation in this disposable container, preserving that isolation.
    namespace = ["--cap-add", "SYS_ADMIN"] if platform == "cachyos" else []
    run("docker", "run", "--rm", "--platform", "linux/amd64", *namespace,
        "--env", f"EXPECTED_VERSION={metadata()['version']}", "--env", "LANG=C.UTF-8",
        "--volume", f"{output}:/packages:ro", "--volume", f"{scripts}:/scripts:ro",
        "--volume", f"{results}:/results", image_for(platform),
        "bash", f"/scripts/test-{platform}.sh")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "test"))
    parser.add_argument("--output", type=Path, default=ROOT / "dist/release")
    parser.add_argument("--platform", choices=("ubuntu", "cachyos"))
    args = parser.parse_args()
    os.chdir(ROOT)
    output = args.output.resolve()
    if args.command == "build":
        build(output)
    else:
        if not args.platform:
            parser.error("test requires --platform")
        test(output, args.platform)
