from nicegui import ui
from nicegui.testing import Screen


def test_add_action_renders_label_and_icon(screen: Screen):
    @ui.page('/')
    def page():
        n = ui.notification('Test', timeout=None)
        n.add_action(lambda: None, text='Click me', icon='check')

    screen.open('/')
    screen.should_contain('Test')
    screen.should_contain('Click me')
    assert screen.find_by_css('.q-notification__actions .q-icon').text == 'check'


def test_add_action_dismisses_notification(screen: Screen):
    @ui.page('/')
    def page():
        n = ui.notification('Test', timeout=None)
        n.add_action(lambda: None, text='OK')

    screen.open('/')
    screen.should_contain('Test')
    screen.click('OK')
    screen.wait(1.5)
    screen.should_not_contain('Test')


def test_add_action_no_dismiss_keeps_notification(screen: Screen):
    @ui.page('/')
    def page():
        n = ui.notification('Test', timeout=None)
        n.add_action(lambda: None, text='Stay', no_dismiss=True)

    screen.open('/')
    screen.should_contain('Test')
    screen.click('Stay')
    screen.wait(1.5)
    screen.should_contain('Test')


def test_add_action_quasar_color(screen: Screen):
    @ui.page('/')
    def page():
        n = ui.notification('Test', timeout=None)
        n.add_action(lambda: None, text='Primary', color='primary')

    screen.open('/')
    screen.should_contain('Primary')
    button = screen.find_by_css('.q-notification__actions .q-btn')
    assert button.value_of_css_property('color') == 'rgba(88, 152, 212, 1)'


def test_add_action_tailwind_color(screen: Screen):
    @ui.page('/')
    def page():
        n = ui.notification('Test', timeout=None)
        n.add_action(lambda: None, text='Blue', color='blue-500')

    screen.open('/')
    screen.should_contain('Blue')
    button = screen.find_by_css('.q-notification__actions .q-btn')
    assert 'text-blue-500' in button.get_attribute('class')


def test_add_action_css_color(screen: Screen):
    @ui.page('/')
    def page():
        n = ui.notification('Test', timeout=None)
        n.add_action(lambda: None, text='Custom', color='#ff0000')

    screen.open('/')
    screen.should_contain('Custom')
    button = screen.find_by_css('.q-notification__actions .q-btn')
    assert button.value_of_css_property('color') == 'rgba(255, 0, 0, 1)'


def test_add_action_color_encoding(screen: Screen):
    """White-box: whether a color lands in the "color" prop, "class" or "style" is not observable in the rendered DOM."""
    n = None

    @ui.page('/')
    def page():
        nonlocal n
        n = ui.notification('Test', timeout=None)
        n.add_action(lambda: None, text='Quasar', color='primary')
        n.add_action(lambda: None, text='Tailwind', color='blue-500')
        n.add_action(lambda: None, text='CSS', color='#ff0000')
        n.add_action(lambda: None, text='None', color=None)

    screen.open('/')
    screen.should_contain('Test')
    quasar, tailwind, css, none = n._props['options']['actions']
    assert quasar['color'] == 'primary' and 'class' not in quasar and 'style' not in quasar
    assert tailwind['class'] == 'text-blue-500' and 'color' not in tailwind and 'style' not in tailwind
    assert css['style'] == 'color: #ff0000;' and 'color' not in css and 'class' not in css
    assert all(key not in none for key in ('color', 'class', 'style'))


def test_add_action_kwargs_merge_with_color_class(screen: Screen):
    @ui.page('/')
    def page():
        n = ui.notification('Test', timeout=None)
        n.add_action(lambda: None, text='Merged', color='blue-500', **{'class': 'my-class'})

    screen.open('/')
    screen.should_contain('Merged')
    classes = screen.find_by_css('.q-notification__actions .q-btn').get_attribute('class')
    assert 'text-blue-500' in classes, 'color must not be dropped when a "class" kwarg is passed'
    assert 'my-class' in classes


def test_add_action_kwargs_merge_with_color_style(screen: Screen):
    @ui.page('/')
    def page():
        n = ui.notification('Test', timeout=None)
        n.add_action(lambda: None, text='Styled', color='#ff0000', style='padding-top: 30px;')

    screen.open('/')
    screen.should_contain('Styled')
    button = screen.find_by_css('.q-notification__actions .q-btn')
    assert button.value_of_css_property('color') == 'rgba(255, 0, 0, 1)', \
        'color must not be dropped when a "style" kwarg is passed'
    assert button.value_of_css_property('padding-top') == '30px'


def test_add_action_each_callback_fires(screen: Screen):
    clicked: list[str] = []

    @ui.page('/')
    def page():
        n = ui.notification('Decide', timeout=None)
        n.add_action(lambda: clicked.append('one'), text='One', no_dismiss=True)
        n.add_action(lambda: clicked.append('two'), text='Two', no_dismiss=True)
        n.add_action(lambda: clicked.append('three'), text='Three', no_dismiss=True)

    screen.open('/')
    screen.should_contain('Decide')
    screen.click('Two')
    screen.wait(0.5)
    screen.click('One')
    screen.wait(0.5)
    screen.click('Three')
    screen.wait(0.5)
    assert clicked == ['two', 'one', 'three']


def test_add_action_returns_self(screen: Screen):
    @ui.page('/')
    def page():
        n = ui.notification('Test', timeout=None)
        result = n.add_action(lambda: None, text='Test')
        assert result is n

    screen.open('/')
    screen.should_contain('Test')


def test_add_action_after_render_no_duplicate(screen: Screen):
    """Adding an action after the notification is on screen must not re-render and duplicate it (see PR #4819)."""
    clicked: list[str] = []

    @ui.page('/')
    def page():
        n = ui.notification('Decide', timeout=None)
        ui.button('Add', on_click=lambda: n.add_action(lambda: clicked.append('late'), text='Late'))

    screen.open('/')
    assert len(screen.find_all_by_class('q-notification')) == 1
    screen.click('Add')
    screen.wait(0.5)
    assert len(screen.find_all_by_class('q-notification')) == 1, 'late add_action must not duplicate the notification'
    screen.click('Late')
    screen.wait(0.5)
    assert clicked == ['late']
