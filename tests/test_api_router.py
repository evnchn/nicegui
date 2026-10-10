import pytest
from fastapi import APIRouter as FastAPIRouter

from nicegui import APIRouter, app, ui
from nicegui.testing import Screen, User


def test_prefix(screen: Screen):
    router = APIRouter(prefix='/some-prefix')

    @router.page('/')
    def page():
        ui.label('Hello, world!')

    app.include_router(router)

    screen.open('/some-prefix')
    screen.should_contain('NiceGUI')
    screen.should_contain('Hello, world!')


def test_passing_page_parameters(screen: Screen):
    router = APIRouter()

    @router.page('/', title='My Custom Title')
    def page():
        ui.label('Hello, world!')

    app.include_router(router)

    screen.open('/')
    screen.should_contain('My Custom Title')


def test_relative_navigation_from_router_root_page(screen: Screen):
    router = APIRouter(prefix='/some-prefix')

    @router.page('/')
    def root():
        ui.button('Go', on_click=lambda: ui.navigate.to('4711'))

    @router.page('/{key:int}')
    def detail(key: int):
        ui.label(f'Detail {key}')

    app.include_router(router)

    screen.open('/some-prefix')
    screen.click('Go')
    screen.should_contain('Detail 4711')
    assert screen.current_path == '/some-prefix/4711'


@pytest.mark.parametrize('how', ['link', 'navigate'])
@pytest.mark.parametrize('layout, expected_path', [
    ('nested', '/outer/inner/page'),
    ('nested_fastapi_outer', '/outer/inner/page'),
    ('extra_prefix', '/extra/inner/page'),
])
async def test_page_function_target_of_included_router(user: User, how: str, layout: str, expected_path: str):
    inner = APIRouter(prefix='/inner')

    @inner.page('/page')
    def target():
        ui.label('Target page')

    if layout == 'nested':
        outer = APIRouter(prefix='/outer')
        outer.include_router(inner)
        app.include_router(outer)
    elif layout == 'nested_fastapi_outer':
        outer = FastAPIRouter(prefix='/outer')
        outer.include_router(inner)
        app.include_router(outer)
    else:
        app.include_router(inner, prefix='/extra')

    @ui.page('/')
    def index():
        if how == 'link':
            ui.link('Go', target)
        else:
            ui.button('Go', on_click=lambda: ui.navigate.to(target))

    await user.open('/')
    user.find('Go').click()
    await user.should_see('Target page')
    assert user.back_history[-1] == expected_path


@pytest.mark.parametrize('other_path', ['/admin/{_:path}', '/legacy/admin'])
async def test_page_function_target_with_two_paths(user: User, other_path: str):
    @ui.page('/admin')
    @ui.page(other_path)
    def admin():
        ui.label('Admin')

    @ui.page('/')
    def index():
        ui.link('Go', admin)

    await user.open('/')
    user.find('Go').click()
    await user.should_see('Admin')
    assert user.back_history[-1] == '/admin'
