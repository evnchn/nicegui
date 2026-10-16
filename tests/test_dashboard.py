from selenium.webdriver.common.action_chains import ActionChains

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
