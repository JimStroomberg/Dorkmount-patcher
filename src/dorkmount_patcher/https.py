"""Use the desktop's CA certificates even when bundled OpenSSL was built elsewhere."""

import os
import ssl
import sys
from pathlib import Path

SYSTEM_CA_BUNDLE = Path("/etc/ssl/certs/ca-certificates.crt")


def verified_context():
    context = ssl.create_default_context()
    paths = ssl.get_default_verify_paths()
    # Debian-built OpenSSL defaults to /usr/lib/ssl, absent on CachyOS.
    # Both supported distributions install this shared CA-bundle path. Keep
    # administrator-supplied SSL_CERT_* overrides authoritative, including empty
    # values; never silently widen an explicitly selected trust store.
    if (sys.platform.startswith("linux") and paths.cafile is None
            and "SSL_CERT_FILE" not in os.environ and "SSL_CERT_DIR" not in os.environ
            and SYSTEM_CA_BUNDLE.is_file()):
        context.load_verify_locations(cafile=SYSTEM_CA_BUNDLE)
    context.set_alpn_protocols(["http/1.1"])
    return context
