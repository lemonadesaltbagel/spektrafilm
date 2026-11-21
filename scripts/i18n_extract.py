"""Find GUI strings that are missing from a translation catalog.

Builds the GUI offscreen while recording every string passed to ``tr()``,
adds the ``tr('...')`` literals found in the source (dialogs and status
messages that only appear on user actions), and compares them with
``src/spektrafilm_gui/locales/<language>.json``.

    python scripts/i18n_extract.py              # report missing / unused keys
    python scripts/i18n_extract.py --write      # add missing keys with "" values

Empty values are ignored at runtime, so the English text is shown until a
translation is filled in.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GUI_SRC = REPO / 'src' / 'spektrafilm_gui'
LOCALES = GUI_SRC / 'locales'

# Passed to tr() through a variable (simulation mode labels in controller.py).
DYNAMIC_KEYS = {'Preview', 'Scan', 'Simulation'}


def collect_source_keys() -> set[str]:
    """String literals passed to ``tr(...)`` in the GUI sources, plus DYNAMIC_KEYS."""
    keys: set[str] = set(DYNAMIC_KEYS)
    for path in GUI_SRC.rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == 'tr'
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and node.args[0].value
            ):
                keys.add(node.args[0].value)
    return keys


def collect_runtime_keys() -> set[str]:
    """Every string that reaches ``tr()`` while the full GUI is built."""
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    os.environ['SPEKTRAFILM_LANG'] = 'en'
    sys.path.insert(0, str(REPO / 'src'))

    from spektrafilm_gui import i18n

    keys: set[str] = set()
    original_tr = i18n.tr

    def recording_tr(text: str) -> str:
        if text:
            keys.add(text)
        return original_tr(text)

    # Patch before the GUI modules import ``tr`` by name.
    i18n.tr = recording_tr
    from spektrafilm_gui.app import create_app

    app = create_app()
    app.viewer.close()
    return keys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--language', default='zh_CN')
    parser.add_argument('--write', action='store_true', help='add missing keys with empty values')
    parser.add_argument('--static-only', action='store_true', help='skip building the GUI')
    args = parser.parse_args()

    keys = collect_source_keys()
    if not args.static_only:
        keys |= collect_runtime_keys()

    catalog_path = LOCALES / f'{args.language}.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8')) if catalog_path.exists() else {}
    missing = sorted(key for key in keys if not catalog.get(key))
    unused = sorted(key for key in catalog if key not in keys)

    print(f'{len(keys)} strings, {len(missing)} untranslated, {len(unused)} unused in {catalog_path.name}')
    for key in missing:
        print(f'  missing: {key!r}')
    for key in unused:
        print(f'  unused:  {key!r}')

    if args.write and missing:
        for key in missing:
            catalog.setdefault(key, '')
        catalog_path.write_text(json.dumps(dict(sorted(catalog.items())), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'wrote {catalog_path}')
    return 1 if missing else 0


if __name__ == '__main__':
    raise SystemExit(main())
