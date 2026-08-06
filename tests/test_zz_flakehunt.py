"""THROWAWAY flake hunt — controlled A/B of the original vs patched fullscreen test.

Both variants run in the SAME pytest process on the SAME runner, interleaved by pytest's
ordering, so they see identical hardware and load. Never merge this file.
"""
import os

import pytest

from nicegui import ui
from nicegui.testing import Screen

REPEATS = int(os.environ.get('REPEATS', '30'))


def _make_table(screen: Screen):
    holder = {}

    @ui.page('/')
    def page():
        table = ui.table(rows=[{'name': 'Alice'}])
        table.add_slot('top', '<q-btn dense flat label="FS" @click="props.toggleFullscreen" />')
        holder['table'] = table

    screen.open('/')
    return holder


@pytest.mark.parametrize('run', range(REPEATS))
def test_original(screen: Screen, run: int):
    """The current upstream logic — the racy second click."""
    holder = _make_table(screen)
    assert holder['table'].is_fullscreen is False

    screen.click('FS')
    screen.wait_for(lambda: holder['table'].is_fullscreen is True)

    screen.click('FS')  # <-- the line that goes stale in CI
    screen.wait_for(lambda: holder['table'].is_fullscreen is False)


@pytest.mark.parametrize('run', range(REPEATS))
def test_upstream_sleep(screen: Screen, run: int):
    """What upstream shipped in c16dc58b: a fixed 0.5 s sleep before the second click."""
    holder = _make_table(screen)
    assert holder['table'].is_fullscreen is False

    screen.click('FS')
    screen.wait_for(lambda: holder['table'].is_fullscreen is True)
    screen.wait(0.5)  # HACK: wait for the echoed fullscreen update

    screen.click('FS')
    screen.wait_for(lambda: holder['table'].is_fullscreen is False)


@pytest.mark.parametrize('run', range(REPEATS))
def test_body_class_wait(screen: Screen, run: int):
    """Reviewer's proposal: wait for Quasar's fullscreen body class, then a plain second click.

    Hypothesis: this is a no-op. The class is added synchronously inside setFullscreen(),
    before the watcher that emits update:fullscreen ever flushes, so it is already set by
    the time the server flag flips. It should fail at the same rate as test_original.
    """
    holder = _make_table(screen)
    assert holder['table'].is_fullscreen is False

    screen.click('FS')
    screen.wait_for(lambda: holder['table'].is_fullscreen is True)
    screen.wait_for(lambda: 'q-body--fullscreen-mixin' in screen.find_by_tag('body').get_attribute('class'))

    screen.click('FS')
    screen.wait_for(lambda: holder['table'].is_fullscreen is False)


@pytest.mark.parametrize('run', range(REPEATS))
def test_patched(screen: Screen, run: int):
    """The proposed fix — the second click retried through wait_for."""
    holder = _make_table(screen)
    assert holder['table'].is_fullscreen is False

    def click_fullscreen_button() -> bool:
        screen.click('FS')
        return True

    screen.click('FS')
    screen.wait_for(lambda: holder['table'].is_fullscreen is True)

    screen.wait_for(click_fullscreen_button)
    screen.wait_for(lambda: holder['table'].is_fullscreen is False)
