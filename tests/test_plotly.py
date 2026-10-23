import numpy as np
import plotly.graph_objects as go

from nicegui import ui
from nicegui.elements.plotly.plotly import LIGHT_TRACE_TYPES
from nicegui.testing import Screen


def test_plotly(screen: Screen):
    @ui.page('/')
    def page():
        fig = go.Figure(go.Scatter(x=[1, 2, 3], y=[1, 2, 3], name='Trace 1'))
        fig.update_layout(title='Test Figure')
        plot = ui.plotly(fig)

        ui.button('Add trace', on_click=lambda: (
            # test NumPy array support for value arrays
            fig.add_trace(go.Scatter(x=np.array([0, 1, 2]), y=np.array([2, 1, 0]), name='Trace 2')),
            plot.update()
        ))

    screen.open('/')
    screen.should_contain('Test Figure')

    screen.click('Add trace')
    screen.should_contain('Trace 1')
    screen.should_contain('Trace 2')


def test_replace_plotly(screen: Screen):
    @ui.page('/')
    def page():
        with ui.row() as container:
            ui.plotly(go.Figure(go.Scatter(x=[1], y=[1], text=['A'], mode='text')))

        def replace():
            with container.clear():
                ui.plotly(go.Figure(go.Scatter(x=[1], y=[1], text=['B'], mode='text')))
        ui.button('Replace', on_click=replace)

    screen.open('/')
    assert screen.find_by_tag('text').text == 'A'

    screen.click('Replace')
    screen.wait(0.5)
    assert screen.find_by_tag('text').text == 'B'


def test_create_dynamically(screen: Screen):
    @ui.page('/')
    def page():
        ui.button('Create', on_click=lambda: ui.plotly(go.Figure(go.Scatter(x=[], y=[]))))

    screen.open('/')
    screen.click('Create')
    assert screen.find_by_tag('svg')


def test_run_plot_method(screen: Screen):
    @ui.page('/')
    def page():
        plot = ui.plotly({'data': [{'type': 'scatter', 'mode': 'text', 'x': [1], 'y': [1], 'text': ['Alpha']}]})
        button = ui.button('Extend')
        button.on_click(lambda: plot.run_plot_method('extendTraces', {'x': [[2]], 'y': [[2]], 'text': [['Beta']]}, [0]))

    screen.open('/')
    screen.should_contain('Alpha')
    screen.should_not_contain('Beta')

    screen.click('Extend')
    screen.should_contain('Beta')
    screen.should_contain('Alpha')


def test_run_plot_method_awaited(screen: Screen):
    @ui.page('/')
    def page():
        plot = ui.plotly(go.Figure(go.Scatter(x=[1, 2, 3], y=[1, 2, 3])))

        async def extend():
            # functions like extendTraces resolve to the graph element; awaiting must not time out
            result = await plot.run_plot_method('extendTraces', {'y': [[4]]}, [0])
            ui.label(f'result: {result!r}')
        ui.button('Extend', on_click=extend)

    screen.open('/')
    screen.click('Extend')
    screen.should_contain('result: None')


def test_light_bundle_for_simple_figures(screen: Screen):
    @ui.page('/')
    def page():
        ui.plotly(go.Figure(go.Scatter(x=[1, 2, 3], y=[1, 2, 3])))

    screen.open('/')
    assert screen.find_by_tag('svg')
    assert _loaded_bundles(screen) == {'index.js'}


def test_full_bundle_for_complex_figures(screen: Screen):
    @ui.page('/')
    def page():
        ui.plotly(go.Figure(go.Scatter3d(x=[1, 2], y=[1, 2], z=[1, 2])))

    screen.open('/')
    screen.wait(2.0)
    assert _loaded_bundles(screen) == {'full.js'}, 'the light bundle must not be fetched needlessly'
    assert _rendered_trace_types(screen) == ['scatter3d']


