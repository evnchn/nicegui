# Issue 6353: `make_sortable` does nothing inside `ui.dialog`

Confirmed on `upstream/main` @ `80a74f1`, and it is wider than dialogs. No fix committed yet: picking one needs a design call.

## What happens

```python
with ui.dialog() as dialog, ui.card() as card:
    ...
card.make_sortable()  # SortableJS binds now, but the card is not in the DOM yet
dialog.open()         # the card appears; nothing ever binds to it
```

- `nicegui/elements/mixins/sortable_element.py:48`: the `Sortable` controller is created in `client.layout`, so it mounts once, at page load.
- `nicegui/elements/sortable/sortable.js:4-5`: `mounted()` calls `Sortable.create(document.getElementById(...))` once. No retry, no re-bind.
- The browser logs `Sortable: el must be an HTMLElement, not [object Null]`.

## Measured (Chromium 141, the repo's `Screen` fixture, clean main)

| Case | Card in DOM, bound? | Drag works? |
|---|---|---|
| Card on the page (control) | yes, yes | ✅ |
| Inside a dialog, after open | yes, **no** | ❌ |
| Dialog closed and reopened (new DOM node) | yes, **no** | ❌ |
| Tab panel not selected at first, after switching | yes, **no** | ❌ |
| Sortable card after `card.move(other_column)` | yes, **no** | ❌ |

The issue's own MRE, with the handle, gives the same result.

## Options

| | Dialog, reopen, tab | `move()` | Nested sortables | Status |
|---|---|---|---|---|
| A. Controller next to the card (`with self.parent_slot or self.client.layout:`) | ✅ | ❌ | ❌ drag lands one slot off | measured |
| B. A + skip non-DOM children in index math | ✅ | ❌ | probably ✅ | not built |
| C. Re-bind in `sortable.js` via a `MutationObserver` | ✅ | ✅ | ✅ | prototyped, existing 5/5 sortable tests pass |
| D. Container owns SortableJS through its own mount/unmount | expected ✅ | expected ✅ | expected ✅ | not built, bigger change |
| E. Document it: call `make_sortable()` after opening | partly | ❌ | – | breaks again on reopen |

- **Rule:** a fix has to cover every row of the measured table without breaking nested sortables. That rules out A, B and E.
- **The question left:** is one document-wide `MutationObserver` per sortable acceptable? It does an O(1) `getElementById` per DOM mutation batch, but the work scales with sortables × DOM churn, and I have not measured it on a busy page.
  - Yes: **C**, already prototyped (patch below).
  - No: **D**.

My lean is C as the smallest patch. D is the cleaner lifecycle if the observer cost is unwelcome.

## Open risks for C

- `mounted()` is async and the observer attaches after `await import(...)`. If the container is deleted first, the observer leaks. A real patch needs an "already unmounted" guard after the await.
- With `group: {pull: 'clone'}` and a dragged item that wraps a sortable, two nodes can briefly share an id, and the observer could rebind to the clone mid-drag. Untested.
- After a dialog closes, the old instance stays on the detached node until the next rebind. Harmless, not cleaned up.
- Not checked: `ui.menu`, `ui.expansion`, `ui.stepper`. The mechanism predicts the same bug wherever Quasar renders content lazily.

## Evidence

<details><summary>Why A breaks nested sortables (measured)</summary>

The controller becomes a hidden child of the card's parent, so SortableJS DOM indices stop matching the server's slot indices when that parent is sortable too:

```
outer column (sortable): Xray, card (sortable), <card's controller>, Yank
drag Xray below Yank
  main:  ['Alpha','Beta','Gamma','Yank','Xray']   ✅
  A:     ['Alpha','Beta','Gamma','Xray','Yank']   ❌ Xray lands above Yank
```
A also leaves `move()` unbound (probe stays `[True, False]`).
</details>

<details><summary>Prototype patch for C (not committed)</summary>

