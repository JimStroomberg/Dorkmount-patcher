PYTHON ?= python3
VENV ?= .venv
PY := $(VENV)/bin/python
OUT ?= dist/release

.PHONY: setup doctor demo check package package-test

setup:
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -r packaging/requirements-build.txt
	$(PY) -m pip install --no-deps --no-build-isolation -e .

doctor:
	$(PY) tools/doctor.py

demo:
	$(VENV)/bin/dorkmount-patcher --demo

check:
	$(PY) tools/release_metadata.py
	QT_QPA_PLATFORM=offscreen $(PY) -m pytest -q
	$(VENV)/bin/ruff check src tests tools examples
	git diff --check

package:
	$(PYTHON) tools/doctor.py --package
	$(PYTHON) tools/build_release.py build --output "$(OUT)"

package-test:
	$(PYTHON) tools/build_release.py test --output "$(OUT)" --platform ubuntu
	$(PYTHON) tools/build_release.py test --output "$(OUT)" --platform cachyos
