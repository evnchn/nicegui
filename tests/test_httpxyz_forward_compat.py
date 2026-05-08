import subprocess
import sys
from importlib.util import find_spec
from textwrap import dedent

import pytest

WARNING_FRAGMENT = 'Real httpx is loaded in this process'

needs_httpxyz = pytest.mark.skipif(find_spec('httpxyz') is None, reason='httpxyz not installed')


def _run(code):
    return subprocess.run([sys.executable, '-W', 'default', '-c', dedent(code)],
                          capture_output=True, text=True, timeout=60, check=False)


def test_cold_import_nicegui_no_warning():
    result = _run('import nicegui')
    assert result.returncode == 0, result.stderr
    assert WARNING_FRAGMENT not in result.stderr


@needs_httpxyz
def test_httpxyz_first_no_warning():
    result = _run('''
        import httpxyz
        import nicegui
    ''')
    assert result.returncode == 0, result.stderr
    assert WARNING_FRAGMENT not in result.stderr


def test_real_httpx_loaded_warns_without_httpxyz():
    result = _run('''
        import httpx
        import nicegui
    ''')
    assert result.returncode == 0, result.stderr
    assert WARNING_FRAGMENT in result.stderr
    assert 'first line of your entry point' in result.stderr
    assert 'https://github.com/zauberzeug/nicegui/issues/6024' in result.stderr


@needs_httpxyz
def test_real_httpx_with_late_httpxyz_warns():
    result = _run('''
        import httpx
        import httpxyz
        import nicegui
    ''')
    assert result.returncode == 0, result.stderr
    assert WARNING_FRAGMENT in result.stderr


def test_warning_points_at_user_code_not_nicegui():
    result = _run('''
        import warnings
        warnings.simplefilter("always")
        import httpx
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            import nicegui
        for w in caught:
            if "Real httpx is loaded" in str(w.message):
                assert "nicegui" not in w.filename, f"warning points inside the package: {w.filename}"
                print("STACKLEVEL_OK", w.filename)
                break
        else:
            raise AssertionError("expected warning was not captured")
    ''')
    assert result.returncode == 0, result.stderr
    assert 'STACKLEVEL_OK' in result.stdout