```diff
diff --git a/nicegui/elements/sortable/sortable.js b/nicegui/elements/sortable/sortable.js
index 89063a3..f715842 100644
--- a/nicegui/elements/sortable/sortable.js
+++ b/nicegui/elements/sortable/sortable.js
@@ -1,8 +1,19 @@
 export default {
   async mounted() {
     const { Sortable } = await import("nicegui-sortable");
-    const element = document.getElementById(this.elementId);
-    this.sortable = Sortable.create(element, {
+    this.bind = () => {
+      const element = document.getElementById(this.elementId);
+      if (!element || element === this.sortable?.el) return;
+      this.sortable?.destroy();
+      this.sortable = this.create(Sortable, element);
+    };
+    this.observer = new MutationObserver(this.bind);
+    this.observer.observe(document.body, { childList: true, subtree: true });
+    this.bind();
+  },
+  methods: {
+    create(Sortable, element) {
+    return Sortable.create(element, {
       ...this.options,
       onEnd: (evt) => {
         const fromId = parseInt(evt.from.id.substring(1));
@@ -32,8 +43,10 @@ export default {
         );
       },
     });
+    },
   },
   unmounted() {
+    this.observer?.disconnect();
     this.sortable?.destroy();
   },
   watch: {
```

</details>

<details><summary>Repro script (run as tests/test_zz_repro_6353.py, not committed; prints instead of asserting)</summary>

I ran this temporarily as `tests/test_zz_repro_6353.py` so it picked up the repo's `Screen` fixture and conftest. It is **not** committed. It prints results instead of asserting; the numbers above come from its output.

