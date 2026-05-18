"""Browser-level tests for ``ui.codemirror.with_crdt()``.

These exercise the full client-side stack (yjs + y-codemirror.next + Socket.IO bridge),
not just the server-side room primitive (``test_yjs_room.py`` covers that).

A single page hosts two editors with the same ``doc_id``; typing into editor A should
propagate to editor B via the Yjs binding. If the JS bundle is broken, the y-codemirror
binding is wired wrong, or the Socket.IO handlers don't fire, this test fails — even
though the server-side ``yjs_room`` unit tests would pass.

A true two-browser test (separate Selenium sessions) remains a follow-up; ``Screen`` is
single-window.
"""
from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By

from nicegui import ui
from nicegui.testing import Screen

pytest.importorskip('pycrdt')


def test_two_editors_same_doc_id_share_state(screen: Screen) -> None:
    @ui.page('/')
    def page():
        ui.codemirror(language='Python').with_crdt('shared-test-doc').classes('editor-a')
        ui.codemirror(language='Python').with_crdt('shared-test-doc').classes('editor-b')

    screen.open('/')

    editor_a = screen.selenium.find_element(By.CSS_SELECTOR, '.editor-a .cm-content')
    editor_a.click()
    editor_a.send_keys('hello world')

    # Editor B's CodeMirror DOM should reflect the same text once the Yjs round-trip
    # (local apply -> emit -> server relay -> remote apply) completes.
    screen.wait(0.5)  # allow the Socket.IO round-trip
    screen.should_contain('hello world')

    editor_b = screen.selenium.find_element(By.CSS_SELECTOR, '.editor-b .cm-content')
    assert 'hello world' in editor_b.text


def test_seeded_room_propagates_to_first_client(screen: Screen) -> None:
    from pycrdt import Text

    from nicegui import yjs_room

    # Seed the room BEFORE the page is opened; the first connecting client must
    # receive the seeded content in its initial yjs_init payload.
    doc = yjs_room.get_doc('seed-test-doc')
    doc['codemirror'] = Text()
    doc['codemirror'] += 'preseeded content'

    @ui.page('/')
    def page():
        ui.codemirror(language='Markdown').with_crdt('seed-test-doc').classes('editor')

    screen.open('/')
    screen.wait(0.5)
    screen.should_contain('preseeded content')
