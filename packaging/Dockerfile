FROM python:3.13-slim-trixie@sha256:9d2e5553305c7c7b0097999bb17187c69b921ccd6bc9d40e4bb5ebe652c00285
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    binutils libgl1 libegl1 libopengl0 libxkbcommon0 libdbus-1-3 libxcb-cursor0 fonts-dejavu-core libgssapi-krb5-2 \
    libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libxcb-xkb1 libxkbcommon-x11-0 \
    libxcb-image0 libxcb-render-util0 libfontconfig1 libglib2.0-0 libgtk-3-0t64 desktop-file-utils \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /source
COPY packaging/requirements-build.txt /requirements-build.txt
RUN python -m pip install --no-cache-dir -r /requirements-build.txt
COPY . .
ARG SOURCE_COMMIT=local
ARG SOURCE_DIRTY=true
ARG SOURCE_DATE_EPOCH=0
ENV SOURCE_COMMIT=$SOURCE_COMMIT SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH SOURCE_DIRTY=$SOURCE_DIRTY
RUN python tools/release_metadata.py \
    && python -m pip install --no-cache-dir --no-deps --no-build-isolation . \
    && QT_QPA_PLATFORM=offscreen python -m pytest -q \
    && ruff check src tests tools examples \
    && pyinstaller --noconfirm --clean --onedir --name Dorkmount-patcher \
       --collect-data dorkmount_patcher --paths src packaging/desktop_entry.py \
    && mkdir /bundle \
    && cp -a dist/Dorkmount-patcher/. /bundle/ \
    && rm -f /bundle/_internal/libstdc++.so.6 /bundle/_internal/libgcc_s.so.1 /bundle/_internal/libfontconfig.so.1 \
    && cp -a docs examples LICENSE THIRD_PARTY.md SECURITY.md /bundle/ \
    && python tools/bundle_notices.py /bundle/third-party-licenses \
    && cp packaging/START-HERE.txt /bundle/START-HERE.txt \
    && QT_QPA_PLATFORM=offscreen /bundle/Dorkmount-patcher --demo --screenshot /tmp/bundle-smoke.png \
    && python tools/package_linux.py /bundle /packages \
    && python -m build --no-isolation --outdir /packages \
    && python -m pip freeze --all > /packages/build-requirements.txt
WORKDIR /bundle
CMD ["./Dorkmount-patcher", "--version"]
