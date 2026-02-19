"""Tests for the lang attribute in the HTML tag."""
import re

import pytest
import requests

from nicegui import ui
from nicegui.testing import Screen


def test_no_lang_attribute_by_default(screen: Screen):
    """Test that lang attribute is not added when language is not explicitly set."""
    @ui.page('/')
    def page():
        ui.label('Hello')

    screen.open('/')

    # Fetch raw HTML from server (not from browser DOM which may be modified by browser)
    response = requests.get('http://localhost:3392/')
    html_text = response.text

    # Check if lang attribute is in the raw HTML from server
    html_tag_match = re.search(r'<html[^>]*>', html_text, re.IGNORECASE)
    assert html_tag_match, 'Could not find <html> tag in response'
    html_tag = html_tag_match.group(0)
    assert 'lang=' not in html_tag.lower(), \
        f'lang attribute should not be in HTML tag when not explicitly set, but got: {html_tag}'


@pytest.mark.parametrize('language_code,expected_lang', [
    ('fr', 'fr'),
    ('zh-CN', 'zh-CN'),
    ('de', 'de'),
    ('es', 'es'),
    ('en-US', 'en-US'),
    ('en-GB', 'en-GB'),
    ('zh-TW', 'zh-TW'),
    ('pt-BR', 'pt-BR'),
    ('de-CH', 'de-CH'),
])
def test_lang_attribute_with_explicit_language(screen: Screen, language_code: str, expected_lang: str):
    """Test that lang attribute is added when language is explicitly set and full codes are preserved."""
    @ui.page('/', language=language_code)
    def page():
        ui.label('Test')

    screen.open('/')

    # Check raw HTML from server
    response = requests.get('http://localhost:3392/')
    html_tag_match = re.search(r'<html[^>]*>', response.text, re.IGNORECASE)
    assert html_tag_match, 'Could not find <html> tag in response'
    html_tag = html_tag_match.group(0)
    assert f'lang="{expected_lang}"' in html_tag, \
        f'lang attribute should be "{expected_lang}", got: {html_tag}'
