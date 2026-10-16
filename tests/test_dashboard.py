from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from nicegui import ui
from nicegui.events import DashboardChangeEventArguments
from nicegui.testing import Screen


def test_drag_updates_layout_on_server(screen: Screen):
    events: list[DashboardChangeEventArguments] = []

    @ui.page('/')
    def page():
        with ui.dashboard(columns=4, cell_height=50, on_change=events.append).classes('w-[800px]') as dashboard:
            with ui.dashboard_item(x=0, y=0, w=1, h=1):
                ui.label('A')
            with ui.dashboard_item(x=1, y=0, w=1, h=1):
                ui.label('B')
        ui.button('Show layout', on_click=lambda: ui.label(str(dashboard.layout)))

    screen.open('/')
    screen.wait_for_js('!!document.querySelector(".grid-stack").gridstack', True)
    ActionChains(screen.selenium) \
        .move_to_element(screen.find('A')) \
        .click_and_hold() \
        .move_by_offset(20, 20).move_by_offset(400, 0) \
        .release() \
        .perform()
    screen.wait_for(lambda: bool(events))
    screen.click('Show layout')
    screen.should_contain("[{'x': 2, 'y': 0, 'w': 1, 'h': 1}, {'x': 1, 'y': 0, 'w': 1, 'h': 1}]")


def test_python_changes_move_tiles(screen: Screen):
    @ui.page('/')
    def page():
        with ui.dashboard(columns=4, cell_height=50).classes('w-[800px]'):
            with ui.dashboard_item(x=0, y=0, w=1, h=1).classes('tile') as item:
                ui.label('A')

        def grow() -> None:
            item.x = 1
            item.w = 3
        ui.button('Grow', on_click=grow)

    screen.open('/')
    tile = screen.find_by_class('tile')
    screen.wait_for(lambda: tile.size['width'] < 250)
    screen.click('Grow')
    screen.wait_for(lambda: tile.size['width'] > 550 and tile.location['x'] > 150)


def test_auto_placed_and_late_tiles_report_geometry(screen: Screen):
    @ui.page('/')
    def page():
        with ui.dashboard(columns=4, cell_height=50).classes('w-[800px]') as dashboard:
            with ui.dashboard_item(x=0, y=0, w=4, h=1):
                ui.label('A')
            with ui.dashboard_item(w=2, h=1):
                ui.label('B')

        def add() -> None:
            with dashboard:
                with ui.dashboard_item(w=2, h=1).classes('late'):
                    ui.label('C')
        ui.button('Add', on_click=add)
        ui.button('Show layout', on_click=lambda: ui.label(str(dashboard.layout)))

    screen.open('/')
    screen.wait_for_js('!!document.querySelector(".grid-stack").gridstack', True)
    screen.click('Add')
    late = screen.find_by_class('late')
    screen.wait_for(lambda: late.get_attribute('gs-y') == '1' and late.size['width'] > 350)
    screen.click('Show layout')
    screen.should_contain(
        "[{'x': 0, 'y': 0, 'w': 4, 'h': 1}, {'x': 0, 'y': 1, 'w': 2, 'h': 1}, {'x': 2, 'y': 1, 'w': 2, 'h': 1}]")


def test_min_max_sizes_are_clamped(screen: Screen):
    @ui.page('/')
    def page():
        with ui.dashboard(columns=4, cell_height=50).classes('w-[800px]') as dashboard:
            with ui.dashboard_item(x=0, y=0, w=1, h=1, max_w=2).classes('a') as a:
                ui.label('A')
            with ui.dashboard_item(x=0, y=1, w=1, h=1).classes('b') as b:
                ui.label('B')

        def widen() -> None:
            a.w = 4
            ui.label(f'a.w={a.w}')
        ui.button('Widen', on_click=widen)
        ui.button('Grow', on_click=lambda: setattr(b, 'min_w', 3))
        ui.button('Show layout', on_click=lambda: ui.label(str(dashboard.layout)))

    screen.open('/')
    screen.wait_for_js('!!document.querySelector(".grid-stack").gridstack', True)
    tile_a = screen.find_by_class('a')
    tile_b = screen.find_by_class('b')
    screen.click('Widen')
    screen.should_contain('a.w=2')
    screen.click('Grow')
    screen.wait_for(lambda: tile_b.size['width'] > 550)
    assert 350 < tile_a.size['width'] < 450
    screen.click('Show layout')
    screen.should_contain("[{'x': 0, 'y': 0, 'w': 2, 'h': 1}, {'x': 0, 'y': 1, 'w': 3, 'h': 1}]")


def test_resize_callback(screen: Screen):
    resizes: list[tuple[int, int]] = []

    @ui.page('/')
    def page():
        with ui.dashboard(columns=4, cell_height=50).classes('w-[800px]'):
            with ui.dashboard_item(x=0, y=0, w=1, h=1, max_w=2, on_resize=lambda e: resizes.append((e.w, e.h))) \
                    .classes('a'):
                ui.label('A')
            with ui.dashboard_item(x=0, y=1, w=1, h=1, on_resize=lambda e: resizes.append((e.w, e.h))).classes('b') as b:
                ui.label('B')
        ui.button('Python resize', on_click=lambda: setattr(b, 'w', 5))

    screen.open('/')
    screen.wait_for_js('!!document.querySelector(".grid-stack").gridstack', True)
    tile = screen.find_by_class('a')
    ActionChains(screen.selenium) \
        .move_to_element(tile) \
        .move_to_element(tile.find_element(By.CLASS_NAME, 'ui-resizable-se')) \
        .click_and_hold() \
        .move_by_offset(20, 0).move_by_offset(400, 0) \
        .release() \
        .perform()
    screen.wait_for(lambda: bool(resizes))
    assert resizes == [(2, 1)]
    assert 350 < tile.size['width'] < 450
    screen.click('Python resize')
    screen.wait_for(lambda: screen.find_by_class('b').size['width'] > 550)
    assert resizes == [(2, 1)]


def test_geometry_respects_columns_and_max_row(screen: Screen):
    items: list[ui.dashboard_item] = []

    @ui.page('/')
    def page():
        with ui.dashboard(columns=4, options={'maxRow': 3}):
            items.append(ui.dashboard_item(x=3, y=0, w=9, h=1, min_w=6))
            items.append(ui.dashboard_item(x=0, y=0, w=1, h=1))
        assert items[0].geometry == {'x': 0, 'y': 0, 'w': 4, 'h': 1}
        ui.label('ready')

    screen.open('/')
    screen.should_contain('ready')
    items[1].w = 3
    items[1].x = 9
    items[1].h = 5
    items[1].y = 7
    assert items[1].geometry == {'x': 1, 'y': 0, 'w': 3, 'h': 3}
