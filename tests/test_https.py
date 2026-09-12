import json
import ssl
import subprocess
import threading
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from dorkmount_patcher import cli, firmware, https


@pytest.fixture
def local_https(tmp_path, monkeypatch, synthetic):
    """A fresh test CA and localhost server; no network service or committed keys."""
    stock, _, _ = synthetic
    ca, key = tmp_path / "ca.pem", tmp_path / "ca.key"
    cert, server_key = tmp_path / "server.pem", tmp_path / "server.key"
    csr, extensions = tmp_path / "server.csr", tmp_path / "extensions.cnf"
    extensions.write_text(
        "basicConstraints=critical,CA:FALSE\n"
        "keyUsage=critical,digitalSignature,keyEncipherment\n"
        "extendedKeyUsage=serverAuth\nsubjectAltName=DNS:localhost\n"
        "authorityKeyIdentifier=keyid,issuer\nsubjectKeyIdentifier=hash\n")

    def openssl(*args):
        subprocess.run(["openssl", *map(str, args)], check=True, capture_output=True)

    openssl("req", "-x509", "-newkey", "rsa:2048", "-noenc", "-days", "1",
            "-subj", "/CN=Dorkmount test CA", "-keyout", key, "-out", ca,
            "-addext", "basicConstraints=critical,CA:TRUE",
            "-addext", "keyUsage=critical,keyCertSign,cRLSign")
    openssl("req", "-new", "-newkey", "rsa:2048", "-noenc", "-subj", "/CN=localhost",
            "-keyout", server_key, "-out", csr)
    openssl("x509", "-req", "-in", csr, "-CA", ca, "-CAkey", key, "-CAcreateserial",
            "-days", "1", "-extfile", extensions, "-out", cert)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            name = self.path.rsplit("/", 1)[-1].removesuffix(".bin")
            body = stock[name]
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, server_key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(firmware, "BASE_URL", f"https://localhost:{server.server_port}/fw/")
    monkeypatch.setattr(https, "SYSTEM_CA_BUNDLE", ca)
    monkeypatch.setattr(https.sys, "platform", "linux")
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("SSL_CERT_DIR", raising=False)
    paths = ssl.get_default_verify_paths()._replace(cafile=None, capath=None)
    monkeypatch.setattr(https.ssl, "get_default_verify_paths", lambda: paths)
    try:
        yield ca, server.server_port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_missing_build_host_ca_paths_use_system_bundle(local_https, tmp_path, synthetic):
    context = https.verified_context()
    assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
    assert firmware.obtain_originals(tmp_path / "download") == synthetic[0]


@pytest.mark.parametrize("failure", ["untrusted", "hostname", "existing-default", "non-linux"])
def test_tls_failures_never_fall_back_to_unverified_download(
        local_https, tmp_path, monkeypatch, failure):
    ca, port = local_https
    if failure == "untrusted":
        monkeypatch.setattr(https, "SYSTEM_CA_BUNDLE", tmp_path / "missing")
    elif failure == "hostname":
        monkeypatch.setattr(firmware, "BASE_URL", f"https://127.0.0.1:{port}/fw/")
    elif failure == "existing-default":
        paths = ssl.get_default_verify_paths()._replace(cafile=str(ca))
        monkeypatch.setattr(https.ssl, "get_default_verify_paths", lambda: paths)
    else:
        monkeypatch.setattr(https.sys, "platform", "darwin")
    out = tmp_path / "download"
    with pytest.raises(urllib.error.URLError) as error:
        firmware.obtain_originals(out)
    assert isinstance(error.value.reason, ssl.SSLCertVerificationError)
    assert list(out.iterdir()) == []


@pytest.mark.parametrize("variable", ["SSL_CERT_FILE", "SSL_CERT_DIR"])
@pytest.mark.parametrize("value", ["", "missing"])
def test_explicit_trust_overrides_are_not_silently_broadened(
        local_https, tmp_path, monkeypatch, variable, value):
    monkeypatch.setenv(variable, str(tmp_path / value) if value else "")
    with pytest.raises(urllib.error.URLError) as error:
        firmware.obtain_originals(tmp_path / "download")
    assert isinstance(error.value.reason, ssl.SSLCertVerificationError)


def test_explicit_ca_file_works(local_https, tmp_path, monkeypatch, synthetic):
    ca, _ = local_https
    monkeypatch.setenv("SSL_CERT_FILE", str(ca))
    assert firmware.obtain_originals(tmp_path / "download") == synthetic[0]


def test_verified_cache_does_not_require_tls_configuration(tmp_path, monkeypatch, synthetic):
    for name, raw in synthetic[0].items():
        (tmp_path / f"{name}.bin").write_bytes(raw)

    def fail():
        raise AssertionError("Cached firmware should not initialize HTTPS")

    monkeypatch.setattr(firmware, "verified_context", fail)
    assert firmware.obtain_originals(tmp_path) == synthetic[0]


def test_cli_download_prepares_and_removes_temporary_cache(
        local_https, tmp_path, synthetic, capsys, monkeypatch):
    caches = []
    obtain = firmware.obtain_originals

    def record(directory):
        caches.append(directory)
        return obtain(directory)

    monkeypatch.setattr(firmware, "obtain_originals", record)
    out = tmp_path / "prepared"
    assert cli.main(["prepare", "--download", "--output", str(out)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "dmr2"
    assert all((out / f"{name}-dmr2.bin").read_bytes() == raw
               for name, raw in synthetic[1].items())
    assert caches and all(not path.exists() for path in caches)


@pytest.mark.parametrize("flags", [["--demo"], ["--screenshot", "demo.png"]])
def test_demo_options_cannot_start_downloads(tmp_path, monkeypatch, flags):
    def fail(*args):
        raise AssertionError("Demo options must not cause a firmware download")

    monkeypatch.setattr(firmware, "obtain_originals", fail)
    out = tmp_path / "prepared"
    with pytest.raises(SystemExit) as error:
        cli.main([*flags, "prepare", "--download", "--output", str(out)])
    assert error.value.code == 2
    assert not out.exists()
