import copy
import weakref
from typing import Any

import pytest
from selenium.webdriver.common.keys import Keys

from nicegui import binding, ui
from nicegui.testing import Screen, User


def test_ui_select_with_tuple_as_key(screen: Screen):
    class Model:
        selection: tuple[int, int] | None = None
    data = Model()
    options = {
        (2, 1): 'option A',
        (1, 2): 'option B',
    }
    data.selection = next(iter(options))

    @ui.page('/')
    def page():
        ui.select(options).bind_value(data, 'selection')

    screen.open('/')
    screen.should_not_contain('option B')
    element = screen.click('option A')
    screen.click_at_position(element, x=20, y=100)
    screen.wait(0.3)
    screen.should_contain('option B')
    screen.should_not_contain('option A')
    assert data.selection == (1, 2)


def test_ui_select_with_list_of_tuples(screen: Screen):
    class Model:
        selection = None
    data = Model()
    options = [(1, 1), (2, 2), (3, 3)]
    data.selection = options[0]

    @ui.page('/')
    def page():
        ui.select(options).bind_value(data, 'selection')

    screen.open('/')
    screen.should_not_contain('2,2')
    element = screen.click('1,1')
    screen.click_at_position(element, x=20, y=100)
    screen.wait(0.3)
    screen.should_contain('2,2')
    screen.should_not_contain('1,1')
    assert data.selection == (2, 2)


def test_ui_select_with_list_of_lists(screen: Screen):
    class Model:
        selection = None
    data = Model()
    options = [[1, 1], [2, 2], [3, 3]]
    data.selection = options[0]

    @ui.page('/')
    def page():
        ui.select(options).bind_value(data, 'selection')

    screen.open('/')
    screen.should_not_contain('2,2')
    element = screen.click('1,1')
    screen.click_at_position(element, x=20, y=100)
    screen.wait(0.3)
    screen.should_contain('2,2')
    screen.should_not_contain('1,1')
    assert data.selection == [2, 2]


def test_binding_to_input(screen: Screen):
    class Model:
        text = 'one'
    data = Model()
    element = None

    @ui.page('/')
    def page():
        nonlocal element
        element = ui.input().bind_value(data, 'text')

    screen.open('/')
    screen.should_contain_input('one')
    screen.type(Keys.TAB)
    screen.type('two')
    screen.should_contain_input('two')
    screen.wait(0.1)
    assert data.text == 'two'
    data.text = 'three'
    screen.should_contain_input('three')
    element.set_value('four')
    screen.should_contain_input('four')
    assert data.text == 'four'
    element.value = 'five'
    screen.should_contain_input('five')
    assert data.text == 'five'


def test_binding_refresh_before_page_delivery(screen: Screen):
    state = {'count': 0}

    @ui.page('/')
    def main_page() -> None:
        ui.label().bind_text_from(state, 'count')
        state['count'] += 1

    screen.open('/')
    screen.should_contain('1')


def test_missing_target_attribute(screen: Screen):
    data: dict = {}

    @ui.page('/')
    def page():
        ui.label('Hello').bind_text_to(data)
        ui.label().bind_text_from(data, 'text', lambda text: f'{text=}')

    screen.open('/')
    screen.should_contain("text='Hello'")


def test_bindable_dataclass(screen: Screen):
    @binding.bindable_dataclass(bindable_fields=['bindable'])
    class TestClass:
        not_bindable: str = 'not_bindable_text'
        bindable: str = 'bindable_text'

    instance = TestClass()

    @ui.page('/')
    def page():
        ui.label().bind_text_from(instance, 'not_bindable')
        ui.label().bind_text_from(instance, 'bindable')

    screen.open('/')
    screen.should_contain('not_bindable_text')
    screen.should_contain('bindable_text')

    assert len(binding.bindings) == 2
    assert len(binding.active_links) == 1
    assert next(iter(binding.active_links.values()))[1] == ('not_bindable',)  # Names are now normalized to tuples


async def test_copy_instance_with_bindable_property(user: User):
    @binding.bindable_dataclass
    class Number:
        value: int = 1

    x = Number()
    y = copy.copy(x)

    @ui.page('/')
    def page():
        ui.label().bind_text_from(x, 'value', lambda v: f'x={v}')
        assert len(binding.bindings) == 1
        assert len(binding.active_links) == 0

        ui.label().bind_text_from(y, 'value', lambda v: f'y={v}')
        assert len(binding.bindings) == 2
        assert len(binding.active_links) == 0

    await user.open('/')
    await user.should_see('x=1')
    await user.should_see('y=1')

    y.value = 2
    await user.should_see('x=1')
    await user.should_see('y=2')