def test_upgrade_to_full_bundle(screen: Screen):
    @ui.page('/')
    def page():
        plot = ui.plotly(go.Figure(go.Scatter(x=[1, 2], y=[1, 2])))
        ui.button('Go 3D', on_click=lambda: plot.run_plot_method(
            'addTraces', {'type': 'scatter3d', 'x': [1, 2], 'y': [1, 2], 'z': [1, 2]}, timeout=10))

    screen.open('/')
    screen.wait(1.0)
    assert _loaded_bundles(screen) == {'index.js'}

    screen.click('Go 3D')
    screen.wait(3.0)
    assert _loaded_bundles(screen) == {'index.js', 'full.js'}
    assert _rendered_trace_types(screen) == ['scatter', 'scatter3d']


def test_light_trace_types_match_the_bundle(screen: Screen):
    @ui.page('/')
    def page():
        ui.plotly(go.Figure(go.Scatter(x=[1], y=[1])))

    screen.open('/')
    screen.wait(1.0)
    screen.selenium.set_script_timeout(30)
    registered = screen.selenium.execute_async_script(
        'const done = arguments[arguments.length - 1];'
        'import("nicegui-plotly").then(({ Plotly }) => done(Object.keys(Plotly.PlotSchema.get().traces)));'
    )
    assert set(registered) == LIGHT_TRACE_TYPES


def _loaded_bundles(screen: Screen) -> set:
    return set(screen.selenium.execute_script(
        'return performance.getEntriesByType("resource").map(entry => entry.name)'
        '.filter(name => name.includes("/esm/")).map(name => name.split("/").pop());'
    ))


def _rendered_trace_types(screen: Screen) -> list:
    return screen.selenium.execute_script(
        'return document.querySelector(".js-plotly-plot")._fullData.map(trace => trace.type);'
    )


def test_unknown_trace_type_does_not_loop(screen: Screen):
    @ui.page('/')
    def page():
        ui.plotly({'data': [{'type': 'nonsense', 'x': [1, 2], 'y': [1, 2]}]})

    screen.open('/')
    screen.wait(3.0)
    assert _loaded_bundles(screen) == {'full.js'}
    assert _rendered_trace_types(screen) == ['scatter'], 'plotly falls back to scatter, and that is the end of it'


def test_full_bundle_for_traces_hidden_in_frames(screen: Screen):
    @ui.page('/')
    def page():
        ui.plotly({
            'data': [{'type': 'scatter', 'x': [1, 2], 'y': [1, 2]}],
            'frames': [{'name': 'f', 'data': [{'type': 'scatter3d', 'x': [1], 'y': [1], 'z': [1]}]}],
        })

    screen.open('/')
    screen.wait(2.0)
    assert _loaded_bundles(screen) == {'full.js'}


def test_upgrade_for_traces_passed_as_a_figure(screen: Screen):
    @ui.page('/')
    def page():
        plot = ui.plotly(go.Figure(go.Scatter(x=[1, 2], y=[1, 2])))
        ui.button('React', on_click=lambda: plot.run_plot_method(
            'react', {'data': [{'type': 'scatter3d', 'x': [1], 'y': [1], 'z': [1]}]}, timeout=10))

    screen.open('/')
    screen.wait(1.0)
    assert _loaded_bundles(screen) == {'index.js'}

    screen.click('React')
    screen.wait(3.0)
    assert _loaded_bundles(screen) == {'index.js', 'full.js'}
    assert _rendered_trace_types(screen) == ['scatter3d']


def test_one_complex_figure_makes_the_page_skip_the_light_bundle(screen: Screen):
    @ui.page('/')
    def page():
        ui.plotly(go.Figure(go.Scatter3d(x=[1, 2], y=[1, 2], z=[1, 2])))  # NOTE: only plots mounting after this one
        ui.plotly(go.Figure(go.Scatter(x=[1, 2], y=[1, 2])))

    screen.open('/')
    screen.wait(2.5)
    assert _loaded_bundles(screen) == {'full.js'}
