from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'package_research_bundle_portable.py'


def load_module():
    spec = importlib.util.spec_from_file_location('portable_packager', SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_portable_manifest_avoids_msys_sha256sum_marker_dependency():
    mod = load_module()
    td = Path(tempfile.mkdtemp())
    bundle = td / 'bundle'
    bundle.mkdir()
    (bundle / 'a.txt').write_text('a', encoding='utf-8')
    (bundle / 'b.txt').write_text('b', encoding='utf-8')
    out = td / 'out.zip'
    digest = mod.build_zip(bundle, out)
    assert len(digest) == 64
    rows = (bundle / mod.MANIFEST).read_text(encoding='utf-8').splitlines()
    assert len(rows) == 2
    assert all(len(row) >= 67 and row[64:66] == '  ' for row in rows)
    assert all(' *' not in row for row in rows)
    with zipfile.ZipFile(out) as zf:
        assert zf.testzip() is None
        assert mod.MANIFEST in zf.namelist()


def test_portable_packager_rewrites_old_msys_manifest():
    mod = load_module()
    td = Path(tempfile.mkdtemp())
    bundle = td / 'bundle'
    bundle.mkdir()
    (bundle / 'payload.txt').write_text('payload', encoding='utf-8')
    (bundle / mod.MANIFEST).write_text('0' * 64 + ' *payload.txt\n', encoding='utf-8')
    out = td / 'out.zip'
    mod.build_zip(bundle, out)
    row = (bundle / mod.MANIFEST).read_text(encoding='utf-8').strip()
    assert row[64:66] == '  '
    assert row.endswith('payload.txt')


if __name__ == '__main__':
    for fn in (test_portable_manifest_avoids_msys_sha256sum_marker_dependency, test_portable_packager_rewrites_old_msys_manifest):
        fn()
        print('PASS', fn.__name__)
