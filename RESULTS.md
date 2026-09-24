# Issue #6353: `make_sortable` does nothing inside `ui.dialog`

**Verdict:** Confirmed on `upstream/main` @ `80a74f1`. The bug is not specific to dialogs. The `Sortable` controller binds SortableJS once, when the controller mounts. Any container whose DOM doesn't exist yet at that moment, or gets re-created later, is never bound. That covers dialogs, tab panels that aren't selected yet, and `move()`. **I did not commit a fix.** The obvious one-liner causes a regression, and the fix that works needs a design decision (options below).

## Root cause

- `nicegui/elements/mixins/sortable_element.py:48`: `with self.client.layout:`. The `Sortable` controller element is created in the page layout, not next to the container. So it mounts once, on page load.
- `nicegui/elements/sortable/sortable.js:4-5`: in `mounted()`, `document.getElementById(this.elementId)` is passed straight to `Sortable.create(...)`. There is no retry and no re-bind.
- QDialog (and QTabPanels for panels that aren't active) don't render their content until opened. So at mount time `getElementById` returns `null`, and SortableJS logs an error and never attaches. When the dialog opens later, a fresh card node appears and nothing binds to it. Closing and reopening re-creates the node again.

### Evidence (real Chromium 141 through the repo's `Screen` fixture)

The probe runs in the browser: `[card in DOM, card has a SortableJS expando]`. SortableJS stores its instance on the element under a `Sortable<id>` key.

| Case (main, unpatched) | probe | order after dragging Alpha below Beta |
|---|---|---|
| Control: card on the page | `[True, True]` | `['Beta', 'Alpha', 'Gamma']` ✅ |
| Dialog, before open | `[False, False]` | – |
| Dialog, after open | `[True, False]` | `['Alpha', 'Beta', 'Gamma']` ❌ |
| Dialog, after close + reopen | `[True, False]` | `['Alpha', 'Beta', 'Gamma']` ❌ |
| Tab panel not selected at first, after switching to it | `[True, False]` | `['Alpha', 'Beta', 'Gamma']` ❌ |
| Sortable card after `card.move(other_column)` (**pre-existing, same cause**) | `[True, True]` → `[True, False]` | `['Alpha', 'Beta', 'Gamma']` ❌ |

Browser console on the dialog and tab cases (in the tab case the `Screen` fixture fails at teardown with "JavaScript console error"):
```
vue.esm-browser.prod.js 4:22172 "Sortable: `el` must be an HTMLElement, not [object Null]"
```
I also ran the issue's exact MRE (handle icon + `handle='.handle'`) and got the same result: the card is not in the DOM before open, the same console error appears, and after open the drag does nothing. The same code outside a dialog reorders fine.

## Why the obvious one-liner is wrong

`with self.parent_slot or self.client.layout:` puts the controller next to the container, so they mount together. In the browser it fixes the dialog, reopen and tab cases (all probes `[True, True]`, drags work). **But** the controller then becomes a hidden child of the container's parent. If that parent is itself sortable, the DOM indices SortableJS reports no longer match the server's slot indices:

```
outer column (sortable): Xray, card(sortable), <card's controller>, Yank
drag Xray below Yank
  main:       ['Alpha','Beta','Gamma','Yank','Xray']   ✅
  one-liner:  ['Alpha','Beta','Gamma','Xray','Yank']   ❌ Xray lands above Yank
```
It also doesn't fix the `move()` case, because the probe stays `[True, False]` after the move.

## Options (design decision needed)

1. **Re-bind in `sortable.js` whenever the target element changes.** A `MutationObserver` on `document.body` (childList + subtree) calls `bind()`. `bind()` does `getElementById`. If the node is present and differs from `this.sortable.el`, it destroys the old instance and creates a new one. The observer is disconnected in `unmounted`.
   - I prototyped this, but did **not** commit it (patch below). In the browser it fixes dialog, reopen, tab panel **and** the pre-existing `move()` case, with no index regression (the "Xray below Yank" case gives `['Alpha','Beta','Gamma','Yank','Xray']`). The existing `tests/test_sortable.py` passes (5/5).
   - Cost: one document-wide observer per sortable. It runs an O(1) `getElementById` on every DOM mutation batch. That's cheap per call, but it's global work that scales with the number of sortables × DOM churn. Maintainers may not want that.
2. **Let the container own SortableJS.** Bind and unbind from the container's own mount/unmount lifecycle, for example through a hook in the generic element renderer or a mixin-level JS hook, instead of a separate controller in `client.layout`. This follows the DOM exactly and needs no global observer, but it's a bigger change that touches how `SortableElement` is rendered.
3. **Controller as a sibling (`parent_slot`) plus index correction.** Keep the one-liner and make `onEnd` / `slot.ids` splicing skip non-DOM children. Fragile: it still doesn't fix `move()`, and it spreads index bookkeeping into more places.
4. **Document the limitation.** Tell users to call `make_sortable()` after the dialog opens. That's a workaround, not a fix, and it still breaks after close + reopen.

My recommendation is (1) as the minimal patch, or (2) if maintainers prefer lifecycle-correct binding over a global observer.

### Prototype patch for option 1 (not committed)
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

## Reproduction script used

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
    _drag(screen, 'Alpha', 'Beta')
    print('DIALOG order after 1st open:', _order(screen)[:3])
    screen.click('Shut')
    screen.wait(0.5)
    screen.click('Open')
    screen.wait(0.5)
    print('DIALOG probe after reopen:', screen.selenium.execute_script(PROBE))
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

## Commands run (with real output)

Environment setup. Selenium Manager can't download a driver here (no network to googlechromelabs), and `/opt/node22/bin/chromedriver` is 147 while the preinstalled Chromium is 141. So I fetched a matching driver:
```
$ git remote add upstream https://github.com/zauberzeug/nicegui.git && git fetch upstream main
$ git checkout -b cloud/issue-6353 upstream/main
$ uv sync
$ npx -y @puppeteer/browsers install chromedriver@141.0.7390.37     # into the scratchpad dir
$ export PATH=<scratchpad>/chromedriver/linux-141.0.7390.37/chromedriver-linux64:$PATH \
         CHROME_BINARY_LOCATION=/opt/pw-browsers/chromium-1194/chrome-linux/chrome SE_OFFLINE=true
```

Repro on main:
```
$ uv run pytest -p no:cacheprovider tests/test_zz_repro_6353.py -s
CONTROL probe [in DOM, Sortable bound]: [True, True]
CONTROL order: ['Beta', 'Alpha', 'Gamma']
DIALOG probe before open: [False, False]
DIALOG probe after open: [True, False]
DIALOG order after 1st open: ['Alpha', 'Beta', 'Gamma']
DIALOG probe after reopen: [True, False]
DIALOG order after reopen: ['Alpha', 'Beta', 'Gamma']
-- console logs ---
.../vue.esm-browser.prod.js 4:22172 "Sortable: `el` must be an HTMLElement, not [object Null]"
TAB probe before switch: [False, False]
TAB probe after switch: [True, False]
TAB order: ['Alpha', 'Beta', 'Gamma']
NESTED outer text: ['Alpha', 'Beta', 'Gamma', 'Yank', 'Xray']
ERROR at teardown of test_tab_panel: JavaScript console error: ... "Sortable: `el` must be an HTMLElement, not [object Null]"
MOVED probe: [True, False]
MOVED order: ['Alpha', 'Beta', 'Gamma']
DOWN order right after drag + server sync: ['Alpha', 'Beta', 'Gamma', 'Yank', 'Xray']
```
(These lines are collected from the main-branch runs. I added the MOVED/DOWN tests in a second pass.)

One-liner (`parent_slot`) applied:
```
DIALOG probe after open: [True, True]      DIALOG order after 1st open: ['Beta', 'Alpha', 'Gamma']
DIALOG probe after reopen: [True, True]    DIALOG order after reopen: ['Beta', 'Gamma', 'Alpha']
TAB probe after switch: [True, True]       TAB order: ['Beta', 'Alpha', 'Gamma']
MOVED probe: [True, False]                 MOVED order: ['Alpha', 'Beta', 'Gamma']
DOWN order right after drag + server sync: ['Alpha', 'Beta', 'Gamma', 'Xray', 'Yank']   <- regression
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

## Uncertain / not done

- No fix is committed, and no regression test was added to `tests/test_sortable.py`, because the fix needs the design decision above. Once an option is chosen, the test should copy `test_basic_reorder`: a `.card` with A/B/C inside `ui.dialog`, click open, `_drag`, `_assert_order`, then close, reopen and drag again.
- I haven't measured the performance cost of the option-1 observer on large or busy pages.
- I haven't checked whether other lazily rendered containers (`ui.menu`, `ui.expansion`, `ui.stepper`) behave the same. The mechanism predicts they will whenever Quasar renders their content lazily.
- My repro script prints results instead of asserting. The only automatic failure was the teardown console-error check in the tab case.
- The clone is shallow, so I couldn't find in git history why `client.layout` was chosen. My inference: it keeps the controller out of the container's own slot, which is sortable.
