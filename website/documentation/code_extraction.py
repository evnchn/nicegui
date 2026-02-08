import inspect
import re
from collections.abc import Callable

import isort

UNCOMMENT_PATTERN = re.compile(r'^(\s*)# ?')


def _uncomment(text: str) -> str:
    return UNCOMMENT_PATTERN.sub(r'\1', text)  # NOTE: non-executed lines should be shown in the code examples


def get_full_code(f: Callable, *, uncomment: bool = True) -> str:
    """Get the full code of a function as a string.

    :param f: the function to extract code from
    :param uncomment: whether to uncomment lines (disable for demos using code_transformers)
    """
    code = inspect.getsource(f).split('# END OF DEMO', 1)[0].strip().splitlines()
    code = [line for line in code if not line.endswith('# HIDE')]
    while not code[0].strip().startswith(('def', 'async def')):
        del code[0]
    del code[0]
    if code[0].strip().startswith('"""'):
        while code[0].strip() != '"""':
            del code[0]
        del code[0]
    non_empty_lines = [line for line in code if line.strip()]
    indentation = len(non_empty_lines[0]) - len(non_empty_lines[0].lstrip())
    code = [line[indentation:] for line in code]
    has_root_function = any(line.strip().startswith(('def root(', 'async def root(')) for line in code)
    if uncomment:
        code = ['from nicegui import ui'] + [_uncomment(line) for line in code]
    else:
        code = ['from nicegui import ui', *code]
    code = ['' if line == '#' else line for line in code]

    if has_root_function:
        code = [line for line in code if line.strip() != 'return root']

    if not code[-1].startswith('ui.run('):
        code.append('ui.run(root)' if has_root_function else 'ui.run()')

    code.insert(-1, '')  # ensure blank line before ui.run
    while code[-3] == '':
        code.pop(-3)  # avoid double blank line before ui.run

    return isort.code('\n'.join(code), no_sections=True, lines_after_imports=1)


# ---------------------------------------------------------------------------
# Modular code transformers
#
# Each transformer is a Callable[[str], str] that takes extracted code and
# returns transformed code suitable for display.  They are designed to be
# composed via the ``code_transformers`` parameter on ``doc.demo()``.
# ---------------------------------------------------------------------------

def get_display_code(f: Callable, code_transformers: list[Callable[[str], str]] | None = None) -> str:
    """Get the display code for a demo function, applying any transformers."""
    code = get_full_code(f, uncomment=not code_transformers)
    if code_transformers:
        for transformer in code_transformers:
            code = transformer(code)
    return code


def make_replacer(old: str, new: str) -> Callable[[str], str]:
    """Create a transformer that performs a simple string replacement."""
    def transform(code: str) -> str:
        return code.replace(old, new)
    return transform


def _lines(code: str) -> list[str]:
    """Split code into lines."""
    return code.split('\n')


def _join(lines: list[str]) -> str:
    """Join lines back into code."""
    return '\n'.join(lines)


def replace_fake_links(code: str) -> str:
    """Replace ``sub_pages.link(...)`` / ``<var>.link(...)`` with ``ui.link(...)``."""
    pattern = re.compile(r'(\s*)\b(\w+)\.link\(')
    lines = _lines(code)
    result = []
    for line in lines:
        m = pattern.match(line)
        if m and m.group(2) not in ('ui', 're', 'os', 'app', 'Path'):
            result.append(pattern.sub(r'\1ui.link(', line, count=1))
        else:
            result.append(line)
    return _join(result)


def replace_fake_sub_pages(code: str) -> str:
    """Replace ``FakeSubPages(...)`` with ``ui.sub_pages(...)``."""
    # Handle assignment: ``sub_pages = FakeSubPages(...)`` → ``ui.sub_pages(...)``
    # Also handle bare: ``FakeSubPages(...)`` → ``ui.sub_pages(...)``
    code = re.sub(r'\b\w+\s*=\s*FakeSubPages\(', 'ui.sub_pages(', code)
    code = re.sub(r'\bFakeSubPages\(', 'ui.sub_pages(', code)
    return code


def remove_fake_init(code: str) -> str:
    """Remove ``sub_pages.init()`` / ``<var>.init()`` lines."""
    lines = _lines(code)
    result = []
    for line in lines:
        stripped = line.strip()
        if re.match(r'\w+\.init\(\)', stripped):
            continue
        result.append(line)
    return _join(result)


def remove_fake_imports(code: str) -> str:
    """Remove imports of ``FakeSubPages`` and ``FakeArguments``.

    Preserves other names on the same import line (e.g.
    ``from x import FakeSubPages, RealThing`` becomes ``from x import RealThing``).
    """
    fake_names = {'FakeSubPages', 'FakeArguments'}
    lines = _lines(code)
    result = []
    for line in lines:
        stripped = line.strip()
        if not any(name in stripped for name in fake_names) or 'import' not in stripped:
            result.append(line)
            continue
        # Parse "from ... import a, b, c" style
        m = re.match(r'(\s*from\s+\S+\s+import\s+)(.*)', line)
        if m:
            prefix, names_str = m.group(1), m.group(2)
            kept = [n.strip() for n in names_str.split(',') if n.strip() not in fake_names]
            if kept:
                result.append(prefix + ', '.join(kept))
            continue
        # Plain "import FakeSubPages" - just drop the line
    return _join(result)


def replace_fake_arguments(code: str) -> str:
    """Replace ``FakeArguments(...)`` with ``PageArguments(...)``."""
    return code.replace('FakeArguments(', 'PageArguments(')


def wrap_in_root(code: str) -> str:
    """Wrap top-level non-function, non-import statements in ``def root():`` and reorder.

    Produces the display pattern:

    .. code-block:: python

        from nicegui import ui

        def root():
            ...  # setup code

        def helper():
            ...

        ui.run(root)
    """
    lines = _lines(code)

    import_lines: list[str] = []
    func_blocks: list[list[str]] = []
    top_level_stmts: list[str] = []
    ui_run_line: str | None = None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith(('import ', 'from ')):
            import_lines.append(line)
            i += 1
        elif stripped.startswith(('def ', 'async def ')):
            block = [line]
            i += 1
            while i < len(lines):
                if lines[i] == '' or lines[i][0] == ' ':
                    block.append(lines[i])
                    i += 1
                else:
                    break
            # trim trailing blank lines from block
            while block and block[-1].strip() == '':
                block.pop()
            func_blocks.append(block)
        elif stripped.startswith('ui.run('):
            ui_run_line = line
            i += 1
        elif stripped == '':
            i += 1
        else:
            top_level_stmts.append(line)
            i += 1

    result: list[str] = list(import_lines)
    result.append('')

    if top_level_stmts:
        result.append('def root():')
        for stmt in top_level_stmts:
            result.append('    ' + stmt)
        result.append('')

    for block in func_blocks:
        result.extend(block)
        result.append('')

    # Ensure correct ui.run() call
    if top_level_stmts:
        result.append('ui.run(root)')
    elif ui_run_line:
        result.append(ui_run_line)
    else:
        result.append('ui.run()')

    return isort.code(_join(result), no_sections=True, lines_after_imports=1)
