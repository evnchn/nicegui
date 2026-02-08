"""SEO utilities for the NiceGUI documentation website."""
import html
import re

SITE_URL = 'https://nicegui.io'
SITE_NAME = 'NiceGUI'
TAGLINE = 'Easy-to-Use Python-Based UI Framework'
DEFAULT_DESCRIPTION = (
    'NiceGUI is an easy-to-use, Python-based UI framework, '
    'which shows up in your web browser. '
    'Create buttons, dialogs, Markdown, 3D scenes, plots and much more.'
)
OG_IMAGE_URL = f'{SITE_URL}/logo_square.png'


def meta(name: str, content: str) -> str:
    """Generate an HTML meta tag."""
    return f'<meta name="{name}" content="{_esc(content)}" />'


def meta_property(property_: str, content: str) -> str:
    """Generate an HTML meta tag with property attribute (for Open Graph)."""
    return f'<meta property="{property_}" content="{_esc(content)}" />'


def canonical_link(path: str) -> str:
    """Generate a canonical link tag for the given path."""
    url = SITE_URL + path
    return f'<link rel="canonical" href="{_esc(url)}" />'


def open_graph_tags(*, title: str, description: str, url: str, og_type: str = 'website') -> str:
    """Generate Open Graph meta tags."""
    return '\n'.join([
        meta_property('og:title', title),
        meta_property('og:description', description),
        meta_property('og:url', url),
        meta_property('og:type', og_type),
        meta_property('og:site_name', SITE_NAME),
        meta_property('og:image', OG_IMAGE_URL),
        meta_property('og:image:alt', f'{SITE_NAME} logo'),
    ])


def twitter_card_tags(*, title: str, description: str) -> str:
    """Generate Twitter Card meta tags."""
    return '\n'.join([
        meta('twitter:card', 'summary'),
        meta('twitter:title', title),
        meta('twitter:description', description),
        meta('twitter:image', OG_IMAGE_URL),
    ])


def page_seo_html(*, title: str, description: str, path: str, og_type: str = 'website') -> str:
    """Generate all SEO-related head HTML for a page."""
    url = SITE_URL + path
    parts = [
        meta('description', description),
        canonical_link(path),
        open_graph_tags(title=title, description=description, url=url, og_type=og_type),
        twitter_card_tags(title=title, description=description),
    ]
    return '\n'.join(parts)


def extract_description(text: str, max_length: int = 160) -> str:
    """Extract a clean description from markdown/rst text, truncated to max_length."""
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # [text](url) -> text
    text = re.sub(r'`([^`]+)`', r'\1', text)  # `code` -> code
    text = re.sub(r'\*+([^*]+)\*+', r'\1', text)  # *bold*/**bold** -> bold
    text = re.sub(r'_([^_]+)_', r'\1', text)  # _italic_ -> italic
    text = re.sub(r':param\s+\w+:', '', text)  # remove :param x:
    text = re.sub(r'<[^>]+>', '', text)  # remove HTML tags
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_length:
        text = text[:max_length - 3].rsplit(' ', 1)[0] + '...'
    return text


def _esc(s: str) -> str:
    return html.escape(s, quote=True)
