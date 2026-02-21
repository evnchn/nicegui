import logging

from .content import overview, redirects, registry
from .content.doc.page import _REPO_ROOT
from .custom_restructured_text import CustomRestructuredText
from .intro import create_intro
from .rendering import render_page
from .search import build_search_index
from .tree import build_tree
from .windows import bash_window, browser_window, python_window

_PAGES_WITHOUT_SOURCE = {
    '',
    'architecture',
    'generic_events',
    'section_action_events',
    'section_audiovisual_elements',
    'section_binding_properties',
    'section_configuration_deployment',
    'section_controls',
    'section_data_elements',
    'section_getting_started',
    'section_page_layout',
    'section_pages_routing',
    'section_security',
    'section_styling_appearance',
    'section_testing',
    'section_text_elements',
}

log = logging.getLogger(__name__)


def validate_sources() -> None:
    """Validate that every documentation page has a resolvable source file.

    Pages listed in _PAGES_WITHOUT_SOURCE are exempt.
    Logs errors for pages with missing or invalid source paths so that
    test_startup.sh (which greps for 'Error') catches regressions in CI.
    """
    for name, page in sorted(registry.items()):
        if page.source is None:
            if name not in _PAGES_WITHOUT_SOURCE:
                log.error('Documentation page %r has no source file', name)
        elif not (_REPO_ROOT / page.source).is_file():
            log.error('Documentation page %r references non-existent source: %s', name, page.source)
    for name in _PAGES_WITHOUT_SOURCE:
        if name not in registry:
            log.error('_PAGES_WITHOUT_SOURCE contains unknown page %r', name)
        elif registry[name].source is not None:
            log.error('_PAGES_WITHOUT_SOURCE lists %r but it now has a source: %s', name, registry[name].source)


__all__ = [
    'CustomRestructuredText',
    'bash_window',
    'browser_window',
    'build_search_index',
    'build_tree',
    'create_intro',
    'overview',  # ensure documentation tree is built
    'python_window',
    'redirects',
    'registry',
    'render_page',
    'validate_sources',
]