```python
from selenium.webdriver.common.action_chains import ActionChains

from nicegui import ui
from nicegui.testing import Screen

PROBE = '''
const el = document.querySelector('.card');
return [!!el, !!el && Object.keys(el).some(k => k.startsWith('Sortable'))];
'''


def _drag(screen, a, b):
    ActionChains(screen.selenium).move_to_element(screen.find(a)).click_and_hold() \
        .move_to_element_with_offset(screen.find(b), 0, 5).release().perform()
    screen.wait(0.5)


def _order(screen):
    return screen.find_by_class('card').text.splitlines()


def test_control(screen: Screen):
    @ui.page('/')
    def page():
        with ui.card().classes('card') as card:
            for n in ['Alpha', 'Beta', 'Gamma']:
                ui.label(n)
        card.make_sortable()
    screen.open('/')
    print('\nCONTROL probe [in DOM, Sortable bound]:', screen.selenium.execute_script(PROBE))
    _drag(screen, 'Alpha', 'Beta')
    print('CONTROL order:', _order(screen))


def test_dialog(screen: Screen):
    @ui.page('/')
    def page():
        with ui.dialog() as dialog, ui.card().classes('card') as card:
            for n in ['Alpha', 'Beta', 'Gamma']:
                ui.label(n)
            ui.button('Shut', on_click=dialog.close)
        card.make_sortable()
        ui.button('Open', on_click=dialog.open)
    screen.open('/')
    print('\nDIALOG probe before open:', screen.selenium.execute_script(PROBE))
    screen.click('Open')
    screen.wait(0.5)
    print('DIALOG probe after open:', screen.selenium.execute_script(PROBE))
    screen.selenium.execute_script('document.querySelector(".card").__mark = 1')
    _drag(screen, 'Alpha', 'Beta')
    print('DIALOG order after 1st open:', _order(screen)[:3])
    screen.click('Shut')
    screen.wait(0.5)
    screen.click('Open')
    screen.wait(0.5)
    print('DIALOG probe after reopen:', screen.selenium.execute_script(PROBE))
    print('DIALOG same card node after reopen:', screen.selenium.execute_script('return document.querySelector(".card").__mark === 1'))
    _drag(screen, 'Alpha', 'Gamma')
    print('DIALOG order after reopen:', _order(screen)[:3])
    print(screen.render_js_logs())


def test_tab_panel(screen: Screen):
    @ui.page('/')
    def page():
        with ui.tabs() as tabs:
            ui.tab('One')
            ui.tab('Two')
        with ui.tab_panels(tabs, value='One'):
            with ui.tab_panel('One'):
                ui.label('first')
            with ui.tab_panel('Two'):
                with ui.card().classes('card') as card:
                    for n in ['Alpha', 'Beta', 'Gamma']:
                        ui.label(n)
        card.make_sortable()
    screen.open('/')
    print('\nTAB probe before switch:', screen.selenium.execute_script(PROBE))
    screen.click('Two')
    screen.wait(0.5)
    print('TAB probe after switch:', screen.selenium.execute_script(PROBE))
    _drag(screen, 'Alpha', 'Beta')
    print('TAB order:', _order(screen))


def test_nested_sortable(screen: Screen):
    @ui.page('/')
    def page():
        with ui.column().classes('outer') as outer:
            ui.label('Xray')
            with ui.card().classes('card') as card:
                for n in ['Alpha', 'Beta', 'Gamma']:
                    ui.label(n)
            ui.label('Yank')
        outer.make_sortable(on_end=lambda e: ui.notify(f'outer {e.old_index}->{e.new_index}'))
        card.make_sortable()
        ui.button('Count', on_click=lambda: ui.notify(f'outer slot children: {len(outer.default_slot.children)}'))
    screen.open('/')
    _drag(screen, 'Xray', 'Yank')
    screen.click('Count')
    screen.wait(0.5)
    print('\nNESTED outer text:', screen.find_by_class('outer').text.splitlines())
    print(screen.render_js_logs())


def test_ctrl_between_items(screen: Screen):
    @ui.page('/')
    def page():
        with ui.column().classes('outer') as outer:
            ui.label('Xray')
            with ui.card().classes('card') as card:
                for n in ['Alpha', 'Beta', 'Gamma']:
                    ui.label(n)
            card.make_sortable()
            ui.label('Yank')
        outer.make_sortable(on_end=lambda e: ui.notify(f'outer {e.item} {e.old_index}->{e.new_index}'))
        ui.button('Count', on_click=lambda: ui.notify(
            'server: ' + ', '.join(type(c).__name__ for c in outer.default_slot.children)))
    screen.open('/')
    print('\nBETWEEN outer DOM children:', screen.selenium.execute_script(
        'return [...document.querySelector(".outer").children].map(e => e.tagName + "#" + e.id)'))
    ActionChains(screen.selenium).move_to_element(screen.find('Yank')).click_and_hold() \
        .move_to_element_with_offset(screen.find('Xray'), 0, -5).release().perform()
    screen.wait(0.5)
    screen.click('Count')
    screen.wait(0.5)
    print('BETWEEN outer DOM after drag:', screen.find_by_class('outer').text.splitlines())
    print('BETWEEN notifications:', [e.text for e in screen.selenium.find_elements('css selector', '.q-notification')])


def test_move_sortable_card(screen: Screen):
    @ui.page('/')
    def page():
        with ui.row():
            with ui.column() as left:
                with ui.card().classes('card') as card:
                    for n in ['Alpha', 'Beta', 'Gamma']:
                        ui.label(n)
                card.make_sortable()
            right = ui.column()
        ui.button('Move', on_click=lambda: card.move(right))
    screen.open('/')
    print('\nMOVED probe before move:', screen.selenium.execute_script(PROBE))
    screen.click('Move')
    screen.wait(0.5)
    print('\nMOVED probe:', screen.selenium.execute_script(PROBE))
    _drag(screen, 'Alpha', 'Beta')
    print('MOVED order:', _order(screen))


def test_ctrl_between_items_down(screen: Screen):
    @ui.page('/')
    def page():
        with ui.column().classes('outer') as outer:
            ui.label('Xray')
            with ui.card().classes('card') as card:
                for n in ['Alpha', 'Beta', 'Gamma']:
                    ui.label(n)
            card.make_sortable()
            ui.label('Yank')
        outer.make_sortable()
    screen.open('/')
    ActionChains(screen.selenium).move_to_element(screen.find('Xray')).click_and_hold() \
        .move_to_element_with_offset(screen.find('Yank'), 0, 5).release().perform()
    screen.wait(1.0)
    print('\nDOWN order right after drag + server sync:', screen.find_by_class('outer').text.splitlines())
```

