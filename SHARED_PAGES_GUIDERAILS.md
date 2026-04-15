# Shared Pages Guiderails

This document describes the guiderails added for the `shared=True` parameter on `@ui.page()` and the reasoning behind each one.

## Background

When `@ui.page('/', shared=True)` is used, **all visitors share the same `Client` instance**. The page function runs only once; subsequent visitors receive the already-built HTML and join the same Socket.IO room. This means every message sent to `client.id` reaches every connected browser simultaneously.

This is fundamentally different from the default per-user pages where each visitor gets their own `Client`, their own element tree, and their own communication channel.

## Guiderail Categories

Guiderails fall into two categories:

- **`RuntimeError`** — the feature is fundamentally incompatible with shared pages and would produce incorrect or broken behavior. Using it is always a mistake.
- **`warn_once`** — the feature *works* but broadcasts to all connected browsers, which may or may not be intentional. The warning fires once per message to avoid log spam.

---

## RuntimeError Guiderails

### `app.storage.tab`

**File:** `nicegui/storage.py` (`.tab` property)

Tab storage is keyed by individual browser tab identity. On a shared page, there is only one `Client` — the concept of "which tab" is meaningless because the server cannot distinguish between tabs belonging to different users.

### `app.storage.client`

**File:** `nicegui/storage.py` (`.client` property)

Client storage is per-`Client` volatile state. Since all browsers share the same `Client` on a shared page, writing to `app.storage.client` would create a shared mutable dict that all users silently read/write to — a race condition and identity confusion bug.

### `app.storage.user`

**File:** `nicegui/storage.py` (`.user` property)

User storage is keyed by session cookie ID from the HTTP request. On a shared page, only the most recent request is stored on the `Client`, so `app.storage.user` would return the storage of whichever user visited most recently — a data leak.

### `app.storage.browser`

**File:** `nicegui/storage.py` (`.browser` property)

Browser storage reads from the session cookie of the current request. Same problem as `app.storage.user`: on a shared page, the request belongs to whichever browser loaded last.

### `await client.run_javascript(...)`

**File:** `nicegui/client.py` (`run_javascript` method, `send_and_wait` inner function)

When `run_javascript` is awaited, the server waits for a single response. On a shared page, the JavaScript executes on **all** connected browsers, and multiple responses would race to fulfill the same future — producing undefined behavior. Fire-and-forget (`run_javascript` without `await`) is still allowed (with a warning).

### `await client.disconnected()`

**File:** `nicegui/client.py` (`disconnected` method)

`disconnected()` blocks until the client is deleted. Shared clients are never deleted (they persist as long as the `page` object holds a weakref to them), so this would block forever.

### `ui.sub_pages`

**File:** `nicegui/elements/sub_pages.py` (`SubPages.__init__`)

`ui.sub_pages` provides client-side routing within a page. Navigation events (URL changes) are dispatched to the `Client`, which on a shared page would re-route **all** connected browsers simultaneously. This is not just a broadcast problem — it would break the element tree for everyone.

---

## Warning Guiderails

### `ui.notify`

**File:** `nicegui/functions/notify.py`

Notifications are sent via the outbox to `client.id`. On a shared page, this means every connected browser sees the notification. This *may* be intentional (e.g., a system-wide alert), so it's a warning rather than an error.

### `ui.navigate.to`

**File:** `nicegui/functions/navigate.py`

Navigation commands are sent to all browsers in the `client.id` room. On a shared page, calling `ui.navigate.to('/other')` would redirect every visitor. Warned because there are edge cases where this is desired.

### `client.open`

**File:** `nicegui/client.py` (`open` method)

Same broadcast issue as `ui.navigate.to` — opens a URL on all connected browsers.

### `client.download`

**File:** `nicegui/client.py` (`download` method)

Triggers a file download on all connected browsers simultaneously. Warned because a developer might intentionally push a file to all viewers.

### `client.ip`

**File:** `nicegui/client.py` (`ip` property)

Returns the IP address from `self.request.client.host`. On a shared page, `self.request` is overwritten on each visit, so this always returns the **most recent** visitor's IP — not any specific user's IP.

### `run_javascript` (fire-and-forget)

**File:** `nicegui/client.py` (`run_javascript` method)

When called without `await`, the JavaScript runs on all browsers. This is warned (not blocked) because broadcasting JS to all viewers can be legitimate (e.g., triggering a visual effect).

---

## Lifecycle Guiderails

### Shared clients exempt from pruning

**File:** `nicegui/client.py` (`prune_instances` classmethod)

`Client.prune_instances()` periodically removes stale clients that never established a socket connection. Shared clients are excluded because they should persist for the lifetime of the application — they represent a long-lived page, not a per-user session.

### Shared clients exempt from disconnect deletion

**File:** `nicegui/client.py` (`handle_disconnect` method)

When a browser disconnects from a normal page, the client is deleted after a timeout. For shared pages, the client must survive individual browser disconnects because other browsers may still be connected (or new ones may connect later).

---

## Design Decisions

1. **Warnings over errors for broadcast behavior**: Features like `ui.notify` and `ui.navigate.to` technically *work* on shared pages — they just affect everyone. Since a developer might intentionally want this (e.g., a dashboard that navigates all viewers to an alert page), we warn rather than block.

2. **Errors for identity-dependent features**: Storage tiers (`tab`, `client`, `user`, `browser`) fundamentally depend on knowing *which* user is making the request. On a shared page this information is lost, so any use is a bug. `app.storage.general` is recommended as the alternative.

3. **Weakref-based client reuse**: The shared client is held via `weakref.ref` on the `page` instance. If the client is somehow garbage-collected (all references dropped), the next visitor transparently creates a fresh one. This avoids memory leaks while keeping the shared page alive as long as it's in use.

4. **No auto-index re-implementation**: NiceGUI 2.x had an "auto-index" page that was implicitly shared. This was removed in 3.0 (PR #5005) because it was too complex and confusing. The new `shared=True` parameter is explicit, opt-in, and much simpler — it's just 15 lines in `page.py` plus guiderails.
