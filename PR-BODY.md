### Motivation

Fixes #5443 (native window close hangs the process on Windows). When a native-mode
app is closed, uvicorn's graceful shutdown enters a connection-drain loop that can hang
**forever** on a ghost Windows connection: a `ConnectionResetError: [WinError 10054]`
raised inside the proactor's `_call_connection_lost` aborts the transport's cleanup
before it detaches from the asyncio `Server`, so `server.wait_closed()` never resolves.
The user closed the window and the process never exits.

This implements the direction @falkoschindler proposed in #5443: in native mode, after
the window is closed, run the user's `app.on_shutdown` callbacks to completion and then
`os._exit(0)` — there is no live browser left to gracefully drain, so a hard exit is the
right call. Supersedes the `timeout_graceful_shutdown=10` default proposed in #5706 /
#6105 (which truncates legitimately-slow shutdown work and affects non-native users).

### Implementation

**Empirical finding that shapes the design (uvicorn 0.40.0 and 0.49.0, verified from
source on the test machine):** `Server.shutdown()` runs the connection drain
*before* lifespan shutdown:

```
shutdown():
  close servers / sockets
  request connection shutdown; sleep(0.1)
  await wait_for(_wait_tasks_to_complete(), timeout=timeout_graceful_shutdown)   # <-- DRAIN (the hang)
      └─ ... ; for server: await server.wait_closed()                            # <-- never resolves on the ghost
  await self.lifespan.shutdown()                                                 # <-- on_shutdown callbacks (AFTER the drain)
```

So @falkoschindler's *literal* sketch — "wait for lifespan shutdown to complete, then
`os._exit(0)`" — cannot work: lifespan shutdown is gated behind the very drain that
hangs. (Verified on real Windows hardware — see candidate V1 below: on a hung trial the
`on_shutdown` callbacks never run, so the "wait for lifespan" loop spins forever.)

This PR therefore implements the *intent* in a drain-independent way: instead of waiting
for uvicorn's lifespan shutdown, we drive NiceGUI's own shutdown directly. On native
window close we schedule `app.stop()` (which runs every `app.on_shutdown` callback) on
the running event loop via `asyncio.run_coroutine_threadsafe`, wait for it to complete,
flush stdout/stderr, then `os._exit(0)`. Because the process exits there, uvicorn never
reaches its own lifespan shutdown, so the handlers run exactly once.

Two call sites cover both modes:

- `nicegui/native/native_mode.py` — `_hard_exit_after_shutdown`, called from the
  window-close watcher `check_shutdown` (the `reload=False` path used by the #4970 repro
  and every packaged native app).
- `nicegui/server.py` — `monitor_shutdown_event` (the `reload=True` path).

Scoped to native mode only; non-native shutdown is untouched. For non-native scenarios
that want a bounded drain, `timeout_graceful_shutdown` remains available as a uvicorn
kwarg through `**kwargs`.

### Progress

- [x] The PR title is a short phrase starting with a verb.
- [x] The implementation is complete.
- [x] This PR does not address a security issue.
- [ ] Pytests have been added/updated or are not necessary. <!-- native-mode window-close hard-exit is verified by a Windows hardware fleet test (see below); not unit-testable in CI -->
- [ ] Documentation has been added/updated or is not necessary.
- [x] No breaking changes to the public API.

---

### Windows verification (real hardware)

DeskPC: Windows 11 IoT Enterprise LTSC 10.0.26100, Python 3.12.10, pywebview 6.2.1,
WebView2 149.0.4022.62, uvicorn 0.49.0. Repro per #4970: 2 × `ui.video`,
`ui.run(native=True, reload=False)`, a `ui.timer` destroys the native window after 8 s,
an `app.on_shutdown` writes+flushes a marker; the runner measures destroy→process-exit
and kills any tree still alive at +30 s. 20 trials `reload=False` + 5 trials `reload=True`
per candidate, run in the interactive session via scheduled task (WebView2 won't start
over SSH). Both candidates installed into fresh venvs from their own branch.

| candidate                                                    | mode           | trials | hangs        | clean exits | on_shutdown ran                     | destroy→exit  |
| ------------------------------------------------------------ | -------------- | ------ | ------------ | ----------- | ----------------------------------- | ------------- |
| **V1** (Falko literal: wait for lifespan, then `os._exit`)   | `reload=False` | 20     | **11 (55%)** | 9           | **9/20** (only the non-hung trials) | 3.3–3.6 s     |
| V1                                                           | `reload=True`  | 5      | 0            | 5           | 5/5                                 | 3.0–3.4 s     |
| **V2** (this PR: run `app.stop()` directly, then `os._exit`) | `reload=False` | 20     | **0**        | **20**      | **20/20**                           | **3.0–3.3 s** |
| V2                                                           | `reload=True`  | 5      | 0            | 5           | 5/5                                 | 3.0–3.2 s     |

**V1 deadlocks ~55% of the time, exactly as the uvicorn-ordering analysis predicts.** On
a hung trial the `on_shutdown` callbacks never ran (`on_shutdown 9/20`, all 9 on the
non-hung trials) — because waiting on lifespan-shutdown-completion can never succeed when
lifespan shutdown is gated behind the drain that is itself stuck. So Falko's literal
sketch is not viable; it reproduces the very hang it set out to fix.

**V2 (this PR) is 0 hangs in 20 `reload=False` trials, with `on_shutdown` running every
single time, and a clean 5/5 `reload=True` regression pass.** Driving `app.stop()` ourselves
makes the exit even snappier than the timeout-bounded alternative (a flat 3.0–3.3 s, with
none of the ~4.5 s "released after the 1 s drain timeout" cluster) because there is no
timer to wait out — the handlers run and the process exits immediately.

Raw CSVs and the rerunnable kit are archived on the test machine and mirrored to
`~/nicegui-6105-verify-staging/results/` (`results-v1*.csv`, `results-v2*.csv`).
