"""User-interface translations for the spektrafilm GUI.

Strings are looked up by their English source text, so a missing
translation simply shows the English original. Catalogs live in
``locales/<language>.json`` as ``{"english text": "translation"}``.

The language is chosen once per process, in this order:

1. the ``SPEKTRAFILM_LANG`` environment variable (``en``, ``zh_CN``, ...),
2. the preference saved from the GUI (``ui/language`` in QSettings),
3. the system locale.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from importlib import resources

from qtpy import QtCore

QLocale = getattr(QtCore, 'QLocale')
QSettings = getattr(QtCore, 'QSettings')

DEFAULT_LANGUAGE = 'en'
AUTO_LANGUAGE = 'auto'
LANGUAGE_ENV_VAR = 'SPEKTRAFILM_LANG'
LANGUAGE_SETTINGS_KEY = 'ui/language'

# Language code -> name shown in the language selector (in that language).
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'zh_CN': '简体中文',
}

_current_language: str | None = None


def _settings():
    return QSettings('spektrafilm', 'spektrafilm')


def normalize_language(code: str | None) -> str | None:
    """Map a locale-ish code (``zh``, ``zh-CN``, ``zh_Hans_CN``) to a supported language."""
    if not code:
        return None
    code = code.strip().replace('-', '_')
    if code in SUPPORTED_LANGUAGES:
        return code
    if code.lower().startswith('zh'):
        return 'zh_CN'
    if code.lower().startswith('en'):
        return 'en'
    return None


def saved_language_preference() -> str:
    """The language picked in the GUI, or ``auto`` to follow the system."""
    value = _settings().value(LANGUAGE_SETTINGS_KEY, AUTO_LANGUAGE)
    value = str(value) if value else AUTO_LANGUAGE
    return value if value == AUTO_LANGUAGE or value in SUPPORTED_LANGUAGES else AUTO_LANGUAGE


def save_language_preference(code: str) -> None:
    if code != AUTO_LANGUAGE and code not in SUPPORTED_LANGUAGES:
        raise ValueError(f'unsupported language: {code}')
    _settings().setValue(LANGUAGE_SETTINGS_KEY, code)


def system_language() -> str:
    return normalize_language(QLocale.system().name()) or DEFAULT_LANGUAGE


def resolve_language() -> str:
    env_language = normalize_language(os.environ.get(LANGUAGE_ENV_VAR))
    if env_language is not None:
        return env_language
    saved = saved_language_preference()
    if saved != AUTO_LANGUAGE:
        return saved
    return system_language()


def current_language() -> str:
    global _current_language
    if _current_language is None:
        _current_language = resolve_language()
    return _current_language


def set_language(code: str | None) -> None:
    """Override the language for this process; ``None`` re-resolves it on next use."""
    global _current_language
    _current_language = normalize_language(code) if code is not None else None


@lru_cache(maxsize=None)
def load_catalog(language: str) -> dict[str, str]:
    if language == DEFAULT_LANGUAGE:
        return {}
    try:
        text = resources.files('spektrafilm_gui.locales').joinpath(f'{language}.json').read_text(encoding='utf-8')
    except (FileNotFoundError, ModuleNotFoundError):
        return {}
    return {key: value for key, value in json.loads(text).items() if value}


@lru_cache(maxsize=None)
def _translations(language: str) -> frozenset[str]:
    return frozenset(load_catalog(language).values())


def is_translation(text: str) -> bool:
    """True when ``text`` is already a translation in the current language."""
    return text in _translations(current_language())


def tr(text: str) -> str:
    """Translate ``text`` into the current language, falling back to ``text``."""
    if not text:
        return text
    return load_catalog(current_language()).get(text, text)
