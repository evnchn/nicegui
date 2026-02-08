from website.documentation.code_extraction import (
    get_display_code,
    make_replacer,
    remove_fake_imports,
    remove_fake_init,
    replace_fake_arguments,
    replace_fake_links,
    replace_fake_sub_pages,
    wrap_in_root,
)


def test_replace_fake_links():
    code = "    sub_pages.link('Go', '/other')\n    ui.link('Keep', '/stay')"
    result = replace_fake_links(code)
    assert "ui.link('Go', '/other')" in result
    assert "ui.link('Keep', '/stay')" in result


def test_replace_fake_links_preserves_known_objects():
    code = "    ui.link('A', '/a')\n    app.link('B', '/b')"
    result = replace_fake_links(code)
    assert "ui.link('A', '/a')" in result
    assert "app.link('B', '/b')" in result  # not replaced


def test_replace_fake_sub_pages():
    code = "sub_pages = FakeSubPages({'/': main})"
    result = replace_fake_sub_pages(code)
    assert result == "ui.sub_pages({'/': main})"


def test_replace_fake_sub_pages_with_data():
    code = "sub_pages = FakeSubPages({'/': main}, data={'x': 1})"
    result = replace_fake_sub_pages(code)
    assert result == "ui.sub_pages({'/': main}, data={'x': 1})"


def test_remove_fake_init():
    code = "    sub_pages.init()\n    pages.init()\n    ui.label('keep')"
    result = remove_fake_init(code)
    assert 'init()' not in result
    assert "ui.label('keep')" in result


def test_remove_fake_imports():
    code = 'from foo import FakeSubPages\nfrom bar import FakeArguments\nfrom nicegui import ui'
    result = remove_fake_imports(code)
    assert 'FakeSubPages' not in result
    assert 'FakeArguments' not in result
    assert 'from nicegui import ui' in result


def test_replace_fake_arguments():
    code = "lambda: main(FakeArguments(msg='hello'))"
    result = replace_fake_arguments(code)
    assert "PageArguments(msg='hello')" in result
    assert 'FakeArguments' not in result


def test_make_replacer():
    transformer = make_replacer('old_func(', 'new_func(')
    assert transformer('call old_func(x)') == 'call new_func(x)'


def test_wrap_in_root_basic():
    code = "from nicegui import ui\n\nui.label('hello')\n\ndef helper():\n    pass\n\nui.run()"
    result = wrap_in_root(code)
    assert 'def root():' in result
    assert "    ui.label('hello')" in result
    assert 'def helper():' in result
    assert 'ui.run(root)' in result


def test_wrap_in_root_preserves_with_blocks():
    code = ('from nicegui import ui\n\n'
            'with ui.row():\n'
            "    ui.label('a')\n"
            "    ui.label('b')\n\n"
            'def helper():\n'
            '    pass\n\n'
            'ui.run()')
    result = wrap_in_root(code)
    assert 'def root():' in result
    assert '    with ui.row():' in result
    assert "        ui.label('a')" in result


def test_wrap_in_root_no_top_level_statements():
    code = 'from nicegui import ui\n\ndef main():\n    pass\n\nui.run()'
    result = wrap_in_root(code)
    assert 'def root():' not in result
    assert 'ui.run()' in result


def test_full_pipeline():
    code = ('from nicegui import ui\n\n'
            'def main():\n'
            "    sub_pages.link('Go', '/other')\n\n"
            "sub_pages = FakeSubPages({'/': main})\n"
            'sub_pages.init()\n\n'
            'ui.run()')

    transformers = [replace_fake_links, replace_fake_sub_pages, remove_fake_init, wrap_in_root]
    for t in transformers:
        code = t(code)

    assert "ui.link('Go', '/other')" in code
    assert "ui.sub_pages({'/': main})" in code
    assert 'init()' not in code
    assert 'def root():' in code
    assert 'ui.run(root)' in code
    assert 'FakeSubPages' not in code


def test_get_display_code_without_transformers():
    def sample_demo():
        pass

    code = get_display_code(sample_demo)
    assert 'from nicegui import ui' in code


def test_get_display_code_with_transformers():
    def sample_demo():
        sub_pages = 'FakeSubPages'  # noqa: F841

    code = get_display_code(sample_demo, [make_replacer('FakeSubPages', 'ui.sub_pages')])
    assert 'ui.sub_pages' in code
