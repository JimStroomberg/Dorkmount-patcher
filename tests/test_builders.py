"""Offline refusal and extraction checks; no vendor firmware or device required."""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_builder(extension):
    spec = importlib.util.spec_from_file_location(
        extension + '_builder', ROOT / 'firmware' / extension / 'build.py'
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Builders(unittest.TestCase):
    def test_rejects_unknown_content_and_wrong_length_for_each_component(self):
        for extension in ('dmr1', 'dmr2', 'dmr3'):
            builder = load_builder(extension)
            for component, (length, _) in builder.STOCK.items():
                for size in (length, length - 1):
                    with self.subTest(extension=extension, component=component, size=size):
                        with tempfile.TemporaryDirectory() as tmp:
                            image = Path(tmp) / 'unknown.bin'
                            image.write_bytes(bytes(size))
                            with self.assertRaisesRegex(ValueError, 'exact supported'):
                                builder.checked_input(image, component)

    def test_unknown_input_refuses_before_compilation_and_export(self):
        for extension in ('dmr1', 'dmr2', 'dmr3'):
            with self.subTest(extension=extension), tempfile.TemporaryDirectory() as tmp:
                builder = load_builder(extension)
                image = Path(tmp) / 'unknown.bin'
                image.write_bytes(bytes(85508))
                output = Path(tmp) / 'output'
                with patch.object(builder.subprocess, 'run') as compiler:
                    with self.assertRaisesRegex(ValueError, 'exact supported'):
                        builder.build(image, image, image, output)
                    compiler.assert_not_called()
                self.assertFalse(output.exists())

    def test_failed_toolchain_leaves_no_export_or_temporary_files(self):
        for extension in ('dmr1', 'dmr2', 'dmr3'):
            with self.subTest(extension=extension), tempfile.TemporaryDirectory() as tmp:
                builder = load_builder(extension)
                output = Path(tmp) / 'output'
                # Input checking is separately tested. Simulate a compiler failure
                # after that boundary without requiring any proprietary images.
                with patch.object(builder, 'checked_input', return_value=b'synthetic'):
                    with patch.object(builder.subprocess, 'run',
                                      side_effect=subprocess.CalledProcessError(1, 'clang')):
                        with self.assertRaises(subprocess.CalledProcessError):
                            builder.build('main', 'dock', 'numpad', output)
                self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_target_metadata_agrees_with_builders(self):
        for extension in ('dmr1', 'dmr2', 'dmr3'):
            with self.subTest(extension=extension):
                builder = load_builder(extension)
                target = json.loads(
                    (ROOT / 'firmware/targets' / f'1.29.0-{extension}.json').read_text()
                )
                self.assertFalse(target['flashing_included'])
                self.assertEqual(set(target['components']), set(builder.STOCK))
                for name, image in target['components'].items():
                    self.assertEqual((image['size'], image['stock_sha256']), builder.STOCK[name])
                    self.assertEqual(image['patched_sha256'], builder.EXPECTED[name])
                ranges = {name: [] for name in builder.STOCK}
                for region in target['patches']:
                    start, length = region['offset'], region['length']
                    size = target['components'][region['component']]['size']
                    self.assertGreaterEqual(start, 0)
                    self.assertGreater(length, 0)
                    self.assertLessEqual(start + length, size)
                    for other_start, other_end in ranges[region['component']]:
                        self.assertTrue(start + length <= other_start or start >= other_end)
                    ranges[region['component']].append((start, start + length))

    def test_extracted_sources_match_recorded_prototype(self):
        manifest = json.loads((ROOT / 'firmware/provenance.json').read_text())
        for name, expected in manifest['unchanged_firmware_files'].items():
            with self.subTest(path=name):
                self.assertEqual(sha256((ROOT / name).read_bytes()).hexdigest(), expected)


if __name__ == '__main__':
    unittest.main()