def test_automatic_cleanup(screen: Screen):
    class Model:
        value = binding.BindableProperty()

        def __init__(self, value: str) -> None:
            self.value = value

    def create_model_and_label(value: str) -> tuple[int, weakref.ref, ui.label]:
        model = Model(value)
        label = ui.label(value).bind_text(model, 'value')
        return id(model), weakref.ref(model), label

    model_id1 = ref1 = label1 = model_id2 = ref2 = label2 = None

    @ui.page('/')
    def page():
        nonlocal model_id1, ref1, label1, model_id2, ref2, label2
        model_id1, ref1, label1 = create_model_and_label('first label')
        model_id2, ref2, label2 = create_model_and_label('second label')

    def is_alive(ref: weakref.ref) -> bool:
        return ref() is not None

    def has_bindable_property(model_id: int) -> bool:
        return any(obj_id == model_id for obj_id, _ in binding.bindable_properties)

    screen.open('/')
    screen.should_contain('first label')
    screen.should_contain('second label')
    assert is_alive(ref1) and has_bindable_property(model_id1)
    assert is_alive(ref2) and has_bindable_property(model_id2)

    binding.remove([label1])
    assert not is_alive(ref1) and not has_bindable_property(model_id1)
    assert is_alive(ref2) and has_bindable_property(model_id2)


def test_remove_only_affects_given_objects():
    """``remove`` must drop only the given objects' bindings and leave unrelated ones working (issue #6150)."""
    binding.reset()

    class Model:
        value = binding.BindableProperty()

        def __init__(self) -> None:
            self.value = 0

    a_source, a_target = Model(), Model()
    b_source, b_target = Model(), Model()
    binding.bind_to(a_source, 'value', a_target, 'value')
    binding.bind_to(b_source, 'value', b_target, 'value')

    binding.remove(obj for obj in (a_source, a_target))  # also covers one-shot iterable input

    a_source.value = 1
    b_source.value = 2
    assert a_target.value == 0, 'removed binding must no longer propagate'
    assert b_target.value == 2, 'unrelated binding must stay intact'


def test_repeated_bind_remove_does_not_accumulate_state():
    """Refresh-style bind/remove cycles must not accumulate binding state, not even in reverse indexes (issue #6150).

    This is the regression guard for the quadratic-CPU bug: if ``remove`` left dangling entries behind,
    the global structures (and the work ``remove`` does) would grow without bound across refreshes.
    """
    binding.reset()

    class Model:
        value = binding.BindableProperty()

        def __init__(self) -> None:
            self.value = 0

    shared_source = {'value': 0}
    for _ in range(5):
        distinct_sources = [Model() for _ in range(20)]
        targets = [Model() for _ in range(20)]
        for source, target in zip(distinct_sources, targets, strict=True):
            binding.bind_to(source, 'value', target, 'value')  # distinct-source binding
            binding.bind_from(target, 'value', shared_source, 'value')  # shared-source active link
        binding.remove(distinct_sources + targets)

    assert not binding.bindings
    assert not binding.active_links
    assert not binding.bindable_properties
    assert not binding._bindings_by_obj, 'stale bindings index entries leaked'  # pylint: disable=protected-access
    assert not binding._active_links_by_obj, 'stale active-links index entries leaked'  # pylint: disable=protected-access


def test_remove_during_propagation_does_not_crash():
    """A transform calling ``remove`` mid-propagation must not raise (dict iterated during mutation, issue #6150)."""
    binding.reset()

    class Model:
        value = binding.BindableProperty()

        def __init__(self) -> None:
            self.value = 0

    source = Model()
    target_a, target_b = Model(), Model()

    def forward(value):
        binding.remove([target_b])  # mutate the shared binding dict while it is being iterated
        return value

    binding.bind_to(source, 'value', target_a, 'value', forward=forward)
    binding.bind_to(source, 'value', target_b, 'value')

    source.value = 5  # must not raise RuntimeError('dictionary changed size during iteration')
    assert target_a.value == 5
    assert target_b.value == 0, 'a reentrantly-removed target must not be written by a stale snapshot entry'
    assert not any(obj_id == id(target_b) for obj_id, _ in binding.bindable_properties), \
        'a reentrantly-removed target must not be resurrected into bindable_properties'


