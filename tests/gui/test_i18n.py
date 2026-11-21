from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

from spektrafilm_gui import i18n
from spektrafilm_gui import param_manifest
from spektrafilm_gui.widget_primitives import normalize_ui_text

REPO = Path(__file__).resolve().parents[2]
LOCALES = REPO / 'src' / 'spektrafilm_gui' / 'locales'
PLACEHOLDER = re.compile(r'\{[a-z_]+\}')


def _load_extract_script():
    spec = importlib.util.spec_from_file_location('i18n_extract', REPO / 'scripts' / 'i18n_extract.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _manifest_keys() -> set[str]:
    """Labels, titles and tooltips the manifest-driven panels pass to tr()."""
    specs: list[param_manifest.ParamSpec] = []
    keys: set[str] = set()
    for value in vars(param_manifest).values():
        if isinstance(value, param_manifest.GroupManifest):
            keys.add(value.title.lower())
            specs.extend(value.fields)
        elif isinstance(value, tuple) and value and all(isinstance(item, param_manifest.ParamSpec) for item in value):
            specs.extend(value)
    for spec in specs:
        keys.add((spec.label or spec.leaf.replace('_', ' ')).lower())
        if spec.tooltip:
            keys.add(spec.tooltip)
    return keys


@pytest.fixture
def zh_catalog() -> dict[str, str]:
    return json.loads((LOCALES / 'zh_CN.json').read_text(encoding='utf-8'))


@pytest.fixture
def language():
    yield i18n.set_language
    i18n.set_language('en')


def test_zh_catalog_translates_every_source_and_manifest_string(zh_catalog) -> None:
    keys = _load_extract_script().collect_source_keys() | _manifest_keys()
    missing = sorted(key for key in keys if not zh_catalog.get(key))
    assert missing == []


def test_zh_catalog_keeps_format_placeholders(zh_catalog) -> None:
    mismatched = {
        key: value
        for key, value in zh_catalog.items()
        if set(PLACEHOLDER.findall(key)) != set(PLACEHOLDER.findall(value))
    }
    assert mismatched == {}


def test_tr_falls_back_to_english(language) -> None:
    language('zh_CN')
    assert i18n.tr('Simulation failed.') == '模拟失败。'
    assert i18n.tr('not a known string') == 'not a known string'
    assert i18n.tr('') == ''

    language('en')
    assert i18n.tr('Simulation failed.') == 'Simulation failed.'


def test_normalize_ui_text_lowercases_then_translates(language) -> None:
    language('en')
    assert normalize_ui_text('Film Profile') == 'film profile'

    language('zh_CN')
    assert normalize_ui_text('Film Profile') == '胶片型号'


@pytest.mark.parametrize(
    ('code', 'expected'),
    [('zh_CN', 'zh_CN'), ('zh-CN', 'zh_CN'), ('zh_Hans_CN', 'zh_CN'), ('zh', 'zh_CN'), ('en_US', 'en'), ('fr_FR', None), ('', None), (None, None)],
)
def test_normalize_language(code, expected) -> None:
    assert i18n.normalize_language(code) == expected


def test_environment_variable_overrides_saved_and_system_language(monkeypatch) -> None:
    monkeypatch.setattr(i18n, 'saved_language_preference', lambda: 'en')
    monkeypatch.setattr(i18n, 'system_language', lambda: 'en')
    monkeypatch.setenv(i18n.LANGUAGE_ENV_VAR, 'zh_CN')
    assert i18n.resolve_language() == 'zh_CN'


def test_saved_preference_beats_system_language(monkeypatch) -> None:
    monkeypatch.delenv(i18n.LANGUAGE_ENV_VAR, raising=False)
    monkeypatch.setattr(i18n, 'system_language', lambda: 'en')
    monkeypatch.setattr(i18n, 'saved_language_preference', lambda: 'zh_CN')
    assert i18n.resolve_language() == 'zh_CN'

    monkeypatch.setattr(i18n, 'saved_language_preference', lambda: i18n.AUTO_LANGUAGE)
    monkeypatch.setattr(i18n, 'system_language', lambda: 'zh_CN')
    assert i18n.resolve_language() == 'zh_CN'


def test_save_language_preference_rejects_unknown_codes() -> None:
    with pytest.raises(ValueError):
        i18n.save_language_preference('xx')


def test_normalize_ui_text_is_idempotent_for_translations(language) -> None:
    language('zh_CN')
    once = normalize_ui_text('import RGB')
    assert once == '导入 RGB'
    assert normalize_ui_text(once) == once
