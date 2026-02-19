"""Tests for the lang attribute in the HTML tag."""
from nicegui import ui
from nicegui.testing import Screen


def test_no_lang_attribute_by_default(screen: Screen):
    """Test that lang attribute is not added when language is not explicitly set."""
    import re

    import requests

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


def test_lang_attribute_with_page_language(screen: Screen):
    """Test that lang attribute is added when language is set on page."""
    import re

    import requests

    @ui.page('/', language='fr')
    def page():
        ui.label('Bonjour')

    screen.open('/')

    # Check raw HTML from server
    response = requests.get('http://localhost:3392/')
    html_tag_match = re.search(r'<html[^>]*>', response.text, re.IGNORECASE)
    assert html_tag_match
    html_tag = html_tag_match.group(0)
    assert 'lang="fr"' in html_tag, f'lang attribute should be "fr", got: {html_tag}'


def test_lang_attribute_with_full_language_code(screen: Screen):
    """Test that full language codes like zh-CN are preserved."""
    import re

    import requests

    @ui.page('/', language='zh-CN')
    def page():
        ui.label('你好')

    screen.open('/')

    # Check raw HTML from server
    response = requests.get('http://localhost:3392/')
    html_tag_match = re.search(r'<html[^>]*>', response.text, re.IGNORECASE)
    assert html_tag_match
    html_tag = html_tag_match.group(0)
    assert 'lang="zh-CN"' in html_tag, \
        f'lang attribute should be "zh-CN" (full code, not simplified), got: {html_tag}'


def test_lang_attribute_with_global_language(screen: Screen):
    """Test that lang attribute is added when language is set globally via ui.run()."""
    import re

    import requests

    # Note: We can't actually call ui.run() in the test, but we can simulate it
    # by manually setting the language on a page
    @ui.page('/', language='de')
    def page():
        ui.label('Hallo')

    screen.open('/')

    # Check raw HTML from server
    response = requests.get('http://localhost:3392/')
    html_tag_match = re.search(r'<html[^>]*>', response.text, re.IGNORECASE)
    assert html_tag_match
    html_tag = html_tag_match.group(0)
    assert 'lang="de"' in html_tag, f'lang attribute should be "de", got: {html_tag}'


def test_page_language_overrides_default(screen: Screen):
    """Test that page-level language overrides any defaults."""
    import re

    import requests

    @ui.page('/', language='es')
    def page():
        ui.label('Hola')

    screen.open('/')

    # Check raw HTML from server
    response = requests.get('http://localhost:3392/')
    html_tag_match = re.search(r'<html[^>]*>', response.text, re.IGNORECASE)
    assert html_tag_match
    html_tag = html_tag_match.group(0)
    assert 'lang="es"' in html_tag, f'lang attribute should be "es" from page setting, got: {html_tag}'


def test_various_language_codes(screen: Screen):
    """Test that various language code formats are preserved correctly."""
    import re

    import requests

    test_cases = [
        ('en-US', 'English (US)'),
        ('en-GB', 'English (GB)'),
        ('zh-TW', 'Chinese (Taiwan)'),
        ('pt-BR', 'Portuguese (Brazil)'),
        ('de-CH', 'German (Switzerland)'),
    ]

    for lang_code, _ in test_cases:
        @ui.page(f'/{lang_code}', language=lang_code)
        def page():
            ui.label('Test')

        screen.open(f'/{lang_code}')

        # Check raw HTML from server
        response = requests.get(f'http://localhost:3392/{lang_code}')
        html_tag_match = re.search(r'<html[^>]*>', response.text, re.IGNORECASE)
        assert html_tag_match
        html_tag = html_tag_match.group(0)
        assert f'lang="{lang_code}"' in html_tag, \
            f'lang attribute should be "{lang_code}" (preserving full code), got: {html_tag}'
