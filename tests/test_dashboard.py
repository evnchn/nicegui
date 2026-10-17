import pytest
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


def test_server_follows_position_rejected_by_grid(screen: Screen):
    items: list[ui.dashboard_item] = []

    @ui.page('/')
    def page():
        with ui.dashboard(columns=4, cell_height=50).classes('w-[800px]'):
            items.append(ui.dashboard_item(x=0, y=0, w=1, h=1).classes('tile'))

        def move_down() -> None:
            items[0].y = 1
            ui.label('moved')
        ui.button('Move down', on_click=move_down)

    screen.open('/')
    screen.wait_for_js('!!document.querySelector(".grid-stack").gridstack', True)
    screen.click('Move down')
    screen.should_contain('moved')
    screen.wait_for(lambda: items[0].y == 0)
    assert screen.find_by_class('tile').get_attribute('gs-y') in (None, '0')


def test_readback_does_not_override_on_change(screen: Screen):
    items: list[ui.dashboard_item] = []
    corrections: list[int] = []

    def correct() -> None:
        if not corrections:
            corrections.append(2)
            items[0].x = 2

    @ui.page('/')
    def page():
        with ui.dashboard(columns=4, cell_height=50, on_change=correct).classes('w-[800px]'):
            items.append(ui.dashboard_item(x=0, y=0, w=1, h=1).classes('tile'))

        def move() -> None:
            items[0].x = 1
            items[0].y = 1
            ui.label('moved')
        ui.button('Move', on_click=move)

    screen.open('/')
    screen.wait_for_js('!!document.querySelector(".grid-stack").gridstack', True)
    screen.click('Move')
    screen.should_contain('moved')
    tile = screen.find_by_class('tile')
    screen.wait_for(lambda: items[0].geometry == {'x': 2, 'y': 0, 'w': 1, 'h': 1} and tile.get_attribute('gs-x') == '2')
    screen.wait(0.5)
    assert items[0].geometry == {'x': 2, 'y': 0, 'w': 1, 'h': 1}
    assert tile.get_attribute('gs-x') == '2'


def _count_geometry_events(dashboard: ui.dashboard, events: list[str]) -> None:
    for event in ('layout_change', 'layout_sync', 'item_resize'):
        dashboard.on(event, lambda _, event=event: events.append(event))
    for item in dashboard.default_slot.children:
        item.on('geometry_sync', lambda: events.append('geometry_sync'))


def _assert_settled(screen: Screen, dashboard: ui.dashboard, events: list[str]) -> None:
    screen.wait(2)
    count = len(events)
    assert count < 20, f'{count} geometry events'
    screen.wait(0.5)
    assert len(events) == count, f'{len(events) - count} more geometry events after settling'
    browser = screen.selenium.execute_script('''
        return [...document.querySelectorAll(".grid-stack-item")]
            .map(el => ({x: el.gridstackNode.x, y: el.gridstackNode.y, w: el.gridstackNode.w, h: el.gridstackNode.h}));
    ''')
    assert browser == dashboard.layout


def test_swapping_tiles_settles(screen: Screen):
    events: list[str] = []
    items: list[ui.dashboard_item] = []
    dashboards: list[ui.dashboard] = []

    @ui.page('/')
    def page():
        with ui.dashboard(columns=4, cell_height=50).classes('w-[800px]') as dashboard:
            for x, y in [(0, 0), (2, 0), (0, 1), (2, 1)]:
                items.append(ui.dashboard_item(x=x, y=y, w=2, h=1))
        _count_geometry_events(dashboard, events)
        dashboards.append(dashboard)

        def swap() -> None:
            items[0].x = 2
            items[1].x = 0
        ui.button('Swap', on_click=swap)

    screen.open('/')
    screen.wait_for_js('!!document.querySelector(".grid-stack").gridstack', True)
    screen.wait(0.5)
    events.clear()
    screen.click('Swap')
    _assert_settled(screen, dashboards[0], events)
    assert items[0].geometry == {'x': 2, 'y': 0, 'w': 2, 'h': 1}
    assert items[1].geometry == {'x': 0, 'y': 0, 'w': 2, 'h': 1}


