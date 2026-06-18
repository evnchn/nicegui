from nicegui import ui
from nicegui.testing import User


async def test_forwarded_prefix_injection_is_neutralized(user: User):
    @ui.page('/')
    def page():
        ui.label('Hello')

    payload = '"></script><script>PWNED</script>'
    response = await user.http_client.get('/', headers={'X-Forwarded-Prefix': payload})
    assert payload not in response.text, 'X-Forwarded-Prefix must not be reflected raw into the page'
    assert '<script>PWNED' not in response.text, 'the injected tag must not survive in executable form'
    assert '%3Cscript%3EPWNED' in response.text, 'dangerous characters should be percent-encoded'


async def test_forwarded_prefix_normal_value_is_unchanged(user: User):
    @ui.page('/')
    def page():
        ui.label('Hello')

    response = await user.http_client.get('/', headers={'X-Forwarded-Prefix': '/myapp'})
    assert '/myapp/_nicegui/' in response.text, 'a legitimate path prefix must pass through unchanged'