def test_remove_after_class_gains_bindable_property():
    """A bindable property added to a class at runtime must still be cleaned by ``remove`` (issue #6150).

    ``remove`` derives a class's bindable-property names from a per-class cache; adding a property
    must invalidate that cache, otherwise the new property would leak past ``remove``.
    """
    binding.reset()

    class Model:
        a = binding.BindableProperty()

        def __init__(self) -> None:
            self.a = 0

    warmup = Model()
    warmup.a = 1
    binding.remove([warmup])  # populates the per-class name cache for Model

    extra = binding.BindableProperty()
    extra.__set_name__(Model, 'b')
    Model.b = extra  # type: ignore[attr-defined]

    model = Model()
    model.a = 1
    model.b = 2  # type: ignore[attr-defined]
    assert any(obj_id == id(model) and name == ('b',) for obj_id, name in binding.bindable_properties)

    binding.remove([model])
    assert not any(obj_id == id(model) for obj_id, _ in binding.bindable_properties), \
        'the runtime-added bindable property must be cleaned by remove'


async def test_nested_propagation(user: User):
    class Demo:
        a = binding.BindableProperty()
        b = binding.BindableProperty(on_change=lambda obj, _: obj.change_a())

        def __init__(self) -> None:
            self.a = 0
            self.b = 0

        def change_a(self) -> None:
            self.a = 1
            self.a = 2

    demo = Demo()

    @ui.page('/')
    def page():
        ui.label().bind_text_from(demo, 'a', lambda a: f'a = {a}')
        ui.number().bind_value_to(demo, 'b')  # should set a to 1 and then 2

    await user.open('/')
    await user.should_see('a = 2')  # the final value of a should be 2


def test_binding_other_dict_is_strict(screen: Screen):
    data: dict[str, str] = {}

    @ui.page('/')
    def page():
        label = ui.label()
        with pytest.raises(KeyError):
            binding.bind(label, 'text', data, 'non_existent_key', other_strict=True)

    screen.open('/')


def test_binding_object_is_strict(screen: Screen):
    class Model:
        attribute = 'existing-attribute'
    model = Model()

    @ui.page('/')
    def page():
        label = ui.label()
        with pytest.raises(AttributeError):
            binding.bind(model, 'no_attribute', label, 'no_text')

    screen.open('/')


def test_binding_dict_is_not_strict(screen: Screen):
    data: dict[str, str] = {}

    @ui.page('/')
    def page():
        label = ui.label()
        binding.bind(data, 'non_existing_key', label, 'text')  # no exception

    screen.open('/')


def test_binding_refresh_interval_none(screen: Screen):
    class Model:
        value = 0

    @ui.page('/')
    def page():
        ui.label().bind_text_from(Model, 'value', lambda value: f'Value is {value}')

    screen.ui_run_kwargs['binding_refresh_interval'] = None
    screen.open('/')
    screen.should_contain('Value is 0')
    screen.assert_py_logger(
        'WARNING', 'Starting active binding loop even though it was disabled via binding_refresh_interval=None.',
    )


@pytest.mark.parametrize('data_type', ['dict-dict', 'object-dict', 'dict-object'])
@pytest.mark.parametrize('initialize', [True, False])
async def test_nested_binding(data_type: str, initialize: bool, user: User):
    class Data:
        def __init__(self, config: dict[str, int]) -> None:
            self.config = config

    class Config:
        def __init__(self, volume: int) -> None:
            self.volume = volume

    data: Any
    if data_type == 'dict-dict':
        data = {'config': {'volume': 0}} if initialize else {}
    if data_type == 'object-dict':
        data = Data({'volume': 0} if initialize else {})
    if data_type == 'dict-object':
        data = {'config': Config(0)} if initialize else {}

    @ui.page('/')
    def page():
        ui.number('Volume', min=0, max=100, value=50).bind_value_to(data, ('config', 'volume'), forward=int)
        ui.label().bind_text_from(data, ('config', 'volume'), backward=lambda v: f'Volume: {v}%')
        with pytest.raises((KeyError, AttributeError), match=r'Could not bind non-existing'):
            ui.input().bind_value(data, ('x', 'y'), strict=True)
        with pytest.raises(AssertionError, match='cannot be empty'):
            ui.input().bind_value(data, ())
        with pytest.raises(AssertionError, match='cannot be empty'):
            ui.input().bind_value(data, '')
        with pytest.raises(AssertionError, match='must contain only strings'):
            ui.input().bind_value(data, ('valid', 123))  # type: ignore[arg-type]

    await user.open('/')
    await user.should_see('Volume: 50%')
    if data_type == 'dict-dict':
        assert data == {'config': {'volume': 50}}
    if data_type == 'object-dict':
        assert data.config == {'volume': 50}
    if data_type == 'dict-object':
        if initialize:
            assert data['config'].volume == 50
        else:
            assert data == {'config': {'volume': 50}}
