"""Tests for the lang attribute in the HTML tag."""
import re

import httpx
import pytest

from nicegui import ui
from nicegui.testing import Screen


def _get_html_tag(url: str) -> str:
    """Fetch the page and return the <html ...> opening tag."""
    response = httpx.get(url)
    match = re.search(r'<html[^>]*>', response.text, re.IGNORECASE)
    assert match, 'Could not find <html> tag in response'
    return match.group(0)


def test_no_lang_attribute_by_default(screen: Screen):
    """Test that lang attribute is not added when language is not explicitly set."""
    @ui.page('/')
    def page():
        ui.label('Hello')

    screen.open('/')
    html_tag = _get_html_tag(screen.url)
    assert 'lang=' not in html_tag.lower(), \
        f'lang attribute should not be in HTML tag when not explicitly set, but got: {html_tag}'


@pytest.mark.parametrize('language_code,expected_lang', [
    ('fr', 'fr'),
    ('zh-CN', 'zh-CN'),
    ('pt-BR', 'pt-BR'),
])
def test_lang_attribute_with_explicit_language(screen: Screen, language_code: str, expected_lang: str):
    """Test that lang attribute is added when language is explicitly set and full codes are preserved."""
    @ui.page('/', language=language_code)
    def page():
        ui.label('Test')

    screen.open('/')
    html_tag = _get_html_tag(screen.url)
    assert f'lang="{expected_lang}"' in html_tag, \
        f'lang attribute should be "{expected_lang}", got: {html_tag}'


def test_none_language_opts_out(screen: Screen):
    """Test that None language explicitly opts out of lang attribute."""
    @ui.page('/', language=None)
    def page():
        ui.label('Test')

    screen.open('/')
    html_tag = _get_html_tag(screen.url)
    assert 'lang=' not in html_tag.lower(), \
        f'lang attribute should not be in HTML tag when None is used, but got: {html_tag}'


def test_none_overrides_global_language(screen: Screen):
    """Test that page language=None opts out even when global config sets a language."""
    screen.ui_run_kwargs['language'] = 'de'

    @ui.page('/', language=None)
    def page():
        ui.label('Test')

    screen.open('/')
    html_tag = _get_html_tag(screen.url)
    assert 'lang=' not in html_tag.lower(), \
        f'lang attribute should not be present when page opts out with None, but got: {html_tag}'


def test_global_language_inherited_by_page(screen: Screen):
    """Test that pages inherit the lang attribute from global config."""
    screen.ui_run_kwargs['language'] = 'de'

    @ui.page('/')
    def page():
        ui.label('Test')

    screen.open('/')
    html_tag = _get_html_tag(screen.url)
    assert 'lang="de"' in html_tag, \
        f'lang attribute should be "de" when inherited from global config, got: {html_tag}'
