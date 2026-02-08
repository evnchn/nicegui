from collections.abc import Callable

import pytest

from nicegui import Client, app, ui
from nicegui.testing import Screen, User


async def test_shared_page_basic(user: User) -> None:
    @ui.page('/', shared=True)
    def index():
        ui.label('Shared Page')

    await user.open('/')
    await user.should_see('Shared Page')


async def test_shared_page_reuses_client(create_user: Callable[[], User]) -> None:
    @ui.page('/', shared=True)
    def index():
        ui.label('Shared Page')

    user1 = create_user()
    user2 = create_user()

    await user1.open('/')
    client1 = user1.client
    await user2.open('/')
    client2 = user2.client

    assert client1 is not None
    assert client2 is not None
    assert client1.id == client2.id, 'Both users should share the same client'


async def test_non_shared_page_creates_separate_clients(create_user: Callable[[], User]) -> None:
    @ui.page('/')
    def index():
        ui.label('Private Page')

    user1 = create_user()
    user2 = create_user()

    await user1.open('/')
    client1 = user1.client
    await user2.open('/')
    client2 = user2.client

    assert client1 is not None
    assert client2 is not None
    assert client1.id != client2.id, 'Each user should have their own client'


async def test_shared_page_function_runs_only_once(create_user: Callable[[], User]) -> None:
    call_count = 0

    @ui.page('/', shared=True)
    def index():
        nonlocal call_count
        call_count += 1
        ui.label(f'Call #{call_count}')

    user1 = create_user()
    user2 = create_user()

    await user1.open('/')
    assert call_count == 1
    await user2.open('/')
    assert call_count == 1, 'Page function should only run once for shared pages'


async def test_shared_page_elements_visible_to_all(create_user: Callable[[], User]) -> None:
    @ui.page('/', shared=True)
    def index():
        ui.label('Initial Content')
        ui.button('Add Label', on_click=lambda: ui.label('Dynamic Content'))

    user1 = create_user()
    user2 = create_user()

    await user1.open('/')
    await user2.open('/')

    user1.find('Add Label').click()
    await user1.should_see('Dynamic Content')


async def test_shared_page_client_not_pruned(user: User) -> None:
    @ui.page('/', shared=True)
    def index():
        ui.label('Shared Page')

    await user.open('/')
    client = user.client
    assert client is not None

    # Shared clients should not be pruned even when stale
    client_count_before = len(Client.instances)
    Client.prune_instances(client_age_threshold=0)
    client_count_after = len(Client.instances)
    assert client.id in Client.instances, 'Shared client should not be pruned'
    assert client_count_after == client_count_before


async def test_shared_page_storage_tab_raises(user: User) -> None:
    @ui.page('/', shared=True)
    async def index():
        ui.label('Shared Page')
        await ui.context.client.connected()
        with pytest.raises(RuntimeError, match=r'app\.storage\.tab is not supported on shared pages'):
            _ = app.storage.tab

    await user.open('/')


async def test_shared_page_storage_client_raises(user: User) -> None:
    @ui.page('/', shared=True)
    def index():
        ui.label('Shared Page')
        with pytest.raises(RuntimeError, match=r'app\.storage\.client is not supported on shared pages'):
            _ = app.storage.client

    await user.open('/')


async def test_shared_page_await_run_javascript_raises(user: User) -> None:
    @ui.page('/', shared=True)
    async def index():
        ui.label('Shared Page')
        await ui.context.client.connected()
        with pytest.raises(RuntimeError, match='Cannot await run_javascript on a shared page'):
            await ui.context.client.run_javascript('return 1')

    await user.open('/')


async def test_shared_page_is_shared_property(user: User) -> None:
    @ui.page('/', shared=True)
    def index():
        ui.label('Shared Page')

    await user.open('/')
    assert user.client is not None
    assert user.client.is_shared is True


async def test_non_shared_page_is_shared_property(user: User) -> None:
    @ui.page('/')
    def index():
        ui.label('Private Page')

    await user.open('/')
    assert user.client is not None
    assert user.client.is_shared is False


async def test_shared_and_non_shared_pages_coexist(create_user: Callable[[], User]) -> None:
    @ui.page('/shared', shared=True)
    def shared():
        ui.label('Shared Page')

    @ui.page('/private')
    def private():
        ui.label('Private Page')

    user1 = create_user()
    user2 = create_user()

    await user1.open('/shared')
    shared_client1 = user1.client
    await user2.open('/shared')
    shared_client2 = user2.client
    assert shared_client1 is not None and shared_client2 is not None
    assert shared_client1.id == shared_client2.id

    await user1.open('/private')
    private_client1 = user1.client
    await user2.open('/private')
    private_client2 = user2.client
    assert private_client1 is not None and private_client2 is not None
    assert private_client1.id != private_client2.id


async def test_shared_page_disconnected_raises(user: User) -> None:
    @ui.page('/', shared=True)
    async def index():
        ui.label('Shared Page')
        await ui.context.client.connected()
        with pytest.raises(RuntimeError, match='not supported on shared pages'):
            await ui.context.client.disconnected()

    await user.open('/')


async def test_shared_page_sub_pages_raises(user: User) -> None:
    @ui.page('/', shared=True)
    def index():
        with pytest.raises(RuntimeError, match=r'ui\.sub_pages is not supported on shared pages'):
            ui.sub_pages({'/': lambda: ui.label('Home')})

    await user.open('/')


def test_shared_page_screen_basic(screen: Screen):
    @ui.page('/', shared=True)
    def index():
        ui.label('Shared Screen Page')

    screen.open('/')
    screen.should_contain('Shared Screen Page')


def test_shared_page_screen_reuses_across_tabs(screen: Screen):
    client_ids: list[str] = []

    @ui.page('/', shared=True)
    def index():
        client_ids.append(ui.context.client.id)
        ui.label('Shared Page')

    screen.open('/')
    screen.switch_to(1)
    screen.open('/')
    screen.should_contain('Shared Page')

    # First visit creates client, second reuses it (page function not called again)
    assert len(client_ids) == 1, 'Page function should only run once for shared pages'
