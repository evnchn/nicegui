"""Internationalization (i18n) support for the NiceGUI website.

Provides a translation function ``t()`` backed by gettext ``.po`` catalogs.
Language is resolved per-request via a ``ContextVar``, which is async-safe.
``.po`` files are compiled to ``.mo`` on the fly when missing or stale,
so committing or manually generating ``.mo`` files is not required.

Workflow (requires Babel as a dev dependency)::

    # Extract translatable strings from source code
    pybabel extract -F babel.cfg -k t -o website/translations/messages.pot .

    # Create a new language catalog (first time only)
    pybabel init -i website/translations/messages.pot -d website/translations -l <lang>

    # Update existing catalogs after source strings change
    pybabel update -i website/translations/messages.pot -d website/translations
"""
from __future__ import annotations

import gettext
from contextvars import ContextVar
from pathlib import Path

# URL slug -> display name
SUPPORTED_LANGUAGES: dict[str, str] = {
    'en': 'English',
    'de': 'Deutsch',
    'ja': '日本語',
    'ko': '한국어',
    'zh': '中文',
}

_TRANSLATIONS_DIR = Path(__file__).parent / 'translations'

_current_language: ContextVar[str] = ContextVar('_current_language', default='en')
_url_prefix: ContextVar[str] = ContextVar('_url_prefix', default='')

_cache: dict[str, gettext.GNUTranslations | gettext.NullTranslations] = {}


def _ensure_mo(lang: str) -> None:
    """Compile ``<lang>/LC_MESSAGES/messages.po`` to ``.mo`` if missing or stale."""
    po = _TRANSLATIONS_DIR / lang / 'LC_MESSAGES' / 'messages.po'
    mo = po.with_suffix('.mo')
    if not po.exists():
        return
    if mo.exists() and mo.stat().st_mtime >= po.stat().st_mtime:
        return
    from babel.messages.mofile import write_mo
    from babel.messages.pofile import read_po
    with open(po, 'rb') as po_file:
        catalog = read_po(po_file)
    with open(mo, 'wb') as mo_file:
        write_mo(mo_file, catalog)


def _load_catalog(lang: str) -> gettext.GNUTranslations | gettext.NullTranslations:
    """Load the gettext catalog for *lang*, returning a cached copy if available."""
    if lang not in _cache:
        _ensure_mo(lang)
        _cache[lang] = gettext.translation(
            'messages',
            localedir=str(_TRANSLATIONS_DIR),
            languages=[lang],
            fallback=True,
        )
    return _cache[lang]


def set_language(lang: str) -> None:
    """Set the language for the current request context."""
    _current_language.set(lang)
    _url_prefix.set(f'/{lang}' if lang != 'en' else '')


def get_language() -> str:
    """Return the current request language."""
    return _current_language.get()


def get_url_prefix() -> str:
    """Return the URL path prefix for the current language (empty for English)."""
    return _url_prefix.get()


def t(english: str) -> str:
    """Look up a translated string for the current language.

    Uses the English text as the message ID.  Falls back to the original
    English string when no translation is available.  Internal documentation
    links are rewritten to include the current language prefix.
    """
    lang = _current_language.get()
    if lang == 'en':
        return english
    text = _load_catalog(lang).gettext(english)
    prefix = _url_prefix.get()
    if prefix and '](/documentation' in text:
        text = text.replace('](/documentation', f']({prefix}/documentation')
    return text
