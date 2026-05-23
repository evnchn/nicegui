import atexit
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from .. import app
from ..storage import Storage
from . import general

# pylint: disable=redefined-outer-name

_configured = False  # separate sentinel so plain `import nicegui.testing` doesn't clobber Storage.path


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add pytest option for main file."""
    parser.addini('main_file', 'main file', default='main.py')


def pytest_configure(config: pytest.Config) -> None:
    """Set up a session-unique storage path and register the "nicegui_main_file" marker."""
    global _configured  # pylint: disable=global-statement  # noqa: PLW0603
    if _configured:
        return  # already configured (e.g. plugin.py + user_plugin.py both loaded)
    _configured = True
    Storage.path = Path(tempfile.mkdtemp(prefix='nicegui-test-storage-')).resolve()
    owner_pid = os.getpid()  # don't let a forked subprocess's atexit rmtree our dir
    atexit.register(lambda: shutil.rmtree(Storage.path, ignore_errors=True) if os.getpid() == owner_pid else None)
    app.storage = Storage()  # rebuild app.storage so its FilePersistentDict picks up the new path
    config.addinivalue_line('markers', 'nicegui_main_file: specify the main file for the test')


def pytest_unconfigure(config: pytest.Config) -> None:  # pylint: disable=unused-argument
    """Reset configured sentinel and clean up session-unique storage at pytest session end.

    Enables in-process re-runs (pytest.main() called twice in one Python process, custom
    test runners): each new session gets a fresh tempdir and a rebuilt app.storage instead
    of silently sharing state with the previous one. atexit still runs at process exit as
    a safety net for aborted sessions; shutil.rmtree(..., ignore_errors=True) makes the
    potential double-cleanup harmless.
    """
    global _configured  # pylint: disable=global-statement  # noqa: PLW0603
    if not _configured:
        return
    shutil.rmtree(Storage.path, ignore_errors=True)
    _configured = False


def get_path_to_main_file(request: pytest.FixtureRequest) -> Path | None:
    """Get the path to the main file from the test marker or global config."""
    marker = next((m for m in request.node.iter_markers('nicegui_main_file')), None)
    main_file = marker.args[0] if marker else request.config.getini('main_file')
    if not main_file:
        return None
    assert request.config.inipath is not None
    path = (request.config.inipath.parent / main_file).resolve()
    if not path.is_file():
        raise FileNotFoundError(f'Main file not found: {path}')
    return path


@pytest.fixture
def nicegui_reset_globals():
    """Reset the global state of the NiceGUI package."""
    with general.nicegui_reset_globals():
        yield