</details>

<details><summary>Environment, commands and raw output</summary>

Environment setup. Selenium Manager can't download a driver here (no network to googlechromelabs), and `/opt/node22/bin/chromedriver` is 147 while the preinstalled Chromium is 141. So I fetched a matching driver:
```
$ git remote add upstream https://github.com/zauberzeug/nicegui.git && git fetch upstream main
$ git checkout -b cloud/issue-6353 upstream/main
$ uv sync
$ npx -y @puppeteer/browsers install chromedriver@141.0.7390.37     # into the scratchpad dir
$ export PATH=<scratchpad>/chromedriver/linux-141.0.7390.37/chromedriver-linux64:$PATH \
         CHROME_BINARY_LOCATION=/opt/pw-browsers/chromium-1194/chrome-linux/chrome SE_OFFLINE=true
```

All browser runs went through this wrapper, saved as `../run.sh`. It filters out Selenium Manager warnings, blank lines and server banners:
```bash
export PATH=/tmp/claude-0/-home-user-nicegui/9da6a4db-254a-5f3f-88d1-312f40cf830d/scratchpad/chromedriver/linux-141.0.7390.37/chromedriver-linux64:$PATH CHROME_BINARY_LOCATION=/opt/pw-browsers/chromium-1194/chrome-linux/chrome SE_OFFLINE=true
cd /home/user/nicegui && timeout 500 uv run pytest -p no:cacheprovider "$@" 2>&1 | grep -v "^WARNING\|^$\|ready to go\|Storing screenshot"
```

Repro on clean main, final version of the script. This is raw output from `timeout 500 uv run pytest -p no:cacheprovider tests/test_zz_repro_6353.py -s 2>&1 | grep -v "^WARNING"` (blank lines removed):
```
Building nicegui @ file:///home/user/nicegui
      Built nicegui @ file:///home/user/nicegui
Uninstalled 1 package in 0.41ms
Installed 1 package in 0.71ms
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0
driver: Chrome
sensitiveurl: .*
rootdir: /home/user/nicegui
configfile: pyproject.toml
plugins: html-4.2.0, metadata-3.1.1, order-1.3.0, anyio-4.14.2, asyncio-1.3.0, selenium-4.1.0, variables-3.1.0, base-url-2.1.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 7 items
tests/test_zz_repro_6353.py NiceGUI ready to go on http://localhost:39105, and http://192.0.2.2:39105
CONTROL probe [in DOM, Sortable bound]: [True, True]
CONTROL order: ['Beta', 'Alpha', 'Gamma']
.Storing screenshot to /home/user/nicegui/screenshots/3537/test_control.png
NiceGUI ready to go on http://localhost:39105, and http://192.0.2.2:39105
DIALOG probe before open: [False, False]
DIALOG probe after open: [True, False]
DIALOG order after 1st open: ['Alpha', 'Beta', 'Gamma']
DIALOG probe after reopen: [True, False]
DIALOG same card node after reopen: False
DIALOG order after reopen: ['Alpha', 'Beta', 'Gamma']
-- console logs ---
http://localhost:39105/_nicegui/0.0.0.post87.dev0+e498335/static/vue.esm-browser.prod.js 4:22172 "Sortable: `el` must be an HTMLElement, not [object Null]"
---------------------
.Storing screenshot to /home/user/nicegui/screenshots/3537/test_dialog.png
NiceGUI ready to go on http://localhost:39105, and http://192.0.2.2:39105
TAB probe before switch: [False, False]
TAB probe after switch: [True, False]
TAB order: ['Alpha', 'Beta', 'Gamma']
.Storing screenshot to /home/user/nicegui/screenshots/3537/test_tab_panel.png
ENiceGUI ready to go on http://localhost:39105, and http://192.0.2.2:39105
NESTED outer text: ['Alpha', 'Beta', 'Gamma', 'Yank', 'Xray']
-- console logs ---
---------------------
.Storing screenshot to /home/user/nicegui/screenshots/3537/test_nested_sortable.png
NiceGUI ready to go on http://localhost:39105, and http://192.0.2.2:39105
BETWEEN outer DOM children: ['DIV#c5', 'DIV#c6', 'DIV#c11']
BETWEEN outer DOM after drag: ['Yank', 'Xray', 'Alpha', 'Beta', 'Gamma']
BETWEEN notifications: ['outer Label [text=Yank] 2->0', 'server: Label, Label, Card']
.Storing screenshot to /home/user/nicegui/screenshots/3537/test_ctrl_between_items.png
NiceGUI ready to go on http://localhost:39105, and http://192.0.2.2:39105
MOVED probe before move: [True, True]
MOVED probe: [True, False]
MOVED order: ['Alpha', 'Beta', 'Gamma']
.Storing screenshot to /home/user/nicegui/screenshots/3537/test_move_sortable_card.png
NiceGUI ready to go on http://localhost:39105, and http://192.0.2.2:39105
DOWN order right after drag + server sync: ['Alpha', 'Beta', 'Gamma', 'Yank', 'Xray']
.Storing screenshot to /home/user/nicegui/screenshots/3537/test_ctrl_between_items_down.png
==================================== ERRORS ====================================
_____________________ ERROR at teardown of test_tab_panel ______________________
JavaScript console error:
{'level': 'SEVERE', 'message': 'http://localhost:39105/_nicegui/0.0.0.post87.dev0+e498335/static/vue.esm-browser.prod.js 4:22172 "Sortable: `el` must be an HTMLElement, not [object Null]"', 'source': 'console-api', 'timestamp': 1790222140340}
=========================== short test summary info ============================
ERROR tests/test_zz_repro_6353.py::test_tab_panel - Failed: JavaScript consol...
========================= 7 passed, 1 error in 17.56s ==========================
```