def test_resize_callback_can_undo_resize(screen: Screen):
    events: list[str] = []
    dashboards: list[ui.dashboard] = []

    @ui.page('/')
    def page():
        with ui.dashboard(columns=4, cell_height=50).classes('w-[800px]') as dashboard:
            ui.dashboard_item(x=0, y=0, w=1, h=1, on_resize=lambda e: setattr(e.sender, 'w', 1)).classes('a')
        _count_geometry_events(dashboard, events)
        dashboards.append(dashboard)

    screen.open('/')
    screen.wait_for_js('!!document.querySelector(".grid-stack").gridstack', True)
    tile = screen.find_by_class('a')
    ActionChains(screen.selenium) \
        .move_to_element(tile) \
        .move_to_element(tile.find_element(By.CLASS_NAME, 'ui-resizable-se')) \
        .click_and_hold() \
        .move_by_offset(20, 0).move_by_offset(200, 0) \
        .release() \
        .perform()
    screen.wait_for(lambda: 'item_resize' in events)
    _assert_settled(screen, dashboards[0], events)
    assert dashboards[0].layout == [{'x': 0, 'y': 0, 'w': 1, 'h': 1}]


@pytest.mark.parametrize('write', ['grow', 'no-op'])
def test_drag_survives_server_write_to_other_tile(screen: Screen, write: str):
    events: list[DashboardChangeEventArguments] = []
    geometry_events: list[str] = []
    items: list[ui.dashboard_item] = []
    dashboards: list[ui.dashboard] = []

    @ui.page('/')
    def page():
        with ui.dashboard(columns=4, cell_height=50, on_change=events.append).classes('w-[800px]') as dashboard:
            items.append(ui.dashboard_item(x=0, y=0, w=1, h=1))
            items.append(ui.dashboard_item(x=1, y=0, w=1, h=1).classes('b'))
        _count_geometry_events(dashboard, geometry_events)
        dashboards.append(dashboard)

    screen.open('/')
    screen.wait_for_js('!!document.querySelector(".grid-stack").gridstack', True)
    tile = screen.find_by_class('b')
    ActionChains(screen.selenium).move_to_element(tile).click_and_hold().move_by_offset(20, 20).move_by_offset(400, 0) \
        .perform()
    screen.wait_for(lambda: 'ui-draggable-dragging' in (tile.get_attribute('class') or ''))
    a = items[0]
    if write == 'grow':
        a.h = 2
    else:
        a.w = a.w
    screen.wait(0.5)
    ActionChains(screen.selenium).release().perform()
    screen.wait_for(lambda: any(items[1] in e.items for e in events))
    screen.wait(0.5)
    assert items[1].x == 3
    assert tile.get_attribute('gs-x') == '3'
    _assert_settled(screen, dashboards[0], geometry_events)


def test_server_updates_apply_after_dragged_tile_is_deleted(screen: Screen):
    items: list[ui.dashboard_item] = []

    @ui.page('/')
    def page():
        with ui.dashboard(columns=4, cell_height=50).classes('w-[800px]'):
            items.append(ui.dashboard_item(x=0, y=0, w=1, h=1).classes('a'))
            items.append(ui.dashboard_item(x=1, y=0, w=1, h=1).classes('b'))

    screen.open('/')
    screen.wait_for_js('!!document.querySelector(".grid-stack").gridstack', True)
    tile = screen.find_by_class('b')
    ActionChains(screen.selenium).move_to_element(tile).click_and_hold().move_by_offset(20, 20).move_by_offset(400, 0) \
        .perform()
    screen.wait_for(lambda: 'ui-draggable-dragging' in (tile.get_attribute('class') or ''))
    items[0].h = 2
    screen.wait(0.5)
    items[1].delete()
    screen.wait(0.5)
    ActionChains(screen.selenium).release().perform()
    items[0].w = 2
    screen.wait_for(lambda: screen.find_by_class('a').get_attribute('gs-h') == '2')
    screen.wait_for(lambda: screen.find_by_class('a').get_attribute('gs-w') == '2')
