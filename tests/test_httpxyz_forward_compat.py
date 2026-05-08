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


@pytest.mark.parametrize('setup, expect_warning', [
    pytest.param('import nicegui', False, id='cold'),
    pytest.param('import httpxyz; import nicegui', False, id='httpxyz-first', marks=needs_httpxyz),
    pytest.param('import httpx; import nicegui', True, id='httpx-only'),
    pytest.param('import httpx; import httpxyz; import nicegui', True, id='httpx-then-httpxyz', marks=needs_httpxyz),
])
def test_warning_fires_iff_real_httpx_loaded(setup, expect_warning):
    result = _run(setup)
    assert result.returncode == 0, result.stderr
    if expect_warning:
        assert WARNING_FRAGMENT in result.stderr
        assert 'first line of your entry point' in result.stderr
        assert 'https://github.com/zauberzeug/nicegui/issues/6024' in result.stderr
    else:
        assert WARNING_FRAGMENT not in result.stderr


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