The one-liner and prototype blocks below are **excerpts**: I grepped earlier runs of the same script for `probe|order|DOWN|MOVED|passed` via `bash ../run.sh ... -s | grep -E ...`. Those runs predate the marker line and the pre-move probe.

One-liner (`parent_slot`) applied:
```
DIALOG probe after open: [True, True]      DIALOG order after 1st open: ['Beta', 'Alpha', 'Gamma']
DIALOG probe after reopen: [True, True]    DIALOG order after reopen: ['Beta', 'Gamma', 'Alpha']
TAB probe after switch: [True, True]       TAB order: ['Beta', 'Alpha', 'Gamma']
MOVED probe: [True, False]                 MOVED order: ['Alpha', 'Beta', 'Gamma']
DOWN order right after drag + server sync: ['Alpha', 'Beta', 'Gamma', 'Xray', 'Yank']   <- regression
# first one-liner run (control/dialog/tab/nested only): ============ 4 passed in 11.27s ============ (no teardown error)
```

Option-1 prototype applied:
```
DIALOG probe after open: [True, True]      DIALOG order after 1st open: ['Beta', 'Alpha', 'Gamma']
DIALOG probe after reopen: [True, True]    DIALOG order after reopen: ['Beta', 'Gamma', 'Alpha']
TAB probe after switch: [True, True]       TAB order: ['Beta', 'Alpha', 'Gamma']
MOVED probe: [True, True]                  MOVED order: ['Beta', 'Alpha', 'Gamma']
DOWN order right after drag + server sync: ['Alpha', 'Beta', 'Gamma', 'Yank', 'Xray']
============================== 7 passed in 17.67s ==============================
$ uv run pytest tests/test_sortable.py     # prototype
============================== 5 passed in 8.14s ===============================
$ uv run pytest tests/test_sortable.py     # main (prototype reverted)
============================== 5 passed in 8.27s ===============================
```


- The clone was shallow, so git history does not say why `client.layout` was chosen. Likely to keep the controller out of the container's own sortable slot.
- No regression test added yet. Once an option is picked, copy `test_basic_reorder` in `tests/test_sortable.py`: a card inside `ui.dialog`, open, drag, assert order, close, reopen, drag again.
</details>
