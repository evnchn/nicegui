import re

import pytest

from nicegui import ui
from nicegui.testing import Screen


def test_nicegui_port_env_var_is_ignored_with_warning(screen: Screen, monkeypatch: pytest.MonkeyPatch):
    @ui.page('/')
    def page():
        ui.label('Hello')

    monkeypatch.setenv('NICEGUI_PORT', '1')
    screen.open('/')
    screen.should_contain('Hello')
    screen.assert_py_logger('WARNING', re.compile('Ignoring the environment variable NICEGUI_PORT=1'))
