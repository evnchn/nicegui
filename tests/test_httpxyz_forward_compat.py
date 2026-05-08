"""Tests for the httpxyz forward-compat advisory in ``nicegui/__init__.py``.

Run each scenario in a fresh subprocess so the import-order check in
``nicegui/__init__.py`` sees a clean ``sys.modules``. ``-W default`` ensures
warnings are emitted to stderr where the test can assert on them.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import textwrap

import pytest

WARNING_FRAGMENT = 'httpxyz is loaded but real httpx was imported first'

httpxyz_available = importlib.util.find_spec('httpxyz') is not None
needs_httpxyz = pytest.mark.skipif(not httpxyz_available, reason='httpxyz not installed')


def _run(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, '-W', 'default', '-c', textwrap.dedent(code)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def test_no_httpxyz_no_warning() -> None:
    """When httpxyz is not imported, NiceGUI must stay silent."""
    result = _run('import nicegui  # noqa: F401')
    assert result.returncode == 0, result.stderr
    assert WARNING_FRAGMENT not in result.stderr


@needs_httpxyz
def test_httpxyz_first_no_warning() -> None:
    """When httpxyz is imported before httpx, the alias is intact and we stay silent."""
    result = _run('''
        import httpxyz  # noqa: F401
        import nicegui  # noqa: F401
    ''')
    assert result.returncode == 0, result.stderr
    assert WARNING_FRAGMENT not in result.stderr


@needs_httpxyz
def test_real_httpx_first_warns() -> None:
    """When real httpx is imported before httpxyz, the alias fails and we warn."""
    result = _run('''
        import httpx  # noqa: F401
        import httpxyz  # noqa: F401
        import nicegui  # noqa: F401
    ''')
    assert result.returncode == 0, result.stderr
    assert WARNING_FRAGMENT in result.stderr
    # The actionable payload must survive any future copy-edits to the warning.
    assert 'first line of your entry point' in result.stderr
    assert 'https://github.com/zauberzeug/nicegui/issues/6024' in result.stderr


@needs_httpxyz
def test_warning_points_at_user_code_not_nicegui() -> None:
    """``stacklevel`` must point at the caller's ``import nicegui``, not at ``nicegui/__init__.py``."""
    result = _run('''
        import warnings
        warnings.simplefilter("always")
        import httpx  # noqa: F401
        import httpxyz  # noqa: F401
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            import nicegui  # noqa: F401
        for w in caught:
            if "httpxyz" in str(w.message):
                # filename should be the -c script (\"<string>\"), not somewhere inside the nicegui package
                assert "nicegui" not in w.filename, f"warning points inside the package: {w.filename}"
                print("STACKLEVEL_OK", w.filename)
                break
        else:
            raise AssertionError("expected httpxyz warning was not captured")
    ''')
    assert result.returncode == 0, result.stderr
    assert 'STACKLEVEL_OK' in result.stdout
